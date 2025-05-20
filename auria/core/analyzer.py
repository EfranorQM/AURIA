from collections import defaultdict
from typing import List, Tuple, Dict, Optional

# Tipo de fila de entrada y salida
ItemIn = Tuple[str, str, int, int, int]   # (item, city, tier, sell, buy)
ItemOut = Tuple[str, int, str, int, str, int, float]  # (item, tier, city_from, sell, city_to, buy, pct)

class ArbitrageAnalyzer:
    def __init__(self, matrix: List[ItemIn]) -> None:
        """Inicializa el analizador con la matriz de datos."""
        self.matrix = matrix

    def best_trades(
        self,
        city_from_filter: Optional[str] = None,
        city_to_filter: Optional[str] = None
    ) -> List[ItemOut]:
        """
        Retorna todas las rutas de arbitraje ordenadas por margen desc.

        Parámetros opcionales:
        - city_from_filter: si se pasa, solo considera rutas desde esa ciudad.
        - city_to_filter: si se pasa, solo considera rutas hacia esa ciudad.
        """
        # 1) Construir cache de mejores precios por (item, tier, city)
        cache: Dict[Tuple[str, int, str], Dict[str, int]] = {}
        for item, city, tier, sell, buy in self.matrix:
            key = (item, tier, city)
            rec = cache.setdefault(key, {"sell": float('inf'), "buy": 0})
            # Sell = precio mínimo al comprar
            if 0 < sell < rec["sell"]:
                rec["sell"] = sell
            # Buy = precio máximo al vender
            if buy > rec["buy"]:
                rec["buy"] = buy

        # 2) Agrupar por (item, tier)
        grouped: Dict[Tuple[str, int], List[Tuple[str, int, int]]] = defaultdict(list)
        for (item, tier, city), prices in cache.items():
            grouped[(item, tier)].append((city, prices["sell"], prices["buy"]))

        # 3) Generar rutas comparando todas las ciudades entre sí
        routes: List[ItemOut] = []
        for (item, tier), city_data in grouped.items():
            for city_from, sell_price, _ in city_data:
                for city_to, _, buy_price in city_data:
                    if city_from == city_to:
                        continue
                    # Filtros de sell/buy
                    if sell_price == float('inf') or buy_price <= sell_price:
                        continue
                    # Filtro opcional por ciudades
                    if city_from_filter and city_from != city_from_filter:
                        continue
                    if city_to_filter and city_to != city_to_filter:
                        continue
                    pct = round((buy_price - sell_price) / sell_price * 100, 2)
                    routes.append((item, tier, city_from, sell_price, city_to, buy_price, pct))

        # Ordenar descendente por porcentaje de margen
        routes.sort(key=lambda x: x[6], reverse=True)
        return routes

    def top_trade(
        self,
        city_from_filter: Optional[str] = None,
        city_to_filter: Optional[str] = None
    ) -> Optional[ItemOut]:
        """Retorna la ruta con mayor margen según filtros opcionales."""
        trades = self.best_trades(city_from_filter, city_to_filter)
        return trades[0] if trades else None
