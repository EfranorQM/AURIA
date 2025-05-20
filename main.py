# main.py – punto de arranque HTTP
from fastapi import FastAPI, Query
from typing import List, Optional

from auria.core.core import MarketCore

core = MarketCore(interval=200)      # se auto-enciende

app = FastAPI(title="Albion Trade-Bot API")

@app.get("/categories")
def categories():
    """Lista de categorías disponibles."""
    return core.available_categories()

@app.get("/routes")
def routes(
    categories: Optional[str] = Query(
        None,
        description="Una o varias categorías separadas por coma, "
                    "ej: monturas,recursos"),
    city_from: Optional[str] = Query(None, description="Ciudad de origen"),
    city_to: Optional[str]   = Query(None, description="Ciudad destino"),
    limit: int = Query(200, ge=1, le=100)
):
    """
    Devuelve rutas de arbitraje ya calculadas.

    - sin parámetros → top global  
    - ?categories=monturas → solo monturas  
    - ?city_from=Fort Sterling → lo que sale de Fort Sterling  
    - combina como quieras.
    """
    cats = categories.split(",") if categories else None
    return core._query(cats, city_from, city_to, limit)  # método interno expuesto

@app.on_event("shutdown")
def shutdown_event():
    core.stop()


@app.get("/routes/summary")
def routes_summary(
    city_from: str | None = Query(None),
    city_to:   str | None = Query(None),
    limit: int = Query(40, ge=1, le=100)
):
    """
    Resumen de mejores rutas por categoría
    (puedes filtrar por city_from / city_to).
    """
    return core.summary_by_category(city_from=city_from,
                                    city_to=city_to,
                                    limit=limit)