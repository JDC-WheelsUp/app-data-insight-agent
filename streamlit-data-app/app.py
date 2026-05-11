import os
from pathlib import Path
from databricks import sql
from databricks.sdk.core import Config
import streamlit as st
import pandas as pd

# Ensure environment variable is set correctly
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."

st.set_page_config(
    page_title="Taxi Fare Insights",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)


THEME_LIGHT = {
    "--bg-app":         "#f5f6fa",
    "--bg-sidebar":     "#ffffff",
    "--bg-card":        "#ffffff",
    "--bg-input":       "#ffffff",
    "--border-color":   "#dde1ea",
    "--accent":         "#FF3621",
    "--accent-hover":   "#d42c1a",
    "--text-primary":   "#1a1a2e",
    "--text-secondary": "#5a5f7a",
    "--text-muted":     "#9095ae",
    "--text-on-accent": "#ffffff",
    "--shadow-card":    "0 1px 4px rgba(0,0,0,0.08)",
}

THEME_DARK = {
    "--bg-app":         "#1a1a2e",
    "--bg-sidebar":     "#16213e",
    "--bg-card":        "#0f3460",
    "--bg-input":       "#2a2a4a",
    "--border-color":   "#3a3a5c",
    "--accent":         "#FF3621",
    "--accent-hover":   "#ff5a47",
    "--text-primary":   "#e8eaf0",
    "--text-secondary": "#a0a8c8",
    "--text-muted":     "#6a7090",
    "--text-on-accent": "#ffffff",
    "--shadow-card":    "0 1px 6px rgba(0,0,0,0.4)",
}


def inject_theme(dark: bool) -> None:
    """Inject CSS variable values into :root so every var() in styles.css resolves correctly.
    Called on every rerun — Streamlit re-renders the full page so the new values take effect
    immediately without any JavaScript."""
    tokens = THEME_DARK if dark else THEME_LIGHT
    vars_css = "\n".join(f"  {k}: {v};" for k, v in tokens.items())
    st.markdown(f"<style>:root {{\n{vars_css}\n}}</style>", unsafe_allow_html=True)


def load_css(file_name: str):
    """Load external CSS file and inject into the page."""
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def sqlQuery(query: str) -> pd.DataFrame:
    cfg = Config()  # Pull environment variables for auth
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()


# ---------- Session state ----------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------- Load styles ----------
load_css("styles.css")

# ---------- Theme injection ----------
# Writes the correct CSS variable values into :root on every rerun.
# No JavaScript needed — Streamlit strips <script> tags; this pure-CSS
# approach works because Streamlit does a full page re-render on rerun.
inject_theme(st.session_state.dark_mode)


@st.cache_data(ttl=30)  # only re-query if it's been 30 seconds
def getData():
    # This example query depends on the nyctaxi data set in Unity Catalog
    # see https://docs.databricks.com/en/discover/databricks-datasets.html
    return sqlQuery("select * from samples.nyctaxi.trips limit 5000")


data = getData()

# ---------- Header row ----------
header_col, toggle_col = st.columns([8, 1])
with header_col:
    st.markdown("## 🚕 Taxi Fare Distribution")
    st.markdown(
        '<p style="color:var(--text-secondary);margin-top:-0.5rem;font-size:0.9rem;">'
        "NYC taxi trips — scatter chart of fare vs distance with live fare predictor"
        "</p>",
        unsafe_allow_html=True,
    )
with toggle_col:
    _lbl = "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"
    if st.button(_lbl, key="theme_toggle", help="Toggle light / dark theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.markdown("---")

# ---------- Main content ----------
col1, col2 = st.columns([3, 1], gap="large")
with col1:
    st.markdown("#### Fare Amount vs Trip Distance")
    st.scatter_chart(data=data, height=420, y="fare_amount", x="trip_distance")

with col2:
    st.markdown("#### 💡 Predict Fare")
    pickup = st.text_input("From (zipcode)", value="10003")
    dropoff = st.text_input("To (zipcode)", value="11238")

    try:
        d = data[
            (data["pickup_zip"] == int(pickup)) & (data["dropoff_zip"] == int(dropoff))
        ]
        predicted = d["fare_amount"].mean() if len(d) > 0 else 99
    except (ValueError, TypeError):
        predicted = 99

    st.markdown("**Estimated fare**")
    st.markdown(
        f'<div style="font-size:2.2rem;font-weight:700;color:var(--accent);">'
        f"${predicted:.2f}</div>",
        unsafe_allow_html=True,
    )
    if len(d) > 0:
        st.caption(f"Based on {len(d)} historical trips")
    else:
        st.caption("No exact match — showing default estimate")

st.markdown("---")

# ---------- Data table ----------
st.markdown("#### 📋 Raw Trip Data")
st.dataframe(data=data, height=500, use_container_width=True)
