#!/usr/bin/env python3
"""
API-Fehler-Diagnose für Qwen3.5-27B.

Testet die Fälle, die in P1/P2a/P2b zu API-Fehlern führten, mit
verschiedenen max_tokens-Werten und mehreren Wiederholungen.

Loggt finish_reason (kritisch: unterscheidet Token-Limit von Modell-Stop).
Speichert alle Ergebnisse in SQLite.

Aufruf:
  python3 scripts/test_api_errors.py --limit 10
  python3 scripts/test_api_errors.py            # alle Fälle
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import yaml
import requests

URL = "http://localhost:8080/v1/chat/completions"
MODEL = "/mnt/data/gguf_models/Qwen3.5-27B-UD-Q4_K_XL.gguf"
DB_PATH = "/tmp/qwen35_error_analysis.sqlite"
CASES_JSON = "/tmp/qwen35_error_cases.json"

MAX_TOKENS_VALUES = [1024, 4096, 8192]
N_REPS = 3
TIMEOUT_S = 300

TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Execute Python code and return stdout/stderr.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"]
        }
    }
}]

PHASE_YAML = {
    "phase1_original":     "yamls/phase1_original.yaml",
    "phase2a_enhanced":    "yamls/phase2a_enhanced.yaml",
    "phase2b_answeronly":  "yamls/phase2b_answeronly.yaml",
}

def load_cases_for_phase(phase):
    with open(PHASE_YAML[phase], encoding="utf-8") as f:
        return {c['id']: c for c in yaml.safe_load(f)}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            case_id TEXT,
            phase TEXT,
            scheme TEXT,
            max_tokens INTEGER,
            rep INTEGER,
            finish_reason TEXT,
            args_len INTEGER,
            json_valid INTEGER,
            error TEXT,
            latency_ms REAL,
            response_excerpt TEXT
        )
    """)
    conn.commit()
    return conn

def call_api(case, max_tokens):
    start = time.perf_counter()
    try:
        r = requests.post(URL, json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": case.get('instruction', '')},
                {"role": "user", "content": case['carrier_text']}
            ],
            "tools": TOOLS,
            "tool_choice": "auto",
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.8
        }, timeout=TIMEOUT_S)
        latency = (time.perf_counter() - start) * 1000
        return r, latency, None
    except requests.exceptions.Timeout:
        latency = (time.perf_counter() - start) * 1000
        return None, latency, "TIMEOUT"
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return None, latency, f"EXC: {e}"

def parse_response(resp, error):
    """Return (finish_reason, args_len, json_valid, error_text, excerpt)."""
    if error:
        return None, 0, 0, error, ""
    if resp is None:
        return None, 0, 0, "NO_RESPONSE", ""
    try:
        data = resp.json()
    except Exception as e:
        return None, 0, 0, f"JSON_DECODE: {e}", resp.text[:200]

    if 'choices' not in data:
        err = json.dumps(data)[:300]
        return None, 0, 0, f"API_ERROR: {err}", ""

    choice = data['choices'][0]
    finish = choice.get('finish_reason')
    msg = choice.get('message', {})

    if msg.get('tool_calls'):
        args = msg['tool_calls'][0]['function']['arguments']
        args_len = len(args)
        try:
            json.loads(args)
            return finish, args_len, 1, None, args[:200]
        except Exception as e:
            return finish, args_len, 0, f"JSON_INVALID: {str(e)[:100]}", args[:200]
    else:
        content = msg.get('content', '') or ''
        return finish, 0, 0, "NO_TOOL_CALL", content[:200]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Nur die ersten N Fälle testen")
    ap.add_argument("--phase", default=None, help="Nur eine Phase")
    args = ap.parse_args()

    # Fehlerfälle laden
    with open(CASES_JSON) as f:
        error_data = json.load(f)

    # (case_id, phase) Paare bauen
    test_targets = []
    for phase, case_ids in error_data['per_phase'].items():
        if args.phase and phase != args.phase:
            continue
        for cid in case_ids:
            test_targets.append((cid, phase))

    if args.limit:
        test_targets = test_targets[:args.limit]

    print(f"Testumfang: {len(test_targets)} (case_id, phase) Paare")
    print(f"max_tokens-Werte: {MAX_TOKENS_VALUES}")
    print(f"Wiederholungen pro Kombination: {N_REPS}")
    print(f"Gesamt Tests: {len(test_targets) * len(MAX_TOKENS_VALUES) * N_REPS}")
    print()

    # Cases pro Phase laden
    cases_per_phase = {p: load_cases_for_phase(p) for p in error_data['per_phase']}

    conn = init_db()
    cur = conn.cursor()

    counter = 0
    total = len(test_targets) * len(MAX_TOKENS_VALUES) * N_REPS

    for case_id, phase in test_targets:
        case = cases_per_phase[phase].get(case_id)
        if not case:
            print(f"  [SKIP] {case_id} nicht in {phase}")
            continue
        scheme = case.get('scheme', '?')

        for max_tok in MAX_TOKENS_VALUES:
            for rep in range(1, N_REPS + 1):
                counter += 1
                resp, latency, call_err = call_api(case, max_tok)
                finish, args_len, valid, err, excerpt = parse_response(resp, call_err)

                cur.execute("""
                    INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (case_id, phase, scheme, max_tok, rep,
                      finish, args_len, valid, err, latency, excerpt))
                conn.commit()

                status = "OK" if valid else f"FAIL({err})"
                print(f"  [{counter}/{total}] {case_id} {phase} max={max_tok} rep={rep} "
                      f"finish={finish} args_len={args_len} → {status}")

    conn.close()
    print(f"\nErgebnisse: {DB_PATH}")

if __name__ == "__main__":
    main()
