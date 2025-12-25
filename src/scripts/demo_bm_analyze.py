from src.domain.bm_analyzer import BMFlippingAnalyzer

def main():
    analyzer = BMFlippingAnalyzer(
        base_item="2H_AXE",
        tier_min=4, tier_max=8,
        ench_min=0, ench_max=4
    )

    results = analyzer.run(
        min_profit_net=1,
        min_margin_net=0.0,
        top_n=25
    )

    for r in results:
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
            "robust=", r.is_robust
        )

if __name__ == "__main__":
    main()
