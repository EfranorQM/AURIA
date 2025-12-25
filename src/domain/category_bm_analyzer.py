from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import requests

from src.domain.bm_analyzer import BMFlippingAnalyzer, FlipResult
from src.infra.template_repo import TemplateRepository, TemplateSpec


@dataclass(frozen=True)
class TemplateGroupResult:
    template_key: str
    results: List[FlipResult]


@dataclass(frozen=True)
class CategoryAnalysis:
    category_slug: str
    groups: List[TemplateGroupResult]
    all_results: List[FlipResult]


class CategoryBMAnalyzer:
    """
    Orquesta análisis BM por categoría:
      category_slug -> templates -> BMFlippingAnalyzer por template_key
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.template_repo = TemplateRepository(self.db_path)

        # Sesión compartida (mejor rendimiento y menos overhead TCP)
        self._session = requests.Session()

    def run(
        self,
        category_slug: str,
        *,
        include_children: bool = False,
        top_n_per_template: int = 25,
        top_n_total: Optional[int] = 100,
        min_profit_net: int = 1,
        min_margin_net: float = 0.0,
    ) -> CategoryAnalysis:
        specs = self.template_repo.list_for_category(category_slug, include_children=include_children)
        if not specs:
            return CategoryAnalysis(category_slug=category_slug, groups=[], all_results=[])

        groups: List[TemplateGroupResult] = []
        all_results: List[FlipResult] = []

        for spec in specs:
            analyzer = self._make_bm_analyzer(spec)
            results = analyzer.run(
                min_profit_net=min_profit_net,
                min_margin_net=min_margin_net,
                top_n=top_n_per_template,
            )
            groups.append(TemplateGroupResult(template_key=spec.template_key, results=results))
            all_results.extend(results)

        # Ranking global igual al de BMFlippingAnalyzer (robust, profit_net, margin_net)
        all_results.sort(key=lambda r: (r.is_robust, r.profit_net, r.margin_net), reverse=True)

        if top_n_total is not None:
            all_results = all_results[:top_n_total]

        return CategoryAnalysis(
            category_slug=category_slug,
            groups=groups,
            all_results=all_results,
        )

    def _make_bm_analyzer(self, spec: TemplateSpec) -> BMFlippingAnalyzer:
        """
        Crea el BMFlippingAnalyzer por template.
        Nota: si quieres reutilizar la misma requests.Session dentro de FastMarketQuery,
        podemos extender FastMarketQuery/BMFlippingAnalyzer para aceptar session.
        Por ahora funciona igual sin eso; solo es una optimización.
        """
        return BMFlippingAnalyzer(
            base_item=spec.template_key,
            tier_min=spec.tier_min,
            tier_max=spec.tier_max,
            ench_min=spec.ench_min,
            ench_max=spec.ench_max,
        )
