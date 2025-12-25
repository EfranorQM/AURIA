import sqlite3
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "auria.db"
TEMPLATES_YAML = ROOT / "config" / "templates.yaml"


def csv_qualities(qs) -> str:
    # qs puede venir como lista [1,2,3] o como string "1,2,3"
    if qs is None:
        return "1,2,3,4,5"
    if isinstance(qs, str):
        # normaliza espacios
        return ",".join([p.strip() for p in qs.split(",") if p.strip()])
    if isinstance(qs, list):
        return ",".join(str(int(x)) for x in qs)
    raise ValueError(f"qualities inválidas: {qs!r}")


def get_category_id(con: sqlite3.Connection, slug: str) -> int:
    row = con.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    if not row:
        raise ValueError(
            f"No existe la categoría slug='{slug}'. Revisa config/categories.yaml y seed_categories.py"
        )
    return int(row[0])


def upsert_template(con: sqlite3.Connection, t: dict) -> int:
    template_key = t["template_key"].strip().upper()
    mode = (t.get("mode") or "TIERED").strip().upper()

    if mode not in ("TIERED", "EXACT"):
        raise ValueError(f"mode inválido para {template_key}: {mode}")

    tier_min = t.get("tier_min")
    tier_max = t.get("tier_max")

    # Para EXACT no exigimos tiers
    if mode == "TIERED":
        if tier_min is None or tier_max is None:
            raise ValueError(f"{template_key}: TIERED requiere tier_min y tier_max")
        tier_min = int(tier_min)
        tier_max = int(tier_max)

    ench_min = int(t.get("ench_min", 0))
    ench_max = int(t.get("ench_max", 0))
    qualities = csv_qualities(t.get("qualities"))

    is_active = int(t.get("is_active", 1))
    notes = t.get("notes")

    row = con.execute(
        "SELECT id FROM item_templates WHERE template_key = ?",
        (template_key,),
    ).fetchone()

    if row:
        template_id = int(row[0])
        con.execute(
            """
            UPDATE item_templates
               SET mode = ?, tier_min = ?, tier_max = ?, ench_min = ?, ench_max = ?,
                   qualities = ?, is_active = ?, notes = ?
             WHERE id = ?
            """,
            (mode, tier_min, tier_max, ench_min, ench_max, qualities, is_active, notes, template_id),
        )
        return template_id

    cur = con.execute(
        """
        INSERT INTO item_templates(template_key, mode, tier_min, tier_max, ench_min, ench_max, qualities, is_active, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (template_key, mode, tier_min, tier_max, ench_min, ench_max, qualities, is_active, notes),
    )
    return int(cur.lastrowid)


def link_template_to_category(con: sqlite3.Connection, template_id: int, category_id: int):
    con.execute(
        """
        INSERT OR IGNORE INTO template_categories(template_id, category_id)
        VALUES (?, ?)
        """,
        (template_id, category_id),
    )


def clear_template_links(con: sqlite3.Connection, template_id: int):
    con.execute("DELETE FROM template_categories WHERE template_id = ?", (template_id,))


def expand_templates(data: dict) -> list[dict]:
    """
    Soporta:
      - templates: [ {...}, {...} ]  (formato viejo)
      - template_groups: [
          {
            name: "axes",
            mode/tier_min/.../qualities/categories: ...,
            template_keys: ["MAIN_AXE", "2H_AXE", ...]
          }
        ]

    Además, template_keys puede contener overrides:
      template_keys:
        - MAIN_AXE
        - template_key: 2H_AXE_AVALON
          ench_max: 3
    """
    out: list[dict] = []

    # 1) formato viejo (si existe)
    old_templates = data.get("templates") or []
    if not isinstance(old_templates, list):
        raise ValueError("templates debe ser una lista")

    for t in old_templates:
        if not isinstance(t, dict):
            raise ValueError(f"templates contiene un elemento no-dict: {t!r}")
        out.append(t)

    # 2) grupos
    groups = data.get("template_groups") or []
    if groups and not isinstance(groups, list):
        raise ValueError("template_groups debe ser una lista")

    for g in groups:
        if not isinstance(g, dict):
            raise ValueError(f"template_groups contiene un elemento no-dict: {g!r}")

        keys = g.get("template_keys") or g.get("keys") or []
        if not isinstance(keys, list) or not keys:
            raise ValueError(f"template_group sin template_keys: {g.get('name', '<sin name>')}")

        # Base = todo menos metadata del grupo
        base = dict(g)
        base.pop("template_keys", None)
        base.pop("keys", None)
        base.pop("name", None)

        # Validación mínima: deben existir categories en el grupo o en el override
        for k in keys:
            if isinstance(k, str):
                item = dict(base)
                item["template_key"] = k
                out.append(item)
            elif isinstance(k, dict):
                if "template_key" not in k:
                    raise ValueError(f"override sin template_key en group {g.get('name')}: {k!r}")
                item = dict(base)
                item.update(k)  # overrides por ítem
                out.append(item)
            else:
                raise ValueError(f"template_keys inválido (debe ser str o dict): {k!r}")

    return out


def main():
    if not TEMPLATES_YAML.exists():
        raise FileNotFoundError(f"No existe {TEMPLATES_YAML}. Crea config/templates.yaml")

    data = yaml.safe_load(TEMPLATES_YAML.read_text(encoding="utf-8")) or {}
    templates = expand_templates(data)

    if not templates:
        print("No hay templates (ni groups) en config/templates.yaml")
        return

    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("PRAGMA foreign_keys = ON;")

        for t in templates:
            template_id = upsert_template(con, t)

            # Reemplazamos links para que el YAML sea “fuente de verdad”
            clear_template_links(con, template_id)

            cats = t.get("categories", []) or []
            if not cats:
                raise ValueError(f"{t.get('template_key')}: no tiene categories[]")

            for slug in cats:
                category_id = get_category_id(con, slug.strip())
                link_template_to_category(con, template_id, category_id)

        con.commit()
    finally:
        con.close()

    print("OK: templates cargados y enlazados a categorías (incluye template_groups)")


if __name__ == "__main__":
    main()
