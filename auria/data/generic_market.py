from __future__ import annotations

"""generic_market.py  – ahora con soporte de encantamientos (@1, @2, @3)"""

import re
from typing import List, Tuple, Optional
import requests

Row = Tuple[str, str, int, int, int]   # (item_id, city, quality, sell, buy)


class GenericMarketSource:
    """Descarga matrices de precios desde la API Albion‑Online‑Data.

    Soporta:
    ─ Tiers   (T1‑T8)
    ─ Qualities (1‑8)
    ─ *NUEVO* Encantamientos 0‑3 ("@1", "@2", "@3").

    Cómo genera los IDs completos:
      • Para cada base_item_id aplica tiers y encantamientos.
      • Si el id ya contiene "@n" se respeta tal cual.
      • Si pasas "*ID_COMPLETO" (asterisco) también se usa tal cual.
      • Soporta rango [T4‑T8]BASE igual que antes.
    """

    BASE_URL       = "https://www.albion-online-data.com/api/v2/stats/prices"
    DEFAULT_CITIES = [
        "Bridgewatch", "Martlock", "Fort Sterling",
        "Lymhurst", "Thetford", "Caerleon", "Black Market", 
    ]
    DEFAULT_TIERS   = list(range(1, 9))   # 1‑8
    DEFAULT_QUALS   = list(range(1, 9))   # 1‑8
    DEFAULT_ENCHS   = [0, 1, 2, 3]        # 0 = sin encantamiento

    _RANGE_RE = re.compile(r"\[T(?P<start>\d)(?:-T?(?P<end>\d))?]\s*(?P<base>.+)", re.I)

    def __init__(
        self,
        base_item_ids: List[str],
        cities: Optional[List[str]]        = None,
        qualities: Optional[List[int]]    = None,
        tiers: Optional[List[int]]        = None,
        enchantments: Optional[List[int]] = None,   # nuevo
    ) -> None:
        self.base_item_ids = base_item_ids
        self.cities        = cities        or self.DEFAULT_CITIES
        self.qualities     = qualities     or self.DEFAULT_QUALS
        self.tiers         = tiers         or self.DEFAULT_TIERS
        self.enchantments  = enchantments  or self.DEFAULT_ENCHS

    # ---------------- PUBLIC ----------------
    def get_url(self) -> str:
        item_ids      = self._expand_all_ids()
        items_str     = ",".join(item_ids)
        cities_str    = ",".join(self.cities)
        qualities_str = ",".join(map(str, self.qualities))
        return (
            f"{self.BASE_URL}/{items_str}.json"
            f"?locations={cities_str}&qualities={qualities_str}"
        )

    def get_filtered_matrix(self) -> List[Row]:
        data   = requests.get(self.get_url()).json()
        matrix: List[Row] = []
        for e in data:
            sell, buy = e.get("sell_price_min", 0), e.get("buy_price_max", 0)
            if sell > 0 or buy > 0:
                matrix.append((
                    e["item_id"],
                    e.get("city", e.get("location")),
                    e["quality"],
                    sell,
                    buy,
                ))
        return matrix

    # ---------------- INTERNAL ----------------
    def _expand_all_ids(self) -> List[str]:
        expanded: List[str] = []
        for raw in self.base_item_ids:
            expanded.extend(self._expand_single_id(raw.strip()))
        return expanded

    def _expand_single_id(self, raw: str) -> List[str]:
        raw_up = raw.upper()

        # A) *ID_COMPLETO  (tal cual, puede traer @)
        if raw_up.startswith("*"):
            return [raw_up[1:]]

        # B) Si contiene '@' ya es un ID completo con encantamiento
        if "@" in raw_up:
            return [raw_up]

        # C) Rango [T4-T8]BASE o [T5]BASE
        m = self._RANGE_RE.match(raw_up)
        if m:
            start = int(m.group("start"))
            end   = int(m.group("end") or start)
            base  = m.group("base")
            core  = [f"T{t}_{base}" for t in range(start, end + 1)]
            return self._apply_enchants(core)

        # D) Ya empieza con "T#_" → ID base sin encantamientos
        if raw_up.startswith("T") and "_" in raw_up:
            return self._apply_enchants([raw_up])

        # E) Nombre base → aplica tiers por defecto
        core = [f"T{t}_{raw_up}" for t in self.tiers]
        return self._apply_enchants(core)

    # Helper: genera @n para cada id base
    def _apply_enchants(self, core_ids: List[str]) -> List[str]:
        res: List[str] = []
        for cid in core_ids:
            for ench in self.enchantments:
                if ench == 0:
                    res.append(cid)          # sin sufijo
                else:
                    res.append(f"{cid}@{ench}")
        return res


# ----------------- DEMO -----------------
if __name__ == "__main__":
    ids = ["[T4-T5]2H_KNUCKLES_KEEPER", "T6_MOUNT_OX", "*UNIQUE_MOUNT_JUGGERNAUT_GOLD"]
    src = GenericMarketSource(ids, cities=["Caerleon"], qualities=[1,2])
    print("\nURL generado:")
    print(src.get_url())
