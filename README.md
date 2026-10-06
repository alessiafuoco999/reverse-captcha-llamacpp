# Reverse-CAPTCHA: llama.cpp Stack

Vergleich der Anfälligkeit zweier Open-Weight-Modelle für unsichtbare Unicode-Injection unter identischen Inferenzbedingungen (llama.cpp).

## Modelle

| Modell | Typ | Parameter | Port |
|--------|-----|-----------|------|
| Qwen3.5-27B-UD-Q4_K_XL | General-Instruct (Dense) | 27B | 8080 |
| Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL | Code-spezialisiert (MoE) | 30B (3B aktiv) | 8081 |

## Struktur

- `yamls/` — Gemeinsame YAML-Dateien für beide Modelle
  - `phase1_original.yaml` — 270 Fälle, Original-Hint aus Paper
  - `phase2a_enhanced.yaml` — 270 Fälle, mit Code-Beispiel ord(c) - 0xE0000
  - `phase2b_answeronly.yaml` — 270 Fälle, mit Answer-Only-Anweisung
  - `test_subset_27.yaml` — 27 Fälle (3 pro Schema), Pilot-Test
  - `cases_original.yaml` — Backup (identisch mit phase1_original)

- `qwen3.5-27b/` — General-Modell
  - `eval_phase1.py` — Evaluierungsskript
  - `results/pilot_27cases.sqlite` — Pilot-Test (27 Fälle × 3 Wiederholungen)

- `qwen3-coder-30b/` — Code-Modell
  - `eval_phase1.py` — Evaluierungsskript
  - `results/pilot_27cases.sqlite` — Pilot-Test (27 Fälle × 3 Wiederholungen)

## Server-Start

Qwen3.5 auf Port 8080:

    ./llama.cpp/build/bin/llama-server \
        -m /mnt/data/gguf_models/Qwen3.5-27B-UD-Q4_K_XL.gguf \
        -c 65536 --host 0.0.0.0 --port 8080 \
        -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
        --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0

Qwen3-Coder auf Port 8081:

    ./llama.cpp/build/bin/llama-server \
        -m /mnt/data/gguf_models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
        -c 65536 --host 0.0.0.0 --port 8081 \
        -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
        --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0

## Pilot-Ergebnisse (n=9 pro Schema)

| Metrik | Qwen3.5-27B | Qwen3-Coder-30B | Fisher p |
|--------|-------------|-----------------|----------|
| tag_hint_full | 88,9 % | 22,2 % | 0,0152 |
| tag_hint_full_injection | 66,7 % | 11,1 % | 0,0498 |
| tag_hint_codepoints | 33,3 % | 0,0 % | 0,2059 |
| Utility | 100 % | 88,9 % | – |

Zentrale Erkenntnis: Das General-Modell Qwen3.5-27B ist signifikant anfälliger als das Code-Modell Qwen3-Coder-30B (p < 0,05 für beide Full-Hint-Schemata).

## Phasen-Plan

| Phase | YAML | Zweck |
|-------|------|-------|
| 1: Original | phase1_original.yaml | Referenz, Paper-Vergleich |
| 2a: Enhanced Hint | phase2a_enhanced.yaml | Angreifer-Optimierung |
| 2b: Enhanced + Answer-Only | phase2b_answeronly.yaml | Reasoning-Check-Quantifizierung |

## Ziel der Arbeit

Vergleichende Evaluierung der Anfälligkeit von Open-Weight-LLMs für unsichtbare Unicode-Injection. Der Fokus liegt auf der Isolierung des Modell-Effekts (Code-spezialisiert vs. General-Instruct) durch Konstanthaltung der Engine (llama.cpp).

## Reproduzierbarkeit

- Modelle: Qwen/Qwen3.5-27B und Qwen/Qwen3-Coder-30B-A3B-Instruct
- Engine: llama.cpp (Build b11456)
- Kontext: 65536 Tokens
- Reasoning: deaktiviert (--reasoning off)
- Grader: packs/reverse_captcha/grader.py aus canonicalmg/reverse-captcha-eval
