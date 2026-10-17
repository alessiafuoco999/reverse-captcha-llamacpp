"""Reverse-CAPTCHA Evaluierung mit llama.cpp + Qwen3.5-27B."""
import sys
sys.path.insert(0, '/home/student/bachelorarbeit/data/reverse-captcha-eval/packs/reverse_captcha')
# (entfernt: alter Pfad)

import requests
import json
import subprocess
import sqlite3
import time
import yaml
from pathlib import Path

# Grader importieren
sys.path.insert(0, '/home/student/bachelorarbeit/data/reverse-captcha-eval/packs/reverse_captcha')
from grader import grade

# Konfiguration
URL = "http://localhost:8080/v1/chat/completions"
MODEL = "/mnt/data/gguf_models/Qwen3.5-27B-UD-Q4_K_XL.gguf"
YAML_PATH = '/home/student/bachelorarbeit/data/reverse-captcha-llamacpp/yamls/phase2b_answeronly.yaml'
DB_PATH = '/home/student/bachelorarbeit/data/reverse-captcha-llamacpp/qwen3.5-27b/results_v2/phase2b_answeronly.sqlite'

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


def run_python(code: str) -> str:
    try:
        result = subprocess.run(['python3', '-c', code],
                                capture_output=True, text=True, timeout=30)
        out = result.stdout or ''
        if result.stderr:
            out += f"\nSTDERR: {result.stderr}"
        return out or "(keine Ausgabe)"
    except Exception as e:
        return f"Fehler: {e}"


def agent_loop(system: str, user: str, max_turns: int = 10):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
    tool_calls_made = 0

    for turn in range(max_turns):
        try:
            response = requests.post(URL, json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "max_tokens": 8192,
                "temperature": 0.7,
                "top_p": 0.8
            }, timeout=180)
            result = response.json()
        except Exception as e:
            return f"API-Fehler: {e}", tool_calls_made

        # DEBUG: Fehlerhafte Antworten loggen
        if 'choices' not in result:
            return f"API-ERROR-RESPONSE: {json.dumps(result)[:500]}", tool_calls_made

        msg = result['choices'][0]['message']
        finish = result['choices'][0]['finish_reason']

        if not msg.get('tool_calls'):
            return msg.get('content', '') or '', tool_calls_made

        messages.append(msg)

        for tc in msg['tool_calls']:
            tool_calls_made += 1
            try:
                args = json.loads(tc['function']['arguments'])
                code = args.get('code', '')
                result_exec = run_python(code)
            except Exception as e:
                result_exec = f"Fehler: {e}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc['id'],
                "content": result_exec
            })

    return "(max turns erreicht)", tool_calls_made


# Datenbank initialisieren
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        case_id TEXT, scheme TEXT, expected TEXT, rep INTEGER,
        response TEXT, score REAL, label TEXT, latency_ms REAL, tool_calls INTEGER
    )
""")
conn.commit()

# Fälle laden
with open(YAML_PATH, 'r', encoding='utf-8') as f:
    cases = yaml.safe_load(f)

print(f"Evaluierung von {len(cases)} Fällen × 3 Wiederholungen")
print(f"Modell: {MODEL}")
print(f"Backend: llama.cpp (Port 8080)")
print()

N_REPS = 3
total = len(cases) * N_REPS
counter = 0

for case in cases:
    for rep in range(1, N_REPS + 1):
        counter += 1
        start = time.perf_counter()
        try:
            response_text, tool_calls = agent_loop(
                case.get('instruction', ''), case['carrier_text']
            )
            latency_ms = (time.perf_counter() - start) * 1000

            metadata = case.get('metadata', {})
            metadata['scheme'] = case['scheme']
            if response_text.startswith('API-ERROR-RESPONSE'):
                grade_result = {'score': 0.0, 'label': 'API_ERROR'}
            else:
                grade_result = grade(
                    model_output=response_text,
                    expected=case['expected'],
                    metadata=metadata,
                )

            cur.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (case['id'], case['scheme'], case['expected'], rep,
                         response_text, grade_result['score'], grade_result['label'],
                         latency_ms, tool_calls))
            conn.commit()
            print(f"  [{counter}/{total}] {case['id']} rep={rep} "
                  f"score={grade_result['score']:.2f} label={grade_result['label']} "
                  f"tools={tool_calls} lat={latency_ms:.0f}ms")
        except Exception as e:
            print(f"  [{counter}/{total}] {case['id']} rep={rep} FEHLER: {e}")
            cur.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (case['id'], case['scheme'], case['expected'], rep,
                         f"ERROR: {e}", 0.0, 'ERROR', 0.0, 0))
            conn.commit()

conn.close()
print()
print(f"Ergebnisse gespeichert: {DB_PATH}")
