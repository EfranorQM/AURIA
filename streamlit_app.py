from __future__ import annotations
import streamlit as st
import pandas as pd

# importa tu core directamente (sin FastAPI)
from auria.core.core import MarketCore      # ajusta el import si tu ruta difiere

st.set_page_config(page_title="Albion Trade-Bot", layout="wide")
st.title("🛡️ Albion Trade-Bot Dashboard")

# ── Iniciar los motores solo una vez ──
@st.cache_resource
def get_core():
    return MarketCore(interval=200)   # refresco cada 5 min
core = get_core()

# ------- Sidebar filtros -------
with st.sidebar:
    st.header("Filtros")
    cats_all = core.available_categories()

    city_from = st.selectbox(
        "Ciudad de origen",
        ["(todas)", "Bridgewatch", "Martlock", "Fort Sterling",
         "Lymhurst", "Thetford", "Caerleon", "Black Market"]
    )

    sel_cats = st.multiselect("Categorías", cats_all, default=cats_all)
    limit = st.slider("Resultados por categoría", 5, 100, 20)

# ------- Obtener datos -------
summary = core.summary_by_category(
    city_from=None if city_from == "(todas)" else city_from,
    limit=limit
)

# ------- Mostrar -------
for cat, rows in summary.items():
    st.subheader(f"📂 {cat.capitalize()} – top {len(rows)} rutas")
    if rows:
        df = pd.DataFrame(rows, columns=[
            "Ítem", "Qual", "Origen", "Sell", "Destino", "Buy", "Margen %"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sin rutas con margen positivo.")
