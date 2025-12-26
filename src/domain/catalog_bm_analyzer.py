from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
import sqlite3
import requests

from src.domain.bm_analyzer import BMFlippingAnalyzer, FlipResult
from src.infra.template_repo import TemplateRepository, TemplateSpec
from src.infra.multi_market_query import MultiMarketQuery, TieredSpec
from src.infra.market_query import MarketIndex


@dataclass(frozen=True)
class TemplateRun:
    template_key: str
    results: List[FlipResult]


@dataclass(frozen=True)
class CategoryRun:
    category_slug: str
    templates: List[TemplateRun]
    top_results: List[FlipResult]


@dataclass(frozen=True)
class CatalogReport:
    categories: List[CategoryRun]
    top_global: List[FlipResult]


class CatalogBMAnalyzer:
    """
    Escaneo completo:
      - obtiene categorías con templates desde SQLite
      - por cada categoría:
          * fetch único (MultiMarketQuery)
          * analiza cada template (BMFlippingAnalyzer.analyze_index sobre sub-índice)
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.template_repo = TemplateRepository(self.db_path)
        self._session = requests.Session()

    def list_categories_with_templates(self) -> List[str]:
        sql = """
        SELECT DISTINCT c.slug
          FROM categories c
          JOIN template_categories tc ON tc.category_id = c.id
          JOIN item_templates t ON t.id = tc.template_id
         WHERE t.is_active = 1
         ORDER BY c.slug
        """
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(sql).fetchall()
        return [r[0] for r in rows]

    def run(
        self,
        *,
        category_slugs: Optional[List[str]] = None,
        include_children: bool = False,
        top_n_per_template: int = 25,
        top_n_per_category: int = 100,
        top_n_global: int = 200,
        min_profit_net: int = 1,
        min_margin_net: float = 0.0,
    ) -> CatalogReport:
        slugs = category_slugs or self.list_categories_with_templates()

        category_runs: List[CategoryRun] = []
        global_results: List[FlipResult] = []

        for slug in slugs:
            specs = self.template_repo.list_for_category(slug, include_children=include_children)
            specs = self._dedupe_specs(specs)
            if not specs:
                continue

            # 1) Fetch único por categoría
            mq = MultiMarketQuery(
                specs=[TieredSpec(
                    template_key=s.template_key,
                    tier_min=s.tier_min,
                    tier_max=s.tier_max,
                    ench_min=s.ench_min,
                    ench_max=s.ench_max,
                ) for s in specs],
                session=self._session,
            )
            full_index = mq.fetch_index()

            # 2) Analiza cada template filtrando sub-índice
            template_runs: List[TemplateRun] = []
            cat_all: List[FlipResult] = []

            for s in specs:
                sub_index = self._subindex_for_spec(full_index, s)

                analyzer = BMFlippingAnalyzer(
                    base_item=s.template_key,
                    tier_min=s.tier_min,
                    tier_max=s.tier_max,
                    ench_min=s.ench_min,
                    ench_max=s.ench_max,
                )
                results = analyzer.analyze_index(
                    sub_index,
                    min_profit_net=min_profit_net,
                    min_margin_net=min_margin_net,
                    top_n=top_n_per_template,
                )

                template_runs.append(TemplateRun(template_key=s.template_key, results=results))
                cat_all.extend(results)

            # ranking categoría
            cat_all.sort(key=lambda r: (r.is_robust, r.profit_net, r.margin_net), reverse=True)
            top_cat = cat_all[:top_n_per_category] if top_n_per_category is not None else cat_all

            category_runs.append(CategoryRun(
                category_slug=slug,
                templates=template_runs,
                top_results=top_cat,
            ))

            global_results.extend(top_cat)

        # ranking global
        global_results.sort(key=lambda r: (r.is_robust, r.profit_net, r.margin_net), reverse=True)
        top_global = global_results[:top_n_global] if top_n_global is not None else global_results

        return CatalogReport(categories=category_runs, top_global=top_global)

    # ---------------- helpers ----------------

    @staticmethod
    def _dedupe_specs(specs: List[TemplateSpec]) -> List[TemplateSpec]:
        seen: Set[str] = set()
        out: List[TemplateSpec] = []
        for s in specs:
            key = s.template_key.strip().upper()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    @staticmethod
    def _build_item_ids_for_spec(s: TemplateSpec) -> Set[str]:
        base = s.template_key.strip().upper()
        ids: Set[str] = set()
        for t in range(int(s.tier_min), int(s.tier_max) + 1):
            core = f"T{t}_{base}"
            for e in range(int(s.ench_min), int(s.ench_max) + 1):
                ids.add(core if e == 0 else f"{core}@{e}")
        return ids

    def _subindex_for_spec(self, full_index: MarketIndex, s: TemplateSpec) -> MarketIndex:
        wanted = self._build_item_ids_for_spec(s)
        return {item_id: full_index[item_id] for item_id in wanted if item_id in full_index}
