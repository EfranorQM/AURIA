import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "auria.db"

con = sqlite3.connect(DB_PATH)
try:
    rows = con.execute("""
        SELECT t.template_key, c.slug
        FROM item_templates t
        JOIN template_categories tc ON tc.template_id = t.id
        JOIN categories c ON c.id = tc.category_id
        ORDER BY c.slug, t.template_key
    """).fetchall()

    for r in rows:
        print(r)
finally:
    con.close()
