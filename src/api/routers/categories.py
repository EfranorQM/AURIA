from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import os
import yaml

router = APIRouter(tags=["catalog"])

# Rutas a tus YAML (ajústalas si están en otra carpeta)
CATEGORIES_YAML = os.getenv("CATEGORIES_YAML", "config/categories.yaml")
TEMPLATES_YAML = os.getenv("TEMPLATES_YAML", "config/templates.yaml")


# -------------------------
# Schemas (Pydantic)
# -------------------------
class CategoryItem(BaseModel):
    id: str
    name: str


class CategoryNode(BaseModel):
    name: str
    slug: str
    items: List[CategoryItem] = Field(default_factory=list)
    children: List["CategoryNode"] = Field(default_factory=list)


CategoryNode.model_rebuild()


class TemplateGroup(BaseModel):
    name: str
    mode: str
    tier_min: int
    tier_max: int
    ench_min: int
    ench_max: int
    qualities: List[int]
    categories: List[str]
    template_keys: List[str]


# -------------------------
# Loaders YAML
# -------------------------
def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_categories_tree() -> List[Dict[str, Any]]:
    data = _load_yaml(CATEGORIES_YAML)
    cats = data.get("categories", [])
    if not isinstance(cats, list):
        raise ValueError("categories.yaml: 'categories' must be a list")
    return cats


def load_template_groups() -> List[Dict[str, Any]]:
    data = _load_yaml(TEMPLATES_YAML)
    groups = data.get("template_groups", [])
    if not isinstance(groups, list):
        raise ValueError("templates.yaml: 'template_groups' must be a list")
    return groups


# -------------------------
# Helpers
# -------------------------
def find_category_node(tree: List[Dict[str, Any]], slug: str) -> Optional[Dict[str, Any]]:
    stack = list(tree)
    while stack:
        node = stack.pop()
        if node.get("slug") == slug:
            return node
        children = node.get("children") or []
        if isinstance(children, list):
            stack.extend(children)
    return None


def build_items_index_from_template_groups() -> Dict[str, List[Dict[str, str]]]:
    """
    Retorna:
      {
        "equipamiento/armas/hachas": [{"id":"MAIN_AXE","name":"MAIN_AXE"}, ...],
        ...
      }
    """
    groups = load_template_groups()

    idx: Dict[str, List[Dict[str, str]]] = {}
    for g in groups:
        cats = g.get("categories") or []
        keys = g.get("template_keys") or []
        if not isinstance(cats, list) or not isinstance(keys, list):
            continue

        items = [{"id": k, "name": k} for k in keys]  # name = id por ahora

        for cat_slug in cats:
            idx.setdefault(cat_slug, [])
            seen = {it["id"] for it in idx[cat_slug]}
            for it in items:
                if it["id"] not in seen:
                    idx[cat_slug].append(it)
                    seen.add(it["id"])
    return idx


def enrich_categories_with_items(
    tree: List[Dict[str, Any]],
    items_index: Dict[str, List[Dict[str, str]]],
) -> List[Dict[str, Any]]:
    def rec(node: Dict[str, Any]) -> Dict[str, Any]:
        slug = node.get("slug", "")
        node["items"] = items_index.get(slug, [])
        children = node.get("children") or []
        node["children"] = [rec(ch) for ch in children] if isinstance(children, list) else []
        return node

    return [rec(n) for n in tree]


# -------------------------
# Endpoints
# -------------------------
@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/categories", response_model=List[CategoryNode])
def get_categories():
    """
    Devuelve el árbol completo de categorías enriquecido con 'items'
    (los template_keys asociados por templates.yaml).
    """
    try:
        tree = load_categories_tree()
        items_index = build_items_index_from_template_groups()
        return enrich_categories_with_items(tree, items_index)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load categories: {e}")


@router.get("/categories/{slug:path}", response_model=CategoryNode)
def get_category(slug: str):
    """
    Devuelve un nodo (por slug) con sus hijos, enriquecido con 'items'.
    Ej: /categories/equipamiento/armas/hachas
    """
    try:
        tree = load_categories_tree()
        node = find_category_node(tree, slug)
        if not node:
            raise HTTPException(status_code=404, detail=f"Category not found: {slug}")

        items_index = build_items_index_from_template_groups()
        enriched = enrich_categories_with_items([node], items_index)
        return enriched[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {e}")


@router.get("/categories/{slug:path}/template-groups", response_model=List[TemplateGroup])
def get_template_groups_for_category(slug: str):
    """
    Devuelve los template_groups cuyo 'categories' incluye exactamente ese slug.
    Ej: /categories/equipamiento/armas/hachas/template-groups
    """
    try:
        groups = load_template_groups()
        matched = [g for g in groups if slug in (g.get("categories") or [])]
        return matched
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load template groups: {e}")
