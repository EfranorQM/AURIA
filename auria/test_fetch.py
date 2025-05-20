"""test_fetch.py – util rápido para testear CategoryManager + GenericMarketSource

Uso en terminal:
    python test_fetch.py                   # prueba todas las categorías
    python test_fetch.py monturas          # solo monturas
    python test_fetch.py monturas recursos # varias categorías

Opciones de personalización dentro del script:
    CITIES_FILTER   → limita lista de ciudades (None = todas)
    SHOW_ROWS       → cuántas filas imprimir por categoría
"""
from __future__ import annotations

import sys
from typing import List, Optional
from pprint import pprint

from data.category_manager import CategoryManager
from data.generic_market import GenericMarketSource

CITIES_FILTER: Optional[List[str]] = None   # ej. ["Bridgewatch", "Martlock"]
SHOW_ROWS = 100                               # primeras N filas por categoría


def fetch_category(cat: str):
    ids = CategoryManager.get_items(cat)
    if not ids:
        print(f"[WARN] Sin ítems para categoría '{cat}'")
        return []

    source = GenericMarketSource(base_item_ids=ids, cities=CITIES_FILTER)
    matrix = source.get_filtered_matrix()
    return matrix


def main():
    cats = sys.argv[1:] or CategoryManager.get_categories()

    for cat in cats:
        print("\n===", cat.upper(), "===")
        try:
            mtx = fetch_category(cat)
        except Exception as exc:
            print("[ERROR]", exc)
            continue
        print(f"Filas obtenidas: {len(mtx)}")
        pprint(mtx[:SHOW_ROWS])


if __name__ == "__main__":
    main()
