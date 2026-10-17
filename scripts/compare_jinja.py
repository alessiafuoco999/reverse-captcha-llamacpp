#!/usr/bin/env python3
"""Vergleicht API-Fehler-Tests mit und ohne Jinja."""

import sqlite3, os

DB_ORIG = "/tmp/qwen35_error_analysis.sqlite"
DB_JINJA = "/tmp/qwen35_jinja_analysis.sqlite"

def stats(db, label, max_tokens_filter=None):
    if not os.path.exists(db):
        print(f"\n=== {label} === [FEHLT: {db}]")
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    where = f"WHERE max_tokens = {max_tokens_filter}" if max_tokens_filter else ""
    cur.execute(f"""
        SELECT finish_reason, json_valid, COUNT(*), ROUND(AVG(args_len))
        FROM results {where}
        GROUP BY finish_reason, json_valid
        ORDER BY finish_reason, json_valid
    """)
    rows = cur.fetchall()
    cur.execute(f"SELECT COUNT(*), COALESCE(SUM(json_valid),0) FROM results {where}")
    total, valid = cur.fetchone()
    conn.close()

    print(f"\n=== {label} ===")
    if total == 0:
        print("Keine Daten")
        return
    print(f"Gesamt: {total}  | Valide: {valid}  | Erfolgsrate: {valid/total*100:.1f}%")
    print(f"{'finish_reason':<15} {'json_valid':<12} {'n':>4} {'avg_args':>10}")
    print("-" * 45)
    for fr, jv, n, avg in rows:
        print(f"{str(fr):<15} {str(jv):<12} {n:>4} {str(avg):>10}")

stats(DB_ORIG, "OHNE Jinja, max_tokens=1024", 1024)
stats(DB_ORIG, "OHNE Jinja, max_tokens=4096", 4096)
stats(DB_ORIG, "OHNE Jinja, max_tokens=8192", 8192)
stats(DB_JINJA, "MIT Jinja, max_tokens=8192")

# Direkter Vergleich bei 8192
print("\n" + "=" * 55)
print("  DIREKTER VERGLEICH bei max_tokens=8192")
print("=" * 55)

for db, label in [(DB_ORIG, "OHNE Jinja"), (DB_JINJA, "MIT Jinja")]:
    if not os.path.exists(db):
        print(f"{label:<15}: DB fehlt")
        continue
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(SUM(json_valid),0) FROM results WHERE max_tokens = 8192")
    total, valid = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM results WHERE max_tokens=8192 AND finish_reason='stop'")
    stops = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM results WHERE max_tokens=8192 AND finish_reason='length'")
    lengths = cur.fetchone()[0]
    conn.close()
    if total:
        print(f"{label:<15}: {valid}/{total} valide ({valid/total*100:.1f}%) | stop={stops} | length={lengths}")
    else:
        print(f"{label:<15}: keine Daten bei 8192")
