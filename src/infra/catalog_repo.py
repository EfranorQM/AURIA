from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set


@dataclass(frozen=True)
class TemplateRow:
    template_key: str
    mode: str                # 'TIERED' | 'EXACT'
    tier_min: int | None
    tier_max: int | None
    ench_min: int
    ench_max: int
    qualities_csv: str       # "1,2,3,4,5"


def _parse_qualities(csv: str) -> List[int]:
    parts = [p.strip() for p in (csv or "").split(",") if p.strip()]
    out: List[int] = []
    for p in parts:
        n = int(p)
        if n < 1 or n > 5:
            # mantenemos 1..5 (Normal..Masterpiece)
            continue
        out.append(n)
    return sorted(set(out)) or [1, 2, 3, 4, 5]


def expand_template_to_item_ids(t: TemplateRow) -> List[str]:
    """
    Expande un template a item_ids listos para la API:
    - EXACT: devuelve template_key tal cual
    - TIERED: genera T{tier}_{template_key} y aplica @ench (0 = sin sufijo)
    """
    mode = (t.mode or "TIERED").upper()

    if mode == "EXACT":
        return [t.template_key.upper()]

    if mode != "TIERED":
        raise ValueError(f"Modo no soportado: {t.mode}")

    if t.tier_min is None or t.tier_max is None:
        raise ValueError(f"Template TIERED sin tiers: {t.template_key}")

    core_ids: List[str] = []
    base = t.template_key.upper()
    for tier in range(int(t.tier_min), int(t.tier_max) + 1):
        core_ids.append(f"T{tier}_{base}")

    # enchantments
    expanded: List[str] = []
    for cid in core_ids:
        for ench in range(int(t.ench_min), int(t.ench_max) + 1):
            if ench == 0:
                expanded.append(cid)
            else:
                expanded.append(f"{cid}@{ench}")
    return expanded


class CatalogRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    def get_templates_by_category_slug(self, slug: str, include_children: bool = True) -> List[TemplateRow]:
        """
        Retorna templates activos para una categoría slug.
        include_children=True incluye todo el subárbol (CTE recursivo).
        """
        slug = slug.strip()

        if include_children:
            sql = """
            WITH RECURSIVE subtree(id) AS (
              SELECT id FROM categories WHERE slug = ?
              UNION ALL
              SELECT c.id FROM categories c
              JOIN subtree s ON c.parent_id = s.id
            )
            SELECT t.template_key, t.mode, t.tier_min, t.tier_max, t.ench_min, t.ench_max, t.qualities
            FROM item_templates t
            JOIN template_categories tc ON tc.template_id = t.id
            JOIN subtree s ON s.id = tc.category_id
            WHERE t.is_active = 1
            ORDER BY t.template_key
            """
            params = (slug,)
        else:
            sql = """
            SELECT t.template_key, t.mode, t.tier_min, t.tier_max, t.ench_min, t.ench_max, t.qualities
            FROM item_templates t
            JOIN template_categories tc ON tc.template_id = t.id
            JOIN categories c ON c.id = tc.category_id
            WHERE c.slug = ? AND t.is_active = 1
            ORDER BY t.template_key
            """
            params = (slug,)

        con = self._connect()
        try:
            rows = con.execute(sql, params).fetchall()
        finally:
            con.close()

        if not rows:
            raise ValueError(f"No se encontraron templates para slug='{slug}'. ¿Existe la categoría? ¿Hay templates linkeados?")

        out: List[TemplateRow] = []
        for r in rows:
            out.append(
                TemplateRow(
                    template_key=r[0],
                    mode=r[1],
                    tier_min=r[2],
                    tier_max=r[3],
                    ench_min=int(r[4]),
                    ench_max=int(r[5]),
                    qualities_csv=r[6],
                )
            )
        return out

    def get_item_ids_for_category(self, slug: str, include_children: bool = True) -> List[str]:
        """
        Retorna item_ids expandidos listos para la API para una categoría.
        """
        templates = self.get_templates_by_category_slug(slug, include_children=include_children)
        item_ids: List[str] = []
        for t in templates:
            item_ids.extend(expand_template_to_item_ids(t))
        # dedupe manteniendo orden
        seen: Set[str] = set()
        ordered: List[str] = []
        for x in item_ids:
            if x not in seen:
                seen.add(x)
                ordered.append(x)
        return ordered

    def get_qualities_for_category(self, slug: str, include_children: bool = True) -> List[int]:
        """
        Junta qualities de todos los templates de la categoría y devuelve una lista única ordenada.
        """
        templates = self.get_templates_by_category_slug(slug, include_children=include_children)
        qs: Set[int] = set()
        for t in templates:
            qs.update(_parse_qualities(t.qualities_csv))
        return sorted(qs)
