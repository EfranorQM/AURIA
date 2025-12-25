import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # carpeta AURIA/
DB_PATH = ROOT / "data" / "auria.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        con.executescript(schema_sql)
        con.commit()
    finally:
        con.close()

    print(f"OK: DB creada/actualizada en: {DB_PATH}")

if __name__ == "__main__":
    main()
