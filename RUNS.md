# Evaluierungs-Runs — Übersicht

## Run v1 — Oktober 2026

**Status:** abgeschlossen (aber mit Artefakten)
**Datum:** 2026-10-15 bis 2026-10-16
**Ordner:** `*/results_v1/`

**Parameter:**
- `max_tokens = 1024`
- `max_turns = 3`
- Grader: Original (Graves 2026)
- `tool_choice = auto`
- `temperature = 0.7`, `top_p = 0.8`

**Modelle:** Qwen3.5-27B, Qwen3-30B-A3B, Qwen3-Coder-30B
**Phasen:** 1 (Original), 2a (Enhanced), 2b (Answer-Only)
**Umfang:** 810 Läufe pro Modell und Phase

**Bekannte Probleme:**
- API-Fehlerrate bei Qwen3.5: 12–16 % (vor allem durch zu niedriges `max_tokens`)
- API-Fehler wurden in DB als `INCORRECT` klassifiziert (Bug, im v2-Lauf behoben)

## Run v2 — Oktober 2026 (in Arbeit)

**Status:** ⏳ läuft
**Datum:** 2026-10-17
**Ordner:** `*/results_v2/`

**Parameter:**
- `max_tokens = 8192`  (erhöht → Token-Limit-Fehler behoben)
- `max_turns = 10`     (erhöht → mehr Tool-Aufrufe möglich)
- Grader: Original (Graves 2026)
- `tool_choice = auto`
- `temperature = 0.7`, `top_p = 0.8`

**Modelle:** Qwen3.5-27B, Qwen3-30B-A3B, Qwen3-Coder-30B
**Phasen:** 1, 2a, 2b

**Änderungen gegenüber v1:**
1. `max_tokens` 1024 → 8192 (behebt Token-Limit-API-Fehler)
2. `max_turns` 3 → 10 (mehr Tool-Aufrufe möglich)
3. API-Fehler werden korrekt als `API_ERROR` klassifiziert (Bug-Fix)
4. `SAFETY_REFUSAL`-Kategorie entfernt (paper-konform)

**Erwartung:**
- API-Fehlerrate sinkt bei Qwen3.5 von ~15 % auf < 5 %
- Q3-30B + Coder: bleiben bei < 1,5 %
- Gesamtergebnis robuster, paper-konformer
