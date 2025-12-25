from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

from src.domain.bm_analyzer import BMFlippingAnalyzer
from src.infra.template_repo import TemplateRepository


# ------------------------- DB helpers -------------------------

def get_root_and_db() -> Path:
    root = Path(__file__).resolve().parents[1]  # AURIA/
    return root / "data" / "auria.db"


def list_category_slugs(db_path: Path) -> list[str]:
    try:
        with sqlite3.connect(db_path) as con:
            rows = con.execute("SELECT slug FROM categories ORDER BY slug").fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def albiononline2d_link(item_id: str) -> str:
    return f"https://albiononline2d.com/es/item/id/{item_id}"


# ------------------------- UI helpers (CSS + cards) -------------------------

def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
        h1, h2, h3 { letter-spacing: -0.02em; }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .18rem .55rem;
            border-radius: 999px;
            font-size: .78rem;
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.04);
            white-space: nowrap;
        }
        .chip-strong { background: rgba(56, 189, 248, .12); border-color: rgba(56, 189, 248, .25); }
        .chip-warn   { background: rgba(251, 191, 36, .12); border-color: rgba(251, 191, 36, .25); }
        .chip-good   { background: rgba(34, 197, 94, .12); border-color: rgba(34, 197, 94, .25); }
        .chip-bad    { background: rgba(239, 68, 68, .12); border-color: rgba(239, 68, 68, .25); }

        .card {
            border-radius: 18px;
            padding: 14px 14px 12px 14px;
            border: 1px solid rgba(255,255,255,.10);
            background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
            box-shadow: 0 8px 24px rgba(0,0,0,.25);
            margin-bottom: 12px;
        }
        .card:hover { border-color: rgba(255,255,255,.18); transform: translateY(-1px); transition: all .12s ease; }
        .card-title {
            font-weight: 650;
            font-size: 1.02rem;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }
        .card-title a { text-decoration: none; }
        .subline { color: rgba(255,255,255,.72); font-size: .85rem; margin-bottom: 10px; }

        .metric-row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-top: 8px;
        }
        .metric {
            border-radius: 14px;
            padding: 10px;
            border: 1px solid rgba(255,255,255,.08);
            background: rgba(255,255,255,.03);
        }
        .metric .k { color: rgba(255,255,255,.65); font-size: .78rem; }
        .metric .v { font-size: 1.05rem; font-weight: 700; margin-top: 2px; }

        [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,.10); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_int(n: int) -> str:
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)


def fmt_pct(x: float) -> str:
    try:
        return f"{float(x):.2f}%"
    except Exception:
        return str(x)


def chip(text: str, kind: str = "chip") -> str:
    cls = "chip"
    if kind == "strong":
        cls += " chip-strong"
    elif kind == "warn":
        cls += " chip-warn"
    elif kind == "good":
        cls += " chip-good"
    elif kind == "bad":
        cls += " chip-bad"
    return f'<span class="{cls}">{text}</span>'


def render_cards(df: pd.DataFrame, *, n: int = 12, cols_per_row: int = 2):
    if df.empty:
        st.info("Sin resultados con los filtros actuales.")
        return

    view = df.head(n).copy()
    cols = st.columns(cols_per_row, gap="large")

    for i, row in enumerate(view.to_dict(orient="records")):
        c = cols[i % cols_per_row]

        item_url = row.get("item_url", "")
        item_id_text = item_url.split("/")[-1] if item_url else str(row.get("item_id", "ITEM"))

        origin_city = str(row.get("origin_city", "?"))
        template_key = str(row.get("template_key", "?"))
        oq = row.get("origin_quality", "?")
        bq = row.get("bm_quality_used", "?")

        cost = int(row.get("origin_price", 0) or 0)
        bm = int(row.get("bm_price", 0) or 0)

        p_net = int(row.get("profit_net", 0) or 0)
        m_net = float(row.get("margin_net_pct", 0.0) or 0.0)
        p_flip = int(row.get("profit_flip", 0) or 0)
        m_flip = float(row.get("margin_flip_pct", 0.0) or 0.0)
        p_order = int(row.get("profit_order", 0) or 0)
        m_order = float(row.get("margin_order_pct", 0.0) or 0.0)

        robust = bool(row.get("is_robust", False))
        cost_src = str(row.get("origin_price_source", ""))
        bm_src = str(row.get("bm_price_source", ""))

        robust_badge = chip("ROBUST", "good") if robust else chip("NON-ROBUST", "warn")
        src_badge = chip(f"cost:{cost_src}", "strong") + " " + chip(f"bm:{bm_src}", "strong")
        q_badge = chip(f"Q{oq}→BM Q{bq}", "warn")
        profit_badge = chip(f"net8 +{fmt_int(p_net)}", "good" if p_net > 0 else "bad")

        with c:
            st.markdown(
                f"""
                <div class="card">
                  <div class="card-title">
                    <a href="{item_url}" target="_blank" rel="noopener noreferrer">{item_id_text}</a>
                    {profit_badge}
                  </div>

                  <div class="subline">
                    {chip(template_key, "strong")} {chip(origin_city, "warn")} {q_badge}
                  </div>

                  <div class="subline">
                    {robust_badge} {src_badge}
                  </div>

                  <div class="metric-row">
                    <div class="metric">
                      <div class="k">Costo</div>
                      <div class="v">{fmt_int(cost)}</div>
                    </div>
                    <div class="metric">
                      <div class="k">BM</div>
                      <div class="v">{fmt_int(bm)}</div>
                    </div>
                    <div class="metric">
                      <div class="k">net8 %</div>
                      <div class="v">{fmt_pct(m_net)}</div>
                    </div>
                  </div>

                  <div class="metric-row" style="margin-top:10px;">
                    <div class="metric">
                      <div class="k">flip4</div>
                      <div class="v">+{fmt_int(p_flip)} <span style="color:rgba(255,255,255,.7); font-weight:600;">({fmt_pct(m_flip)})</span></div>
                    </div>
                    <div class="metric">
                      <div class="k">order6.5</div>
                      <div class="v">+{fmt_int(p_order)} <span style="color:rgba(255,255,255,.7); font-weight:600;">({fmt_pct(m_order)})</span></div>
                    </div>
                    <div class="metric">
                      <div class="k">net8</div>
                      <div class="v">+{fmt_int(p_net)}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_category_section(slug: str, df: pd.DataFrame, *, top_cards: int, top_table: int, col_cfg: dict):
    if df.empty:
        return

    best_net = int(df["profit_net"].max()) if "profit_net" in df.columns else 0
    best_flip = int(df["profit_flip"].max()) if "profit_flip" in df.columns else 0
    best_order = int(df["profit_order"].max()) if "profit_order" in df.columns else 0
    cnt = len(df)

    st.markdown(
        f"""
        <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:14px; margin-bottom: 10px;">
          <div>
            <div style="font-size:1.15rem; font-weight:750;">{slug}</div>
            <div style="color:rgba(255,255,255,.65); font-size:.9rem;">{cnt} oportunidades post-filtro</div>
          </div>
          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            {chip("Best net8 +" + fmt_int(best_net), "good")}
            {chip("Best flip4 +" + fmt_int(best_flip), "strong")}
            {chip("Best order6.5 +" + fmt_int(best_order), "strong")}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_cards(df, n=top_cards, cols_per_row=2)

    show_table = st.checkbox(f"Mostrar tabla técnica ({slug})", value=False, key=f"show_table_{slug}")
    if show_table:
        st.dataframe(
            df.head(top_table),
            use_container_width=True,
            hide_index=True,
            column_config=col_cfg,
        )


# ------------------------- Analysis -------------------------

@st.cache_data(ttl=60)
def analyze_template_cached(
    base_item: str,
    tier_min: int,
    tier_max: int,
    ench_min: int,
    ench_max: int,
    min_profit_net: int,
    min_margin_net: float,
    top_n: int,
) -> list[dict]:
    analyzer = BMFlippingAnalyzer(
        base_item=base_item,
        tier_min=tier_min, tier_max=tier_max,
        ench_min=ench_min, ench_max=ench_max,
    )
    results = analyzer.run(
        min_profit_net=min_profit_net,
        min_margin_net=min_margin_net,
        top_n=top_n,
    )
    return [asdict(r) for r in results]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df["item_url"] = df["item_id"].map(albiononline2d_link)

    for col in ["margin_net", "margin_flip", "margin_order"]:
        if col in df.columns:
            df[col + "_pct"] = (df[col].astype(float) * 100.0)

    ordered = [
        "item_url",
        "template_key",
        "origin_city",
        "origin_quality",
        "bm_quality_used",
        "origin_price",
        "origin_price_source",
        "bm_price",
        "bm_price_source",
        "profit_net",
        "margin_net_pct",
        "profit_flip",
        "margin_flip_pct",
        "profit_order",
        "margin_order_pct",
        "is_robust",
    ]
    cols = [c for c in ordered if c in df.columns] + [c for c in df.columns if c not in ordered]
    return df[cols]


# ------------------------- App -------------------------

st.set_page_config(page_title="AURIA Scanner", layout="wide")
st.title("AURIA – Scanner por categorías (BM)")
inject_css()

db_path = get_root_and_db()
st.caption(f"DB: {db_path}")

slugs = list_category_slugs(db_path)
repo = TemplateRepository(db_path)

with st.sidebar:
    st.header("Filtros")

    if slugs:
        selected_slugs = st.multiselect(
            "Categorías",
            options=slugs,
            default=slugs,
        )
    else:
        st.warning("No pude listar categorías desde SQLite. Revisa la tabla categories.")
        selected_slugs = []

    include_children = st.checkbox("Incluir subcategorías (prefix/*)", value=False)

    st.divider()
    st.subheader("Límites")
    top_n_per_template = st.number_input("Top N por template", min_value=1, max_value=200, value=25, step=5)

    st.divider()
    st.subheader("Filtro net8 (conservador)")
    min_profit_net = st.number_input("Min profit net8", min_value=0, value=1, step=1000)
    min_margin_net = st.number_input("Min margin net8 (%)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
    robust_only = st.checkbox("Solo robust=True", value=True)

    st.divider()
    st.subheader("Orden")
    sort_by = st.selectbox(
        "Ordenar por",
        options=["profit_net", "profit_flip", "profit_order"],
        index=0,
    )

    show_by_template = st.checkbox("Mostrar sub-bloques por template", value=False)

    st.divider()
    query = st.text_input("Buscar (item_id / ciudad / template)", value="").strip().lower()

    st.divider()
    st.subheader("Vista")
    top_cards = st.slider("Cards por categoría", 4, 30, 12, step=2)
    top_table = st.slider("Filas en tabla técnica", 10, 200, 50, step=10)

auto_run = True
run_btn = st.button("Recalcular ahora", type="primary")

if auto_run or run_btn:
    if not selected_slugs:
        st.stop()

    min_margin_net_fraction = float(min_margin_net) / 100.0

    progress = st.progress(0)
    status = st.empty()

    all_category_frames: dict[str, pd.DataFrame] = {}
    total_templates = 0

    cat_specs: dict[str, list] = {}
    for slug in selected_slugs:
        specs = repo.list_for_category(slug, include_children=include_children)
        cat_specs[slug] = specs
        total_templates += len(specs)

    done = 0

    for slug in selected_slugs:
        rows: list[dict] = []
        specs = cat_specs.get(slug, [])
        for spec in specs:
            status.write(f"Analizando {slug} / {spec.template_key} ...")
            data = analyze_template_cached(
                base_item=spec.template_key,
                tier_min=spec.tier_min,
                tier_max=spec.tier_max,
                ench_min=spec.ench_min,
                ench_max=spec.ench_max,
                min_profit_net=int(min_profit_net),
                min_margin_net=float(min_margin_net_fraction),
                top_n=int(top_n_per_template),
            )

            for d in data:
                if robust_only and not d.get("is_robust", False):
                    continue
                d["template_key"] = spec.template_key
                d["category_slug"] = slug
                rows.append(d)

            done += 1
            progress.progress(min(done / max(total_templates, 1), 1.0))

        df = pd.DataFrame(rows)
        if not df.empty:
            df.sort_values(
                by=["is_robust", sort_by, "margin_net"],
                ascending=[False, False, False],
                inplace=True,
                kind="mergesort",
            )

        all_category_frames[slug] = normalize_df(df)

    progress.empty()
    status.empty()

    # ------------------------- Render -------------------------

    st.subheader("Resumen")
    total_ops = sum(len(df) for df in all_category_frames.values() if df is not None)
    st.write(f"Categorías: {len(selected_slugs)} | Oportunidades (post-filtro): {total_ops}")

    col_cfg = {
        "item_url": st.column_config.LinkColumn("Item", display_text=r".*/([^/]+)$"),
        "profit_net": st.column_config.NumberColumn("net8", format="%d"),
        "margin_net_pct": st.column_config.NumberColumn("net8 %", format="%.2f"),
        "profit_flip": st.column_config.NumberColumn("flip4", format="%d"),
        "margin_flip_pct": st.column_config.NumberColumn("flip4 %", format="%.2f"),
        "profit_order": st.column_config.NumberColumn("order6.5", format="%d"),
        "margin_order_pct": st.column_config.NumberColumn("order6.5 %", format="%.2f"),
        "origin_price": st.column_config.NumberColumn("cost", format="%d"),
        "bm_price": st.column_config.NumberColumn("bm", format="%d"),
    }

    st.divider()
    st.subheader("Resultados por categoría (vista cómoda)")

    for slug in selected_slugs:
        df = all_category_frames.get(slug)
        if df is None or df.empty:
            continue

        if query:
            mask = pd.Series(False, index=df.index)
            for c in ["item_url", "origin_city", "template_key"]:
                if c in df.columns:
                    mask = mask | df[c].astype(str).str.lower().str.contains(query, na=False)
            df = df[mask]

        if df.empty:
            continue

        with st.expander(f"{slug} — {len(df)} oportunidades", expanded=False):
            render_category_section(
                slug,
                df,
                top_cards=int(top_cards),
                top_table=int(top_table),
                col_cfg=col_cfg,
            )

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"Descargar CSV ({slug})",
                data=csv,
                file_name=f"{slug.replace('/','_')}.csv",
                mime="text/csv",
            )

            if show_by_template and "template_key" in df.columns:
                st.markdown("### Por template")
                for tkey, tdf in df.groupby("template_key", sort=False):
                    st.markdown(f"**{tkey}** — {len(tdf)}")
                    render_cards(tdf, n=min(8, len(tdf)), cols_per_row=2)
