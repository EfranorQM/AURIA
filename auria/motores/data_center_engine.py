from __future__ import annotations

"""
market_data_engine.py

Mantiene un cache en memoria {category: matrix} y lo actualiza cada
*interval* segundos (default: 300 s).  Ahora permite definir categorías
que NO deben incluir encantamientos (@1-@3) al consultar la API.
"""

import threading
import time
from typing import Dict, List, Optional

from auria.data.category_manager import CategoryManager
from auria.data.generic_market import GenericMarketSource, Row


class MarketDataEngine:
    """
    Refresca matrices de mercado por categoría en segundo plano.

    - NO_ENCHANT_CATEGORIES: cualquier categoría listada aquí se consultará
      con enchantments=[0]  → sólo ítems base, sin sufijos @1/@2/@3.
    """

    NO_ENCHANT_CATEGORIES = {"monturas"}   # ajusta a tu gusto

    def __init__(self, interval: int = 300,
                 cities: Optional[List[str]] = None) -> None:
        self.interval = interval
        self.cities   = cities
        self._cache: Dict[str, List[Row]] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._refresh()                                   # primer pull
        threading.Thread(target=self._loop, daemon=True).start()

    # ─────────── PUBLIC API ───────────
    def get_matrix(self,
                   categories: Optional[List[str] | str] = None) -> List[Row]:
        """
        Devuelve la matriz combinada de las categorías pedidas.

        - categories None → todas.
        - str             → una categoría.
        - list[str]       → unión de esas categorías.
        """
        if isinstance(categories, str):
            cats = [categories]
        elif categories is None:
            cats = list(CategoryManager.get_categories())
        else:
            cats = categories

        with self._lock:
            return [row for cat in cats for row in self._cache.get(cat, [])]

    def stop(self):
        """Detiene el hilo de refresco."""
        self._stop.set()

    # ─────────── INTERNALS ───────────
    def _loop(self):
        while not self._stop.wait(self.interval):
            self._refresh()

    def _refresh(self):
        for category in CategoryManager.get_categories():
            base_ids = CategoryManager.get_items(category)
            if not base_ids:
                continue

            ench = [0] if category in self.NO_ENCHANT_CATEGORIES else None

            src = GenericMarketSource(
                base_item_ids=base_ids,
                cities=self.cities,
                enchantments=ench          # 👈 evita @1-3 si corresponde
            )

            try:
                matrix = src.get_filtered_matrix()
            except Exception as exc:
                print(f"[WARN] No se pudo refrescar {category}: {exc}")
                continue

            with self._lock:
                self._cache[category] = matrix
            time.sleep(0.25)               # pequeño respiro para la API


# ─────────── Prueba rápida ───────────
if __name__ == "__main__":
    eng = MarketDataEngine(interval=15)   # demo, refresco rápido
    try:
        for _ in range(3):
            print("Top 3 monturas:", eng.get_matrix("monturas")[:3])
            time.sleep(6)
    finally:
        eng.stop()
