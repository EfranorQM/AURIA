PRAGMA foreign_keys = ON;

-- =========================
-- CATEGORIES (árbol)
-- =========================
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  parent_id INTEGER,
  FOREIGN KEY(parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- =========================
-- ITEM TEMPLATES (catálogo por patrones)
-- =========================
CREATE TABLE IF NOT EXISTS item_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_key TEXT NOT NULL UNIQUE,  -- ej: MAIN_AXE o UNIQUE_MOUNT_...
  mode TEXT NOT NULL DEFAULT 'TIERED' CHECK (mode IN ('TIERED','EXACT')),
  tier_min INTEGER,                  -- usado si mode=TIERED
  tier_max INTEGER,
  ench_min INTEGER NOT NULL DEFAULT 0,
  ench_max INTEGER NOT NULL DEFAULT 0,
  qualities TEXT NOT NULL DEFAULT '1,2,3,4,5', -- CSV: "1,2,3,4,5"
  is_active INTEGER NOT NULL DEFAULT 1,
  notes TEXT
);

-- =========================
-- RELACIÓN TEMPLATE <-> CATEGORÍA (muchos-a-muchos)
-- =========================
CREATE TABLE IF NOT EXISTS template_categories (
  template_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  PRIMARY KEY (template_id, category_id),
  FOREIGN KEY(template_id) REFERENCES item_templates(id) ON DELETE CASCADE,
  FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Opcional: watchlist por template (útil)
CREATE TABLE IF NOT EXISTS watchlist_templates (
  template_id INTEGER PRIMARY KEY,
  note TEXT,
  priority INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(template_id) REFERENCES item_templates(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_templates_active ON item_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_template_categories_category ON template_categories(category_id, template_id);
