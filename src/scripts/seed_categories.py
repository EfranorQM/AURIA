import sqlite3
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "auria.db"
CATEGORIES_YAML = ROOT / "config" / "categories.yaml"

def upsert_category(con: sqlite3.Connection, name: str, slug: str, parent_id: int | None) -> int:
    row = con.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    if row:
        cat_id = row[0]
        con.execute(
            "UPDATE categories SET name = ?, parent_id = ? WHERE id = ?",
            (name, parent_id, cat_id),
        )
        return cat_id

    cur = con.execute(
        "INSERT INTO categories(name, slug, parent_id) VALUES (?, ?, ?)",
        (name, slug, parent_id),
    )
    return cur.lastrowid

def insert_tree(con: sqlite3.Connection, node: dict, parent_id: int | None):
    cat_id = upsert_category(con, node["name"], node["slug"], parent_id)
    for child in node.get("children", []) or []:
        insert_tree(con, child, cat_id)

def main():
    data = yaml.safe_load(CATEGORIES_YAML.read_text(encoding="utf-8"))
    roots = data.get("categories", [])

    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        for r in roots:
            insert_tree(con, r, None)
        con.commit()
    finally:
        con.close()

    print("OK: categorías cargadas en SQLite")

if __name__ == "__main__":
    main()
