from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

# Importa tus dataclasses y analyzer
from src.domain.category_bm_analyzer import CategoryBMAnalyzer  
from src.domain.bm_analyzer import FlipResult  # dataclass
from src.domain.category_bm_analyzer import TemplateGroupResult, CategoryAnalysis  # dataclasses

router = APIRouter(prefix="/black-market", tags=["black-market"])

# Puedes configurar DB_PATH por env var
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


class TemplateGroupResultOut(BaseModel):
    template_key: str
    results: List[FlipResultOut]


class CategoryAnalysisOut(BaseModel):
    category_slug: str
    groups: List[TemplateGroupResultOut]
    all_results: List[FlipResultOut]


# -------------------------
# Serializadores (dataclass -> dict compatible)
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


def template_group_to_out(g: TemplateGroupResult) -> TemplateGroupResultOut:
    return TemplateGroupResultOut(
        template_key=g.template_key,
        results=[flipresult_to_out(r) for r in g.results],
    )


def category_analysis_to_out(a: CategoryAnalysis) -> CategoryAnalysisOut:
    return CategoryAnalysisOut(
        category_slug=a.category_slug,
        groups=[template_group_to_out(g) for g in a.groups],
        all_results=[flipresult_to_out(r) for r in a.all_results],
    )


# -------------------------
# Endpoint
# -------------------------
@router.get("/categories/{slug:path}/analysis", response_model=CategoryAnalysisOut)
def analyze_category_bm(
    slug: str,
    include_children: bool = Query(False, description="Si True, incluye templates de subcategorías hijas"),
    top_n_per_template: int = Query(25, ge=1, le=500),
    top_n_total: Optional[int] = Query(100, ge=1, le=5000),
    min_profit_net: int = Query(1, ge=0),
    min_margin_net: float = Query(0.0, ge=0.0),
):
    """
    Analiza flipping del Black Market para una categoría (slug).
    Ej: /black-market/categories/equipamiento/armas/hachas/analysis
    """
    try:
        analyzer = CategoryBMAnalyzer(db_path=DB_PATH)
        analysis = analyzer.run(
            category_slug=slug,
            include_children=include_children,
            top_n_per_template=top_n_per_template,
            top_n_total=top_n_total,
            min_profit_net=min_profit_net,
            min_margin_net=min_margin_net,
        )
        return category_analysis_to_out(analysis)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"DB not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
