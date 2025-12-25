from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import sqlite3


@dataclass(frozen=True)
class TemplateSpec:
    template_key: str
    tier_min: int
    tier_max: int
    ench_min: int
    ench_max: int


class TemplateRepository:
    """
    Repo robusto: autodetecta nombres de tablas en SQLite.

    Busca:
      - tabla de categorías: tiene columna 'slug'
      - tabla de templates: tiene 'template_key', 'tier_min', 'tier_max', 'ench_min', 'ench_max'
      - tabla puente (opcional): tiene 'template_id' y 'category_id'
        Si no existe, intenta relación directa desde templates vía 'category_id' o 'category_slug'.
    """

    TEMPLATE_COLS = {"template_key", "tier_min", "tier_max", "ench_min", "ench_max"}
    CATEGORY_COLS = {"slug"}

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def list_for_category(self, category_slug: str, include_children: bool = False) -> List[TemplateSpec]:
        slug = category_slug.strip()

        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row

            tables = self._list_tables(con)
            if not tables:
                raise RuntimeError(
                    f"DB sin tablas (¿ruta incorrecta?). DB: {self.db_path}"
                )

            cat_table = self._find_table_with_cols(con, prefer=["categories"], required=self.CATEGORY_COLS)
            tpl_table = self._find_table_with_cols(con, prefer=["templates", "item_templates"], required=self.TEMPLATE_COLS)

            if cat_table is None:
                raise RuntimeError(f"No encontré tabla de categorías con columna 'slug'. Tablas: {tables}")
            if tpl_table is None:
                raise RuntimeError(
                    "No encontré tabla de templates con columnas: "
                    f"{sorted(self.TEMPLATE_COLS)}. Tablas: {tables}"
                )

            bridge = self._find_bridge_table(con, prefer=["template_categories", "category_templates", "template_category"])

            # where de categoría (exacto o include_children)
            where = "c.slug = ?"
            params: list = [slug]
            if include_children:
                where = "(c.slug = ? OR c.slug LIKE ?)"
                params = [slug, slug.rstrip("/") + "/%"]

            # Caso A: hay tabla puente template_id <-> category_id
            if bridge is not None:
                sql = f"""
                SELECT
                    t.template_key,
                    t.tier_min,
                    t.tier_max,
                    t.ench_min,
                    t.ench_max
                FROM {tpl_table} t
                JOIN {bridge} tc ON tc.template_id = t.id
                JOIN {cat_table} c ON c.id = tc.category_id
                WHERE {where}
                ORDER BY t.template_key
                """
                rows = con.execute(sql, params).fetchall()
                return [self._row_to_spec(r) for r in rows]

            # Caso B: relación directa desde templates
            tpl_cols = self._cols(con, tpl_table)

            if "category_id" in tpl_cols:
                sql = f"""
                SELECT
                    t.template_key,
                    t.tier_min,
                    t.tier_max,
                    t.ench_min,
                    t.ench_max
                FROM {tpl_table} t
                JOIN {cat_table} c ON c.id = t.category_id
                WHERE {where}
                ORDER BY t.template_key
                """
                rows = con.execute(sql, params).fetchall()
                return [self._row_to_spec(r) for r in rows]

            if "category_slug" in tpl_cols:
                # include_children en este caso se hace contra el campo category_slug del template
                if include_children:
                    sql = f"""
                    SELECT template_key, tier_min, tier_max, ench_min, ench_max
                    FROM {tpl_table}
                    WHERE (category_slug = ? OR category_slug LIKE ?)
                    ORDER BY template_key
                    """
                    rows = con.execute(sql, [slug, slug.rstrip("/") + "/%"]).fetchall()
                else:
                    sql = f"""
                    SELECT template_key, tier_min, tier_max, ench_min, ench_max
                    FROM {tpl_table}
                    WHERE category_slug = ?
                    ORDER BY template_key
                    """
                    rows = con.execute(sql, [slug]).fetchall()

                return [self._row_to_spec(r) for r in rows]

            raise RuntimeError(
                "Encontré tabla de templates pero no pude relacionarla a categorías.\n"
                f"tpl_table={tpl_table} cols={sorted(tpl_cols)}\n"
                f"cat_table={cat_table}\n"
                f"Tablas: {tables}\n"
                "Solución: usa una tabla puente con columnas (template_id, category_id) o agrega (category_id/category_slug) a templates."
            )

    # ---------- helpers ----------

    @staticmethod
    def _row_to_spec(r: sqlite3.Row) -> TemplateSpec:
        return TemplateSpec(
            template_key=str(r["template_key"]),
            tier_min=int(r["tier_min"]),
            tier_max=int(r["tier_max"]),
            ench_min=int(r["ench_min"]),
            ench_max=int(r["ench_max"]),
        )

    @staticmethod
    def _list_tables(con: sqlite3.Connection) -> List[str]:
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def _cols(con: sqlite3.Connection, table: str) -> set[str]:
        rows = con.execute(f"PRAGMA table_info({table})").fetchall()
        # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
        return {r[1] for r in rows}

    def _find_table_with_cols(
        self,
        con: sqlite3.Connection,
        *,
        prefer: List[str],
        required: set[str],
    ) -> Optional[str]:
        tables = self._list_tables(con)

        # Prioriza nombres típicos
        for name in prefer:
            if name in tables and required.issubset(self._cols(con, name)):
                return name

        # Búsqueda general
        for t in tables:
            if required.issubset(self._cols(con, t)):
                return t

        return None

    def _find_bridge_table(
        self,
        con: sqlite3.Connection,
        *,
        prefer: List[str],
    ) -> Optional[str]:
        tables = self._list_tables(con)
        needed = {"template_id", "category_id"}

        for name in prefer:
            if name in tables and needed.issubset(self._cols(con, name)):
                return name

        for t in tables:
            if needed.issubset(self._cols(con, t)):
                return t

        return None
