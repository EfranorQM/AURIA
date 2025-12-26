from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

# Domain
from src.domain.catalog_bm_analyzer import (
    CatalogBMAnalyzer,
    CatalogReport,
    CategoryRun,
    TemplateRun,
)
from src.domain.bm_analyzer import FlipResult  # dataclass


router = APIRouter(prefix="/black-market", tags=["black-market"])

DB_PATH = Path(__import__("os").getenv("DB_PATH", "data/auria.db"))


# -------------------------
# Schemas de respuesta
# -------------------------
class FlipResultOut(BaseModel):
    item_id: str
    origin_quality: int
    bm_quality_used: int
    origin_city: str

    origin_price: int
    origin_price_source: str
    bm_price: int
    bm_price_source: str

    profit_net: int
    margin_net: float

    profit_flip: int
    margin_flip: float
    profit_order: int
    margin_order: float

    is_robust: bool


class TemplateRunOut(BaseModel):
    template_key: str
    results: List[FlipResultOut]


class CategoryRunOut(BaseModel):
    category_slug: str
    templates: List[TemplateRunOut]
    top_results: List[FlipResultOut]


class CatalogReportOut(BaseModel):
    categories: List[CategoryRunOut]
    top_global: List[FlipResultOut]


# -------------------------
# Serializadores
# -------------------------
def flipresult_to_out(r: FlipResult) -> FlipResultOut:
    return FlipResultOut(
        item_id=r.item_id,
        origin_quality=r.origin_quality,
        bm_quality_used=r.bm_quality_used,
        origin_city=r.origin_city,

        origin_price=r.origin_price,
        origin_price_source=r.origin_price_source,
        bm_price=r.bm_price,
        bm_price_source=r.bm_price_source,

        profit_net=r.profit_net,
        margin_net=r.margin_net,

        profit_flip=r.profit_flip,
        margin_flip=r.margin_flip,
        profit_order=r.profit_order,
        margin_order=r.margin_order,

        is_robust=r.is_robust,
    )


def template_run_to_out(t: TemplateRun) -> TemplateRunOut:
    return TemplateRunOut(
        template_key=t.template_key,
        results=[flipresult_to_out(r) for r in t.results],
    )


def category_run_to_out(c: CategoryRun) -> CategoryRunOut:
    return CategoryRunOut(
        category_slug=c.category_slug,
        templates=[template_run_to_out(t) for t in c.templates],
        top_results=[flipresult_to_out(r) for r in c.top_results],
    )


def catalog_report_to_out(r: CatalogReport) -> CatalogReportOut:
    return CatalogReportOut(
        categories=[category_run_to_out(c) for c in r.categories],
        top_global=[flipresult_to_out(x) for x in r.top_global],
    )


# -------------------------
# Endpoints
# -------------------------
@router.get("/catalog/categories", response_model=List[str])
def list_categories_with_templates():
    """
    Lista categorías (slug) que tienen templates activos asociados.
    Útil para el frontend (dropdown/multiselect).
    """
    try:
        runner = CatalogBMAnalyzer(db_path=DB_PATH)
        return runner.list_categories_with_templates()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"DB not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {e}")


@router.get("/catalog/analysis", response_model=CatalogReportOut)
def analyze_catalog_bm(
    category_slugs: Optional[List[str]] = Query(
        None,
        description="Si se omite, analiza todas las categorías con templates. "
                    "Puedes repetir el query param: ?category_slugs=a&category_slugs=b",
    ),
    include_children: bool = Query(False, description="Si True, incluye templates de subcategorías hijas"),
    top_n_per_template: int = Query(25, ge=1, le=500),
    top_n_per_category: int = Query(100, ge=1, le=5000),
    top_n_global: int = Query(200, ge=1, le=20000),
    min_profit_net: int = Query(1, ge=0),
    min_margin_net: float = Query(0.0, ge=0.0),
):
    """
    Escaneo completo (catálogo):
      - por categoría (y templates)
      - top por categoría
      - top global del catálogo
    """
    try:
        runner = CatalogBMAnalyzer(db_path=DB_PATH)
        report = runner.run(
            category_slugs=category_slugs,
            include_children=include_children,
            top_n_per_template=top_n_per_template,
            top_n_per_category=top_n_per_category,
            top_n_global=top_n_global,
            min_profit_net=min_profit_net,
            min_margin_net=min_margin_net,
        )
        return catalog_report_to_out(report)

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"DB not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Catalog analysis failed: {e}")
