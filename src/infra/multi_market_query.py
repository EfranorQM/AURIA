from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set
import requests

from src.infra.market_query import MarketIndex, Quote, FastMarketQuery


@dataclass(frozen=True)
class TieredSpec:
    template_key: str
    tier_min: int
    tier_max: int
    ench_min: int
    ench_max: int


class MultiMarketQuery:
    """
    Descarga precios para MUCHOS templates en una sola (o pocas) consultas,
    construyendo un MarketIndex global.

    La idea:
      - unir todos los item_ids de la categoría
      - pedirlos en batches (para no explotar la URL)
      - devolver MarketIndex[item_id][city][quality] -> Quote(...)
    """

    def __init__(
        self,
        specs: List[TieredSpec],
        *,
        cities: Optional[List[str]] = None,
        qualities: Optional[List[int]] = None,
        batch_size: int = 120,
        timeout_sec: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.specs = specs
        self.cities = cities or FastMarketQuery.DEFAULT_CITIES
        self.qualities = qualities or FastMarketQuery.DEFAULT_QUALITIES
        self.batch_size = int(batch_size)
        self.timeout_sec = int(timeout_sec)
        self.session = session or requests.Session()

    def build_item_ids(self) -> List[str]:
        ids: Set[str] = set()
        for s in self.specs:
            ids.update(self._build_item_ids_for_spec(s))
        # Orden estable solo para debug/consistencia
        return sorted(ids)

    def fetch_index(self) -> MarketIndex:
        index: MarketIndex = {}

        item_ids = self.build_item_ids()
        for chunk in self._chunks(item_ids, self.batch_size):
            url = self._build_url(chunk)
            data = self._get_json(url)
            if not isinstance(data, list):
                continue

            for e in data:
                item_id = e.get("item_id")
                city = e.get("city") or e.get("location")
                quality = e.get("quality")

                if not item_id or not city or quality is None:
                    continue

                try:
                    q_int = int(quality)
                except Exception:
                    continue

                sell_min = int(e.get("sell_price_min", 0) or 0)
                sell_max = int(e.get("sell_price_max", 0) or 0)
                buy_min  = int(e.get("buy_price_min", 0) or 0)
                buy_max  = int(e.get("buy_price_max", 0) or 0)

                if sell_min == 0 and sell_max == 0 and buy_min == 0 and buy_max == 0:
                    continue

                quote = Quote(
                    sell_min=sell_min,
                    sell_max=sell_max,
                    buy_min=buy_min,
                    buy_max=buy_max,
                    sell_min_date=e.get("sell_price_min_date", ""),
                    sell_max_date=e.get("sell_price_max_date", ""),
                    buy_min_date=e.get("buy_price_min_date", ""),
                    buy_max_date=e.get("buy_price_max_date", ""),
                )

                index.setdefault(item_id, {}).setdefault(city, {})[q_int] = quote

        return index

    # ---------------- internal ----------------

    @staticmethod
    def _build_item_ids_for_spec(s: TieredSpec) -> List[str]:
        base = s.template_key.strip().upper()
        ids: List[str] = []
        for t in range(int(s.tier_min), int(s.tier_max) + 1):
            core = f"T{t}_{base}"
            for e in range(int(s.ench_min), int(s.ench_max) + 1):
                ids.append(core if e == 0 else f"{core}@{e}")
        return ids

    def _build_url(self, item_ids: List[str]) -> str:
        items_str = ",".join(item_ids)
        loc_str = ",".join(self._encode_location(x) for x in self.cities)
        qual_str = ",".join(map(str, self.qualities))
        return f"{FastMarketQuery.BASE_URL}/{items_str}.json?locations={loc_str}&qualities={qual_str}"

    def _get_json(self, url: str):
        r = self.session.get(url, timeout=self.timeout_sec)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _encode_location(s: str) -> str:
        return s.strip().replace(" ", "%20")

    @staticmethod
    def _chunks(items: List[str], n: int):
        for i in range(0, len(items), n):
            yield items[i : i + n]
