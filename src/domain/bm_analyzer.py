from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

from src.infra.market_query import FastMarketQuery, MarketIndex, Quote


# Impuestos (según tu modelo)
TAX_NET = 0.08          # neto "principal" (conservador)
TAX_FLIP = 0.04         # vender directo (flipping)
TAX_ORDER = 0.065       # orden de venta


@dataclass(frozen=True)
class FlipResult:
    item_id: str
    origin_quality: int
    bm_quality_used: int
    origin_city: str

    origin_price: int
    origin_price_source: str      # "sell_max" | "sell_min"
    bm_price: int
    bm_price_source: str          # "buy_max" | "buy_min"

    # NETO principal (8%)
    profit_net: int
    margin_net: float

    # Alternativas
    profit_flip: int              # 4%
    margin_flip: float
    profit_order: int             # 6.5%
    margin_order: float

    is_robust: bool               # True si la ganancia existe usando sell_max


class BMFlippingAnalyzer:
    BM_CITY = "Black Market"

    def __init__(
        self,
        base_item: str,
        tier_min: int = 4,
        tier_max: int = 8,
        ench_min: int = 0,
        ench_max: int = 4,
    ) -> None:
        self.q = FastMarketQuery(
            base_item=base_item,
            tier_min=tier_min,
            tier_max=tier_max,
            ench_min=ench_min,
            ench_max=ench_max,
        )

    def run(
        self,
        min_profit_net: int = 1,
        min_margin_net: float = 0.0,
        top_n: Optional[int] = None,
    ) -> List[FlipResult]:
        index = self.q.fetch_index()
        return self.analyze_index(
            index,
            min_profit_net=min_profit_net,
            min_margin_net=min_margin_net,
            top_n=top_n,
        )

    # ---------------- Internal ----------------

    def _compute(self, index: MarketIndex) -> List[FlipResult]:
        out: List[FlipResult] = []

        for item_id, city_map in index.items():
            bm_qmap = city_map.get(self.BM_CITY)
            if not bm_qmap:
                continue

            # BM revenue por calidad + fuente
            bm_rev_by_q: Dict[int, Tuple[int, str]] = {}
            for q_bm, quote_bm in bm_qmap.items():
                rev, src = self._bm_revenue_with_source(quote_bm)
                if rev > 0:
                    bm_rev_by_q[q_bm] = (rev, src)

            if not bm_rev_by_q:
                continue

            for origin_city, qmap in city_map.items():
                if origin_city == self.BM_CITY:
                    continue

                for origin_quality, quote_origin in qmap.items():
                    robust_cost, robust_src = self._origin_cost_robust(quote_origin)
                    opportunistic_cost, opp_src = self._origin_cost_opportunistic(quote_origin)

                    if robust_cost <= 0 and opportunistic_cost <= 0:
                        continue

                    bm_choice = self._best_bm_revenue_for_origin_quality(bm_rev_by_q, origin_quality)
                    if bm_choice is None:
                        continue

                    bm_quality_used, (revenue, bm_src) = bm_choice
                    if revenue <= 0:
                        continue

                    # Para resultados “relevantes”: prioriza costo robusto (sell_max) si existe
                    cost, cost_src = self._choose_cost_for_output(robust_cost, robust_src, opportunistic_cost, opp_src)
                    if cost <= 0:
                        continue

                    gross_profit = revenue - cost
                    if gross_profit <= 0:
                        continue

                    # is_robust: si hay sell_max y con sell_max también hay profit
                    robust_profit = -1
                    if robust_cost > 0:
                        net_rev_robust = int(round(revenue * (1.0 - TAX_FLIP)))
                        robust_profit = net_rev_robust - robust_cost

                    is_robust = (robust_src == "sell_max") and (robust_profit > 0)


                    # Netos (tu modelo: “aplicar impuesto al profit”)
                    profit_net, margin_net = self._apply_tax_on_revenue(revenue, cost, TAX_NET)
                    profit_flip, margin_flip = self._apply_tax_on_revenue(revenue, cost, TAX_FLIP)
                    profit_order, margin_order = self._apply_tax_on_revenue(revenue, cost, TAX_ORDER)

                    out.append(FlipResult(
                        item_id=item_id,
                        origin_quality=origin_quality,
                        bm_quality_used=bm_quality_used,
                        origin_city=origin_city,

                        origin_price=cost,
                        origin_price_source=cost_src,
                        bm_price=revenue,
                        bm_price_source=bm_src,

                        profit_net=profit_net,
                        margin_net=margin_net,

                        profit_flip=profit_flip,
                        margin_flip=margin_flip,
                        profit_order=profit_order,
                        margin_order=margin_order,

                        is_robust=is_robust,
                    ))

        return out

    # ---------- tax helper ----------

    @staticmethod
    def _apply_tax_on_revenue(revenue: int, cost: int, tax_rate: float) -> Tuple[int, float]:
        """
        Impuesto aplicado al REVENUE (precio de venta), que es como funciona BM/mercados.
        net_revenue = revenue * (1 - tax)
        profit = net_revenue - cost
        margin = profit / cost
        """
        net_revenue = int(round(revenue * (1.0 - tax_rate)))
        profit = net_revenue - cost
        margin = (profit / cost) if cost > 0 else 0.0
        return profit, margin



    # ---------- price selectors ----------

    @staticmethod
    def _origin_cost_robust(q: Quote) -> Tuple[int, str]:
        # Robusto: prioriza sell_max (más representativo)
        if q.sell_max > 0:
            return q.sell_max, "sell_max"
        if q.sell_min > 0:
            return q.sell_min, "sell_min"
        return 0, "sell_min"

    @staticmethod
    def _origin_cost_opportunistic(q: Quote) -> Tuple[int, str]:
        # Oportunista: prioriza sell_min (best case)
        if q.sell_min > 0:
            return q.sell_min, "sell_min"
        if q.sell_max > 0:
            return q.sell_max, "sell_max"
        return 0, "sell_min"

    @staticmethod
    def _bm_revenue_with_source(q: Quote) -> Tuple[int, str]:
        # Ingreso BM: preferir buy_max; si no, buy_min
        if q.buy_max > 0:
            return q.buy_max, "buy_max"
        if q.buy_min > 0:
            return q.buy_min, "buy_min"
        return 0, "buy_max"

    @staticmethod
    def _choose_cost_for_output(
        robust_cost: int, robust_src: str,
        opp_cost: int, opp_src: str
    ) -> Tuple[int, str]:
        # Para output, usa robust si existe; si no, oportunista
        if robust_cost > 0:
            return robust_cost, robust_src
        return opp_cost, opp_src

    # ---------- BM quality selection ----------

    @staticmethod
    def _best_bm_revenue_for_origin_quality(
        bm_rev_by_q: Dict[int, Tuple[int, str]],
        origin_quality: int
    ) -> Optional[Tuple[int, Tuple[int, str]]]:
        """
        Elige el mejor revenue en BM entre calidades <= origin_quality.
        Empate: prefiere mayor calidad.
        """
        best_q: Optional[int] = None
        best_rev: int = 0
        best_src: str = "buy_max"

        for q_bm, (rev, src) in bm_rev_by_q.items():
            if q_bm > origin_quality:
                continue
            if best_q is None or rev > best_rev or (rev == best_rev and q_bm > best_q):
                best_q = q_bm
                best_rev = rev
                best_src = src

        if best_q is None:
            return None
        return best_q, (best_rev, best_src)

    def analyze_index(
            self,
            index: MarketIndex,
            *,
            min_profit_net: int = 1,
            min_margin_net: float = 0.0,
            top_n: Optional[int] = None,
        ) -> List[FlipResult]:
            """
            Igual que run(), pero reutiliza un MarketIndex ya descargado.
            Ideal para análisis masivo por categoría/catálogo.
            """
            results = self._compute(index)

            # Filtra usando el neto principal (8%) para ser conservador
            results = [
                r for r in results
                if r.profit_net >= min_profit_net and r.margin_net >= min_margin_net
            ]

            # Ranking: robustos arriba, luego profit_net, luego margin_net
            results.sort(key=lambda x: (x.is_robust, x.profit_net, x.margin_net), reverse=True)

            return results[:top_n] if top_n is not None else results