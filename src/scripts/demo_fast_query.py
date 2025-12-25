from src.infra.market_query import FastMarketQuery

def main():
    q = FastMarketQuery(
        base_item="2H_AXE",
        tier_min=4,
        tier_max=8,
        ench_min=0,
        ench_max=4,
    )

    print("Ejemplo URL (primer batch):")
    print(q.build_urls()[0])

    idx = q.fetch_index()
    print(f"\nitems con señal: {idx}")

    # ejemplo: leer un valor puntual en O(1)
    sample_item = "T8_2H_AXE@1"
    if sample_item in idx and "Black Market" in idx[sample_item] and 2 in idx[sample_item]["Black Market"]:
        quote = idx[sample_item]["Black Market"][2]
        print("\nSample:", sample_item, "BM quality=2 ->", quote)

if __name__ == "__main__":
    main()
