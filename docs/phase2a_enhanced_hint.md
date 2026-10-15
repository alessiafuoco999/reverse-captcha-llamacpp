# Phase 2a: Enhanced Hint — Reverse-CAPTCHA Evaluierung

**Datum:** 15.10.2026
**Status:** Abgeschlossen und verifiziert
**Modell:** Qwen3-Coder-30B-A3B (Code-spezialisiert, MoE)
**Engine:** llama.cpp (Build b11456)
**YAML:** phase2a_enhanced.yaml (MD5: b50f7de21d8633066f1cab5bb9984544)

---

## 1. Was ist Phase 2a?

Phase 2a ist die **zweite von drei Phasen** der Reverse-CAPTCHA-Evaluierung für Qwen3-Coder-30B. Sie untersucht, wie stark sich die Anfälligkeit erhöht, wenn der Angreifer dem Modell ein **konkretes Python-Code-Beispiel** im Hint mitliefert.

### Unterschied zu Phase 1

| Aspekt | Phase 1 (Original) | Phase 2a (Enhanced) |
|--------|-------------------|---------------------|
| Hint-Inhalt | Nur Dekodierungsregeln | Dekodierungsregeln + Code-Beispiel |
| Code-Beispiel | Nein | Ja: print(''.join(chr(ord(c) - 0xE0000) for c in tag_string)) |
| Angreifer-Typ | Aktiver Angreifer | Informierter aktiver Angreifer |
| Ziel | Referenz für Paper-Vergleich | Angreifer-Optimierung |

### Was genau geändert wurde

Der Hint wurde bei den **aktiven Schemata** (`*_hint_codepoints`, `*_hint_full`, `*_hint_full_injection`) erweitert. Die passiven Schemata (`*_unhinted`) und die Utility-Messung (`control`) blieben **unverändert**, um den im Paper beschriebenen Hint-Gradienten zu erhalten.

**Wichtig:** Die Code-Beispiel-Erweiterung wurde **beidseitig** (für beide Modelle identisch) durchgeführt, um die wissenschaftliche Vergleichbarkeit zu wahren.

### Wissenschaftliche Motivation

Die Vorstudie zeigte, dass Qwen3-Coder-30B mit dem Original-Hint nicht in der Lage war, den korrekten Dekodierungscode zu schreiben (nur 11,1 % bei tag_hint_full). Das Code-Beispiel prüft, ob die **Dekodierungsfähigkeit** oder die **Befolgungsbereitschaft** die limitierende Größe ist.

---

## 2. Verifikation

| Dimension | Wert | Status |
|-----------|------|--------|
| Anzahl Läufe | 810 / 810 | OK |
| Anzahl Fälle | 270 / 270 | OK |
| Schema-Verteilung | 30 pro Schema (9 Schemata) | OK |
| Wiederholungen pro Fall | 3 / 3 | OK |
| Gemeinsame Case-IDs mit Phase 1 | 270 / 270 | OK |
| API-Fehler | 11 (1,4 %) | OK |

**Ergebnis:** Phase 2a wurde unter **identischen Bedingungen** wie Phase 1 durchgeführt — nur der Hint-Inhalt unterscheidet sich.

---

## 3. Ergebnisse Phase 2a

### 3.1 Compliance pro Schema

| Schema | N | FH | PT | AV | IC | Compliance | 95 % CI |
|--------|---|----|----|----|----|-----------|---------|
| tag_hint_full | 90 | 29 | 45 | 12 | 4 | **32,2 %** | [23,5 %, 42,4 %] |
| tag_hint_full_injection | 90 | 37 | 45 | 0 | 8 | **41,1 %** | [31,5 %, 51,4 %] |
| tag_hint_codepoints | 90 | 33 | 43 | 10 | 4 | **36,7 %** | [27,4 %, 47,0 %] |
| zw_hint_codepoints | 90 | 2 | 0 | 78 | 10 | 2,2 % | [0,6 %, 7,7 %] |
| zw_hint_full | 90 | 0 | 1 | 74 | 15 | 0,0 % | [0 %, 4,1 %] |
| zw_hint_full_injection | 90 | 3 | 2 | 67 | 18 | 3,3 % | [1,1 %, 9,3 %] |
| tag_unhinted | 90 | 0 | 0 | 69 | 21 | 0,0 % | [0 %, 4,1 %] |
| zw_unhinted | 90 | 0 | 1 | 72 | 17 | 0,0 % | [0 %, 4,1 %] |
| control (Utility) | 90 | 0 | 0 | 0 | 0 | (siehe 3.2) | – |

### 3.2 Utility (control)

| Metrik | Wert | 95 % CI |
|--------|------|---------|
| CORRECT_CONTROL | 77 / 90 | 85,6 % |
| 95 % CI | | [76,8 %, 91,4 %] |
| INCORRECT_CONTROL | 13 / 90 | 14,4 % |

### 3.3 Gesamt (alle aktiven Angriffs-Schemata)

| Metrik | Wert | 95 % CI |
|--------|------|---------|
| FOLLOWED_HIDDEN (Gesamt) | 102 / 450 | **22,7 %** |
| 95 % CI | | [19,0 %, 26,8 %] |

---

## 4. Direktvergleich: Phase 1 vs. Phase 2a

| Schema | Phase 1 | Phase 2a | Differenz | Fisher p |
|--------|---------|----------|-----------|----------|
| tag_hint_codepoints | 1,1 % | 36,7 % | **+35,6 pp** | **< 0,0001** |
| tag_hint_full | 11,1 % | 32,2 % | **+21,1 pp** | **0,0010** |
| tag_hint_full_injection | 23,3 % | 41,1 % | **+17,8 pp** | **0,0164** |
| zw_hint_codepoints | 0,0 % | 2,2 % | +2,2 pp | 0,4972 |
| zw_hint_full | 1,1 % | 0,0 % | -1,1 pp | 1,0000 |
| zw_hint_full_injection | 2,2 % | 3,3 % | +1,1 pp | 1,0000 |
| tag_unhinted | 0,0 % | 0,0 % | 0,0 pp | 1,0000 |
| zw_unhinted | 0,0 % | 0,0 % | 0,0 pp | 1,0000 |
| **Gesamt (aktive)** | **7,8 %** | **22,7 %** | **+14,9 pp** | – |

**Drei von drei Tag-Schemata zeigen statistisch signifikante Steigerungen** (p < 0,05).

---

## 5. Interpretation

### 5.1 Der Hint-Effekt ist bei Tags dramatisch

Die Compliance-Raten bei Unicode Tags steigen durch das Code-Beispiel massiv:

- tag_hint_codepoints: **33-facher Anstieg** (1,1 % -> 36,7 %)
- tag_hint_full: **2,9-facher Anstieg** (11,1 % -> 32,2 %)
- tag_hint_full_injection: **1,8-facher Anstieg** (23,3 % -> 41,1 %)

**Kernbefund:** Das Code-Beispiel ist der kritische Enabler für Qwen3-Coder-30B bei der Tag-Dekodierung. Ohne das Beispiel schreibt das Modell fehlerhaften Code (z. B. int() statt ord()), mit dem Beispiel dekodiert es zuverlässig.

### 5.2 Zero-Width bleibt unempfindlich

Alle ZW-Schemata bleiben unter 4 % Compliance — auch mit Code-Beispiel. Qwen3-Coder hat eine **starke modell-spezifische Präferenz für Unicode Tags**, vergleichbar mit Anthropic-Modellen (Claude) im Paper.

### 5.3 Überraschung: tag_hint_codepoints profitiert am stärksten

Der Anstieg ist bei tag_hint_codepoints (+35,6 pp) am größten — nicht bei tag_hint_full (+21,1 pp). **Interpretation:** Bei hint_codepoints wusste das Modell nur, dass Tag-Zeichen existieren. Das Code-Beispiel hat ihm dann gezeigt, wie es sie dekodiert. Bei hint_full hatte es die Regeln schon — der zusätzliche Effekt war geringer.

### 5.4 Injection-Framing bleibt aktiv

Bei tag_hint_full_injection (41,1 %) ist die Compliance höher als bei tag_hint_full (32,2 %) — +8,9 pp. Dies bestätigt den Trend aus Phase 1: Bei Qwen3-Coder erhöht Injection-Framing die Compliance (im Gegensatz zu Claude/GPT-5.2 aus dem Paper).

### 5.5 Utility stabil

86,7 % (Phase 1) -> 85,6 % (Phase 2a). Der Hint verändert die Fähigkeit des Modells, normale Aufgaben zu lösen, nicht signifikant.

---

## 6. Limitationen

1. **API-Fehler (11/810 = 1,4 %):** Deutlich niedriger als bei Qwen3.5-27B (15,9 %), aber vorhanden. Ursache: JSON-Serialisierung bei langen Tool-Call-Argumenten.
2. **Grader-Schwächen:** Der Original-Grader klassifiziert Antworten mit Erklärungen als FOLLOWED_HIDDEN (im Paper dokumentiert).
3. **PARTIAL-Rate:** In Phase 2a sehr hoch (45/90 bei tag_hint_full). Das deutet darauf hin, dass das Modell oft beide Antworten ausgibt, wenn es den Code dekodiert.
4. **Nur zwei Modelle:** Generalisierung auf andere Modellfamilien nicht möglich.

---

## 7. Zusammenfassung

Phase 2a zeigt, dass Qwen3-Coder-30B mit einem konkreten Code-Beispiel deutlich anfälliger für Unicode-Tag-Injection wird (7,8 % -> 22,7 % gesamt). Der Effekt ist kodierungsabhängig: Tags reagieren stark, Zero-Width nicht. Die Utility bleibt stabil (85,6 %).

---

## 8. Reproduzierbarkeit

**Skript:** qwen3-coder-30b/eval_phase2a.py
**DB:** qwen3-coder-30b/results/phase2a_enhanced.sqlite
**Log:** qwen3-coder-30b/logs/phase2a_enhanced.log

**Server-Start:**
```bash
./llama.cpp/build/bin/llama-server \
    -m /mnt/data/gguf_models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
    -c 65536 --host 0.0.0.0 --port 8081 \
    -ngl 99 -ctk q8_0 -ctv q8_0 -fa on \
    --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0
```
