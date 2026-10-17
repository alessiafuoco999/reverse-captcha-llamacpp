#!/usr/bin/env python3
"""Re-graded eine SQLite-DB mit dem Original-Grader (ohne Neu-Inferenz)."""

import sys
import sqlite3
import yaml

sys.path.insert(0, '/home/student/bachelorarbeit/data/reverse-captcha-eval/packs/reverse_captcha')
from grader import grade

def regrade(db_path, yaml_path):
    # YAML laden (um expected + metadata zu bekommen)
    with open(yaml_path, encoding='utf-8') as f:
        cases = {c['id']: c for c in yaml.safe_load(f)}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT rowid, case_id, scheme, expected, response FROM results")
    rows = cur.fetchall()

    changed = 0
    for rowid, case_id, scheme, expected, response in rows:
        case = cases.get(case_id)
        if not case:
            continue
        metadata = case.get('metadata', {})
        metadata['scheme'] = case['scheme']

        # API-Fehler bleiben API_ERROR (nicht neu graden)
        if (response or '').startswith('API-ERROR-RESPONSE'):
            new_label, new_score = 'API_ERROR', 0.0
        else:
            result = grade(
                model_output=response or '',
                expected=expected,
                metadata=metadata,
            )
            new_label, new_score = result['label'], result['score']

        cur.execute(
            "UPDATE results SET label=?, score=? WHERE rowid=?",
            (new_label, new_score, rowid)
        )
        changed += 1

    conn.commit()
    conn.close()
    print(f"{db_path}: {changed} Zeilen neu gegraded")

if __name__ == "__main__":
    regrade(
        'qwen3-30b-a3b/results_v2/phase1_original.sqlite',
        'yamls/phase1_original.yaml'
    )
