from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import requests


@dataclass(frozen=True)
class Quote:
    sell_min: int
    sell_max: int
    buy_min: int
    buy_max: int
    sell_min_date: str
    sell_max_date: str
    buy_min_date: str
    buy_max_date: str


MarketIndex = Dict[str, Dict[str, Dict[int, Quote]]]
#            item_id -> city -> quality -> Quote


class FastMarketQuery:
    """
    Consulta precios a Albion Online Data Project para:
      - un item base (p.ej. "2H_AXE")
      - un rango de tiers (p.ej. 4..8)
      - un rango de encantamientos (p.ej. 0..4) donde 0 = sin @

    Devuelve un índice rápido:
      index[item_id][city][quality] -> Quote(...)
    """

    DEFAULT_CITIES = [
        "Bridgewatch",
        "Martlock",
        "Fort Sterling",
        "Lymhurst",
        "Thetford",
        "Caerleon",
        "Brecilien",
        "Black Market",
    ]

    DEFAULT_QUALITIES = [1, 2, 3, 4, 5]

    BASE_URL = "https://www.albion-online-data.com/api/v2/stats/prices"

    def __init__(
        self,
        base_item: str,
        tier_min: int = 4,
        tier_max: int = 8,
        ench_min: int = 0,
        ench_max: int = 4,
        cities: Optional[List[str]] = None,
        timeout_sec: int = 30,
        batch_size: int = 120,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_item = base_item.strip().upper()
        self.tier_min = int(tier_min)
        self.tier_max = int(tier_max)
        self.ench_min = int(ench_min)
        self.ench_max = int(ench_max)
        self.cities = cities or self.DEFAULT_CITIES
        self.timeout_sec = timeout_sec
        self.batch_size = batch_size
        self.session = session or requests.Session()

        if self.tier_min > self.tier_max:
            raise ValueError("tier_min > tier_max")
        if self.ench_min > self.ench_max:
            raise ValueError("ench_min > ench_max")
        if self.ench_min < 0:
            raise ValueError("ench_min no puede ser < 0")
        if self.ench_max > 4:
            raise ValueError("ench_max > 4 no es válido en Albion (usa 0..4)")
        if self.tier_min < 1 or self.tier_max > 8:
            raise ValueError("tiers fuera de rango (1..8)")

    # ---------------- Public ----------------

    def build_item_ids(self) -> List[str]:
        ids: List[str] = []
        for t in range(self.tier_min, self.tier_max + 1):
            core = f"T{t}_{self.base_item}"
            for e in range(self.ench_min, self.ench_max + 1):
                ids.append(core if e == 0 else f"{core}@{e}")
        return ids

    def build_urls(self) -> List[str]:
        item_ids = self.build_item_ids()
        return [self._build_url(chunk) for chunk in self._chunks(item_ids, self.batch_size)]

    def fetch_index(self) -> MarketIndex:
        index: MarketIndex = {}

        for url in self.build_urls():
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

                # NUEVA CONDICIÓN: elimina solo si los 4 están en 0
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

    # ---------------- Internal ----------------

    def _build_url(self, item_ids: List[str]) -> str:
        items_str = ",".join(item_ids)
        loc_str = ",".join(self._encode_location(x) for x in self.cities)
        qual_str = ",".join(map(str, self.DEFAULT_QUALITIES))
        return f"{self.BASE_URL}/{items_str}.json?locations={loc_str}&qualities={qual_str}"

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
