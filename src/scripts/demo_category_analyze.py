from __future__ import annotations

import sys
from pathlib import Path

from src.domain.category_bm_analyzer import CategoryBMAnalyzer

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "auria.db"


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m src.scripts.demo_category_analyze equipment/weapons/axes")
        raise SystemExit(2)

    category_slug = sys.argv[1].strip()

    runner = CategoryBMAnalyzer(DB_PATH)
    report = runner.run(
        category_slug,
        include_children=False,
        top_n_per_template=25,
        top_n_total=100,
        min_profit_net=1,
        min_margin_net=0.0,
    )

    if not report.groups:
        print("No se encontraron templates para:", category_slug)
        return

    print("\n=== RESULTADOS POR TEMPLATE ===")
    for g in report.groups:
        print(f"\n[{g.template_key}] ({len(g.results)} resultados)")
        for r in g.results[:10]:  # imprime top 10 por template
            print(
                r.item_id,
                "originQ=", r.origin_quality,
                "bmQ=", r.bm_quality_used,
                "city=", r.origin_city,
                "cost=", r.origin_price, f"({r.origin_price_source})",
                "bm=", r.bm_price, f"({r.bm_price_source})",
                "net8=", r.profit_net, f"({round(r.margin_net*100, 2)}%)",
                "flip4=", r.profit_flip, f"({round(r.margin_flip*100, 2)}%)",
                "order6.5=", r.profit_order, f"({round(r.margin_order*100, 2)}%)",
                "robust=", r.is_robust,
            )

    print("\n=== TOP GLOBAL CATEGORÍA ===")
    for r in report.all_results[:25]:
        print(
            r.item_id,
            "originQ=", r.origin_quality,
            "bmQ=", r.bm_quality_used,
            "city=", r.origin_city,
            "cost=", r.origin_price, f"({r.origin_price_source})",
            "bm=", r.bm_price, f"({r.bm_price_source})",
            "net8=", r.profit_net, f"({round(r.margin_net*100, 2)}%)",
            "flip4=", r.profit_flip, f"({round(r.margin_flip*100, 2)}%)",
            "order6.5=", r.profit_order, f"({round(r.margin_order*100, 2)}%)",
            "robust=", r.is_robust,
        )


if __name__ == "__main__":
    main()
