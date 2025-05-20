"""core.py  – fachada principal del bot de trade

• Arranca MarketDataEngine y MarketResultEngine
• Expone métodos sencillos de consulta
"""

from __future__ import annotations
from typing import List, Optional

from auria.motores.data_center_engine import MarketDataEngine
from auria.motores.results_engine     import MarketResultEngine, ItemOut
from auria.data.category_manager      import CategoryManager


class MarketCore:
    """Coordina motores de datos y resultados y provee API de consulta."""

    def __init__(self, interval: int = 300,
                 cities: Optional[List[str]] = None) -> None:
        # 1) centro de datos
        self.data_engine   = MarketDataEngine(interval=interval, cities=cities)
        # 2) motor de resultados
        self.result_engine = MarketResultEngine(self.data_engine,
                                                interval=interval)

    # ─────────── consultas genéricas ───────────
    def _query(self,
               categories: Optional[List[str] | str] = None,
               city_from: Optional[str] = None,
               city_to:   Optional[str] = None,
               limit: Optional[int] = None) -> List[ItemOut]:

        rows = self.result_engine.get_results(categories,
                                              city_from=city_from,
                                              city_to=city_to)
        return rows if limit is None else rows[:limit]

    # top global
    def all(self, limit: Optional[int] = None) -> List[ItemOut]:
        return self._query(limit=limit)

    # top por categoría(s)
    def top_category(self, category: str | List[str],
                     limit: Optional[int] = None) -> List[ItemOut]:
        return self._query(categories=category, limit=limit)

    # top por ciudad origen
    def top_city(self, city_from: str,
                 categories: Optional[List[str] | str] = None,
                 limit: Optional[int] = None) -> List[ItemOut]:
        return self._query(categories, city_from=city_from, limit=limit)

    # top ciudad_origen → ciudad_destino
    def top_between(self, city_from: str, city_to: str,
                    categories: Optional[List[str] | str] = None,
                    limit: Optional[int] = None) -> List[ItemOut]:
        return self._query(categories, city_from, city_to, limit)

    # ─────────── resumen por categoría ───────────
    def summary_by_category(self,
                            city_from: str | None = None,
                            city_to:   str | None = None,
                            limit: int = 20) -> dict[str, list]:
        """
        Devuelve las mejores *limit* rutas para cada categoría.
        Puede filtrar por ciudad origen/destino.
        """
        summary: dict[str, list] = {}
        for cat in CategoryManager.get_categories():
            routes = self.result_engine.get_results(
                categories=[cat],
                city_from=city_from,
                city_to=city_to
            )[:limit]
            summary[cat] = routes
        return summary

    # ─────────── utilidades ───────────
    @staticmethod
    def available_categories() -> List[str]:
        return CategoryManager.get_categories()

    # ─────────── ciclo de vida ───────────
    def stop(self):
        self.result_engine.stop()
        self.data_engine.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()


# demo rápido
if __name__ == "__main__":
    from time import sleep
    with MarketCore(interval=60) as core:
        sleep(10)                            # dejar que refresque
        print("Top FS → Martlock (monturas):")
        for r in core.top_between("Fort Sterling", "Martlock",
                                  "monturas", limit=3):
            print("  ", r)
