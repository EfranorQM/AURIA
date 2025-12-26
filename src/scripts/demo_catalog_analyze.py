from __future__ import annotations

from pathlib import Path

from src.domain.catalog_bm_analyzer import CatalogBMAnalyzer


def get_db() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "auria.db"


def main():
    db = get_db()
    runner = CatalogBMAnalyzer(db)

    report = runner.run(
        include_children=False,
        top_n_per_template=10,
        top_n_per_category=50,
        top_n_global=100,
        min_profit_net=1,
        min_margin_net=0.0,
    )

    print("\n=== TOP GLOBAL ===\n")
    for r in report.top_global[:50]:
        print(
            r.item_id,
            "city=", r.origin_city,
            "q=", r.origin_quality,
            "bmQ=", r.bm_quality_used,
            "net8=", r.profit_net,
            f"({round(r.margin_net*100,2)}%)",
            "robust=", r.is_robust,
        )

    print("\n=== RESUMEN POR CATEGORÍA ===\n")
    for c in report.categories:
        print(f"[{c.category_slug}]  top={len(c.top_results)}  templates={len(c.templates)}")

if __name__ == "__main__":
    main()
