"""Motor de resultados (MarketResultEngine)

• Se conecta a un MarketDataEngine ya creado.
• Cada *interval* segundos (por defecto el mismo que el data‑engine)
  recalcula los mejores trades por categoría usando ArbitrageAnalyzer.
• Exposición de API:
    get_results(categories=None,
                city_from=None,
                city_to=None) -> list[ItemOut]

  - categories None      → todas las categorías
  - str                  → una categoría
  - list[str]            → unión de esas categorías
  - city_from / city_to  → filtros opcionales (se re‑filtran al vuelo, no
                           regeneran análisis, por lo que es instantáneo)

Dependencias: category_manager.py, analyzer.py, data_center_engine.py
"""
from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional

from auria.motores.data_center_engine import MarketDataEngine, Row
from auria.core.analyzer import ArbitrageAnalyzer, ItemOut
from auria.data.category_manager import CategoryManager


class MarketResultEngine:
    """Motor que mantiene en caché las rutas de arbitraje por categoría."""

    def __init__(self, data_engine: MarketDataEngine, interval: Optional[int] = None):
        self.data_engine = data_engine
        self.interval = interval or data_engine.interval

        self._lock = threading.Lock()
        self._results: Dict[str, List[ItemOut]] = {}

        self._stop_event = threading.Event()
        # Primera generación síncrona
        self._refresh()
        # Hilo de actualización
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # -------------------------------------------------- public API
    def get_results(
        self,
        categories: Optional[List[str]] | str = None,
        city_from: Optional[str] = None,
        city_to: Optional[str] = None,
    ) -> List[ItemOut]:
        """Devuelve las rutas de arbitraje ya calculadas.

        • categories None  → todas las categorías.
        • str             → una categoría.
        • list[str]       → unión de esas categorías.
        • city_from / city_to se aplican como filtros en memoria (rápido).
        """
        if isinstance(categories, str):
            cats = [categories]
        elif categories is None:
            cats = CategoryManager.get_categories()
        else:
            cats = categories

        with self._lock:
            union = [row for cat in cats for row in self._results.get(cat, [])]

        # filtros opcionales sobre los ItemOut
        if city_from:
            union = [r for r in union if r[2] == city_from]
        if city_to:
            union = [r for r in union if r[4] == city_to]
        return union

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)

    # -------------------------------------------------- internals
    def _loop(self):
        while not self._stop_event.wait(self.interval):
            self._refresh()

    def _refresh(self):
        """Recalcula análisis para cada categoría."""
        new_results: Dict[str, List[ItemOut]] = {}
        for cat in CategoryManager.get_categories():
            matrix: List[Row] = self.data_engine.get_matrix(cat)
            analyzer = ArbitrageAnalyzer(matrix)
            best = analyzer.best_trades()  # sin filtros → top ordenado
            new_results[cat] = best
        with self._lock:
            self._results = new_results


# Demo -----------------------------------------------------------
if __name__ == "__main__":
    data_engine = MarketDataEngine(interval=60)  # refresco cada minuto
    res_engine = MarketResultEngine(data_engine)

    try:
        time.sleep(5)  # deja que genere
        print("Mejores monturas:")
        for row in res_engine.get_results("monturas")[:3]:
            print(" ", row)

        print("\nMejores rutas Fort Sterling → cualquiera (top 5):")
        for row in res_engine.get_results(city_from="Fort Sterling")[:5]:
            print(" ", row)

    finally:
        res_engine.stop()
        data_engine.stop()
