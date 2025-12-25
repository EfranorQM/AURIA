from pathlib import Path
from src.infra.catalog_repo import CatalogRepository

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "auria.db"

def main():
    repo = CatalogRepository(DB_PATH)

    slug = "equipment/weapons/axes"
    item_ids = repo.get_item_ids_for_category(slug, include_children=True)
    qualities = repo.get_qualities_for_category(slug, include_children=True)

    print(f"\nCategoría: {slug}")
    print(f"Qualities: {qualities}")
    print(f"Total item_ids: {len(item_ids)}\n")

    # imprime solo los primeros 40 para no spamear consola
    for x in item_ids[:40]:
        print(x)

    if len(item_ids) > 40:
        print(f"... ({len(item_ids) - 40} más)")

if __name__ == "__main__":
    main()
