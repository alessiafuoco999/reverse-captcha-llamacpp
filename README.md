# Reverse-CAPTCHA: llama.cpp Stack

Reproduzierbare Evaluierung der Anfälligkeit von Open-Weight-LLMs für
unsichtbare Unicode-Injection (Reverse-CAPTCHA, Graves 2026).

## Modelle

| Modell | Typ | Architektur | Parameter aktiv | Port |
|--------|-----|-------------|-----------------|------|
| Qwen3.5-27B | General-Instruct | Dense | 27B | 8080 |
| Qwen3-30B-A3B | General-Instruct | MoE | 3B | 8082 |
| Qwen3-Coder-30B | Code-spezialisiert | MoE | 3B | 8081 |

## Ordnerstruktur
├── yamls/ # Aktuelle Test-Cases (v2-Parameter)
│ ├── phase1_original.yaml # Paper-Original (identisch mit GitHub-Repo)
│ ├── phase2a_enhanced.yaml # Eigene Erweiterung (Code-Beispiel, ohne int()-Warnung)
│ ├── phase2b_answeronly.yaml # Eigene Erweiterung (Answer-Only)
│ └── test_subset_27.yaml # Pilot-Test
├── yamls_v1/ # Archiv: YAMLs des v1-Runs (mit int()-Warnung)
├── results_v1/ # Archiv: Runs v1 (max_tokens=1024, max_turns=3)
├── results_v2/ # Aktuelle Runs v2 (max_tokens=8192, max_turns=10)
├── scripts/ # Analyse- und Diagnose-Skripte
│ ├── analyze_all_phases.py # Haupt-Analyse (Compliance-Tabellen)
│ ├── regrade_db.py # Re-graded DB mit Original-Grader
│ ├── test_api_errors.py # API-Fehler-Diagnose (Token-Limit, Timeout)
│ ├── compare_jinja.py # Jinja-Test-Vergleich
│ └── classify_refusals.py # Refusal-Klassifikation (diagnostisch)
├── qwen3.5-27b/ # Modell-spezifisch
│ ├── eval_phase*.py # Eval-Skripte (aktuelle v2-Parameter)
│ ├── results_v1/ # v1-Ergebnisse
│ ├── results_v2/ # v2-Ergebnisse (nach Lauf)
│ ├── logs/ # Log-Dateien
│ └── backup_skripte/ # Backup der Original-Skripte
├── qwen3-30b-a3b/ # (analog)
├── qwen3-coder-30b/ # (analog)
├── docs/ # Thesis-Dokumentation (Markdown)
├── RUNS.md # Detaillierte Run-Dokumentation
└── llama.cpp/ # Engine (Build b11456)

## Phasen

| Phase | YAML | Zweck |
|-------|------|-------|
| **1: Original** | `phase1_original.yaml` | Paper-Referenz (byte-identisch mit Graves 2026) |
| **2a: Enhanced Hint** | `phase2a_enhanced.yaml` | Eigene Erweiterung: Code-Beispiel im Hint |
| **2b: Answer-Only** | `phase2b_answeronly.yaml` | Eigene Erweiterung: Reasoning-Check-Unterdrückung |

## Runs

### Run v1 (15.-16. Oktober 2026)

- **max_tokens = 1024**, **max_turns = 3**
- **Problem:** API-Fehlerrate bei Qwen3.5: 12-16 % (durch zu niedriges Token-Limit)
- **Archiv:** `*/results_v1/`, `yamls_v1/`

### Run v2 (ab 17. Oktober 2026)

- **max_tokens = 8192**, **max_turns = 10**
- **Änderungen:**
  - `int()`-Warnung aus Tag-Hints entfernt (verursachte Elephant-Effekt)
  - Zero-Width-Hints um Code-Beispiel ergänzt (Konsistenz)
  - API-Fehler werden als `API_ERROR` klassifiziert (Bug-Fix)
- **Ergebnisse:** `*/results_v2/`
- **Details:** siehe `RUNS.md`

## Server-Start (Beispiele)

# Qwen3.5-27B auf Port 8080:

```bash
./llama.cpp/build/bin/llama-server \
    -m /mnt/data/gguf_models/Qwen3.5-27B-UD-Q4_K_XL.gguf \
    -c 65536 --host 0.0.0.0 --port 8080 \
    -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
    --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0
# Qwen3-30B-A3B auf Port 8082:

./llama.cpp/build/bin/llama-server \
    -m /mnt/data/gguf_models/Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL.gguf \
    -c 65536 --host 0.0.0.0 --port 8082 \
    -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
    --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0
# Qwen3-Coder-30B auf Port 8081:
./llama.cpp/build/bin/llama-server \
    -m /mnt/data/gguf_models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
    -c 65536 --host 0.0.0.0 --port 8081 \
    -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
    --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0
## Evaluierung starten
cd qwen3-30b-a3b
python3 eval_phase1.py    # Phase 1
python3 eval_phase2a.py   # Phase 2a
python3 eval_phase2b.py   # Phase 2b
Ergebnisse landen in results_v2/phase{N}_*.sqlite.

## Analyse
python3 scripts/analyze_all_phases.py -o docs/analysis_v2.md
Erzeugt Markdown-Tabellen mit Compliance-Raten pro Modell x Phase x Schema.
Reproduzierbarkeit

    Paper-Original: Phase 1 (yamls/phase1_original.yaml) ist byte-identisch mit canonicalmg/reverse-captcha-eval (MD5: c728786b9597c010da014eec9bc16a54). Grader ebenso (MD5: 733cefef56cb311ee678011f5e87efd8).

    Engine: llama.cpp (Build b11456)

    Kontext: 65536 Tokens

    Reasoning: deaktiviert (--reasoning off)

    Grader: packs/reverse_captcha/grader.py aus canonicalmg/reverse-captcha-eval

    Phasen 2a / 2b: Eigene Erweiterungen (dokumentiert in Thesis, Abschnitt Methodik)

## Ziel der Arbeit
Systematischer Vergleich der Anfälligkeit von Dense- und MoE-Modellen
für unsichtbare Unicode-Injection. Untersuchung der Effekte von
Hint-Leveln und Answer-Only-Anweisungen auf die Compliance-Rate

