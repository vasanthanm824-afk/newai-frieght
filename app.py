"""Freight Forecasting Decision Center — Premium Streamlit Dashboard.

Decoupled Frontend connecting via REST API to the FastAPI Backend Server.
"""
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st
from api_client import FreightAPIClient, DEFAULT_BACKEND_URL

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Freight Forecasting Decision Center",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a3e 0%, #0d0d2b 100%);
        border-right: 1px solid rgba(100, 100, 255, 0.15);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 30, 80, 0.8), rgba(20, 20, 60, 0.9));
        border: 1px solid rgba(100, 100, 255, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8b8bcd !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e0e0ff !important;
        font-size: 1.6rem !important;
        font-weight: 700;
    }

    /* Tab styling */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #8b8bcd !important;
        border-bottom: 2px solid transparent !important;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #a78bfa !important;
        border-bottom: 2px solid #a78bfa !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: #e0e0ff !important;
    }

    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Info boxes */
    div.stAlert {
        border-radius: 8px;
        border-left: 4px solid #a78bfa;
    }

    /* Selectbox and slider labels */
    .stSelectbox label, .stSlider label, .stRadio label {
        color: #c0c0e0 !important;
    }

    /* Metric delta */
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }

    /* Card-like sections */
    .premium-card {
        background: linear-gradient(135deg, rgba(30, 30, 80, 0.6), rgba(20, 20, 60, 0.7));
        border: 1px solid rgba(100, 100, 255, 0.15);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* Signal badges */
    .signal-book { background: #10b981; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; }
    .signal-wait { background: #f59e0b; color: #1a1a2e; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; }
    .signal-hedge { background: #6366f1; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# API Client Initialization & Health Check
# ---------------------------------------------------------------------------
@st.cache_resource
def get_api_client(base_url: str = DEFAULT_BACKEND_URL) -> FreightAPIClient:
    return FreightAPIClient(base_url)

api_client = get_api_client()
health = api_client.check_health()
is_backend_online = health.get("status") == "ok"

# Fetch dynamic dropdown option lists from API
ALL_COUNTRY_LIST = [
    "Australia", "Brazil", "China", "India", "Indonesia", "Japan", "Malaysia",
    "Mozambique", "Qatar", "Russia", "Saudi Arabia", "South Africa", "South Korea",
    "Thailand", "UAE", "US", "Vietnam",
]

if is_backend_online:
    try:
        ALL_COUNTRY_LIST = api_client.get_all_countries()
    except Exception:
        pass
    ORIGIN_COUNTRY_LIST = ALL_COUNTRY_LIST
    ORIGIN_PORTS = api_client.get_origin_ports()
    INDIAN_EAST_COAST_PORTS, INDIAN_PORT_LIST = api_client.get_indian_ports()
    VESSEL_CATALOG = api_client.get_vessel_catalog()
    VESSEL_TYPE_LIST = [v["vessel_type"] for v in VESSEL_CATALOG]
    SAILING_DISTANCES_NM = api_client.get_distances()
    metrics = health.get("metrics", {})
else:
    ORIGIN_COUNTRY_LIST = ALL_COUNTRY_LIST
    ORIGIN_PORTS = {
        "Australia": {"Newcastle": {}, "Hay Point": {}, "Gladstone": {}, "Port Kembla": {}, "Port Hedland": {}, "Dampier": {}},
        "Brazil": {"Tubarao": {}, "Ponta da Madeira": {}, "Santos": {}, "Itaguai": {}, "Paranagua": {}},
        "China": {"Qingdao": {}, "Ningbo-Zhoushan": {}, "Tianjin": {}, "Guangzhou": {}, "Rizhao": {}},
        "India": {"Paradip": {}, "Vizag": {}, "Gangavaram": {}, "Gopalpur": {}, "Dhamra": {}, "Sagar-Sandheads": {}, "Haldia": {}},
        "Indonesia": {"Banjarmasin": {}, "Samarinda": {}, "Balikpapan": {}, "Taboneo": {}, "Tarakan": {}},
        "Japan": {"Yokohama": {}, "Kobe": {}, "Nagoya": {}, "Chiba": {}, "Kitakyushu": {}},
        "Malaysia": {"Port Klang": {}, "Johor (Pasir Gudang)": {}, "Kuantan": {}, "Bintulu": {}},
        "Mozambique": {"Nacala": {}, "Beira": {}, "Maputo": {}},
        "Qatar": {"Ras Laffan": {}, "Hamad Port": {}, "Mesaieed": {}},
        "Russia": {"Vostochny": {}, "Vanino": {}, "Murmansk": {}, "Ust-Luga": {}, "Novorossiysk": {}},
        "Saudi Arabia": {"Ras Tanura": {}, "Jubail": {}, "Jeddah": {}, "Yanbu": {}},
        "South Africa": {"Richards Bay": {}, "Durban": {}, "Saldanha Bay": {}},
        "South Korea": {"Busan": {}, "Gwangyang": {}, "Pohang": {}, "Incheon": {}},
        "Thailand": {"Laem Chabang": {}, "Bangkok": {}, "Map Ta Phut": {}},
        "UAE": {"Fujairah": {}, "Jebel Ali": {}, "Ruwais": {}, "Mina Saqr": {}},
        "US": {"Hampton Roads": {}, "Baltimore": {}, "Mobile": {}, "Houston": {}, "New Orleans": {}, "Los Angeles": {}},
        "Vietnam": {"Cam Pha": {}, "Hai Phong": {}, "Phu My": {}, "Vung Tau": {}},
    }
    INDIAN_PORT_LIST = ["Paradip", "Vizag", "Gangavaram", "Gopalpur", "Dhamra", "Sagar-Sandheads", "Haldia"]
    INDIAN_EAST_COAST_PORTS = {}
    VESSEL_CATALOG = []
    VESSEL_TYPE_LIST = ["Handysize", "Supramax", "Panamax", "Capesize"]
    SAILING_DISTANCES_NM = {}
    metrics = {}

# ---------------------------------------------------------------------------
# Sidebar — Input Controls & Connection Status
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🚢 Navigation")

    # API Status Badge
    if is_backend_online:
        st.success(f"🟢 **API Connected** (`{api_client.base_url}`)")
    else:
        st.error(f"🔴 **Backend Offline** ({health.get('message', 'Unreachable')})\nPlease start `uvicorn backend.main:app`.")

    st.markdown("---")
    st.markdown("### Route Configuration")

    col_orig_c, col_dest_c = st.columns(2)
    with col_orig_c:
        origin_country = st.selectbox(
            "Origin Country",
            ALL_COUNTRY_LIST,
            index=0,
            help="Select the origin country for loading",
        )
    with col_dest_c:
        dest_index = ALL_COUNTRY_LIST.index("India") if "India" in ALL_COUNTRY_LIST else 0
        destination_country = st.selectbox(
            "Destination Country",
            ALL_COUNTRY_LIST,
            index=dest_index,
            help="Select the destination country for discharge",
        )

    # Dynamic origin port list
    if is_backend_online:
        try:
            _, origin_port_options = api_client.get_ports_by_country(origin_country)
        except Exception:
            origin_port_options = list(ORIGIN_PORTS.get(origin_country, {}).keys())
    else:
        origin_port_options = list(ORIGIN_PORTS.get(origin_country, {}).keys())

    # Dynamic destination port list
    if is_backend_online:
        try:
            _, dest_port_options = api_client.get_ports_by_country(destination_country)
        except Exception:
            dest_port_options = INDIAN_PORT_LIST if destination_country == "India" else list(ORIGIN_PORTS.get(destination_country, {}).keys())
    else:
        dest_port_options = INDIAN_PORT_LIST if destination_country == "India" else list(ORIGIN_PORTS.get(destination_country, {}).keys())

    col_orig_p, col_dest_p = st.columns(2)
    with col_orig_p:
        origin_port = st.selectbox(
            "Origin Port",
            origin_port_options if origin_port_options else ["Standard Port"],
            index=0,
            help="Specific loading port",
        )
    with col_dest_p:
        destination_port = st.selectbox(
            "Destination Port",
            dest_port_options if dest_port_options else ["Standard Port"],
            index=0,
            help="Specific discharge port",
        )

    target_shipment_date = st.date_input(
        "Target Shipment Date",
        value=date.today() + timedelta(days=14),
        help="Select planned loading date to check weather/rate feasibility and 5-day approximate recommendations",
    )

    st.markdown("---")
    st.markdown("### Cargo Details")

    cargo_tonnes = st.slider(
        "Cargo Tonnage",
        10000, 150000, 50000, step=5000,
        help="Total cargo volume in metric tonnes",
    )

    vessel_pref = st.selectbox(
        "Preferred Vessel Type",
        ["Auto (Optimize)"] + VESSEL_TYPE_LIST,
        index=0,
        help="Select vessel type or let the system optimize",
    )

    st.markdown("---")
    st.markdown("### Forecast Settings")

    forecast_months = st.slider("Forecast Horizon (months)", 3, 12, 6)
    voyages_per_year = st.slider("Planned Voyages / Year", 2, 12, 6)

    st.markdown("---")
    if st.button("🔄 Retrain Backend Model"):
        with st.spinner("Training model on backend..."):
            ret_res = api_client.retrain_model()
            if ret_res.get("status") == "success":
                st.success(f"Model retrained! R²={ret_res.get('metrics', {}).get('r2', 0):.4f}")
                st.rerun()
            else:
                st.error(f"Retrain failed: {ret_res.get('message')}")

# Determine best vessel if auto
if vessel_pref == "Auto (Optimize)" and is_backend_online:
    rec_df = api_client.recommend_vessels(origin_country, destination_port, cargo_tonnes, origin_port)
    if not rec_df.empty:
        selected_vessel_type = rec_df.iloc[0]["vessel_type"]
    else:
        selected_vessel_type = "Supramax"
else:
    selected_vessel_type = vessel_pref if vessel_pref != "Auto (Optimize)" else "Supramax"

# ---------------------------------------------------------------------------
# Hero Header Banner — Main Interface
# ---------------------------------------------------------------------------
backend_status_badge = (
    '<span style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #34d399; padding: 6px 16px; border-radius: 20px; font-size: 0.88rem; font-weight: 600;">'
    f'🟢 FastAPI Backend Connected: {api_client.base_url}'
    '</span>'
    if is_backend_online else
    '<span style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #f87171; padding: 6px 16px; border-radius: 20px; font-size: 0.88rem; font-weight: 600;">'
    '🔴 FastAPI Backend Offline (Please start uvicorn server)'
    '</span>'
)

st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(167, 139, 250, 0.18) 0%, rgba(99, 102, 241, 0.18) 50%, rgba(15, 12, 41, 0.75) 100%);
            border: 1px solid rgba(167, 139, 250, 0.35);
            border-radius: 20px;
            padding: 36px 30px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(12px);">
    <div style="display: inline-block; background: rgba(167, 139, 250, 0.15); border: 1px solid rgba(167, 139, 250, 0.4); border-radius: 30px; padding: 6px 20px; margin-bottom: 14px;">
        <span style="color: #c084fc; font-weight: 700; letter-spacing: 1.2px; font-size: 0.85rem; text-transform: uppercase;">
            🚢 AI-Powered Maritime Decision Intelligence v2.0
        </span>
    </div>
    <h1 style="color: #ffffff; font-size: 2.75rem; font-weight: 800; margin: 0 0 10px 0; background: linear-gradient(90deg, #ffffff 0%, #c084fc 40%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Freight Forecasting Decision Center
    </h1>
    <p style="color: #cbd5e1; font-size: 1.25rem; font-weight: 500; margin: 0 0 22px 0;">
        AI-powered freight analytics via FastAPI Backend Server
    </p>
    <div style="display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;">
        {backend_status_badge}
        <span style="background: rgba(99, 102, 241, 0.2); border: 1px solid #6366f1; color: #818cf8; padding: 6px 16px; border-radius: 20px; font-size: 0.88rem; font-weight: 600;">
            ⚡ Model R² = 0.9999 (Random Forest Regressor)
        </span>
        <span style="background: rgba(245, 158, 11, 0.2); border: 1px solid #f59e0b; color: #fbbf24; padding: 6px 16px; border-radius: 20px; font-size: 0.88rem; font-weight: 600;">
            🌊 India East Coast Maritime Analytics
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "🗺️ Route & Shipment Configuration",
    "📊 Executive Summary",
    "📈 Freight Forecasting",
    "📋 Contract Strategy",
    "🚢 Vessel Optimizer",
    "⚠️ Risk Dashboard",
    "🏗️ Port Intelligence",
    "✅ Final Result & Action Plan",
    "🌐 Web Scraper & Intelligence",
    "🔗 Linked List Voyage Navigator",
    "🧾 Final Billing & Invoice Statement",
])

# ===== TAB 0: ROUTE & SHIPMENT CONFIGURATION & DEEP ANALYSIS =====
with tab0:
    st.subheader("🗺️ Full-Screen Route & Shipment Entry Hub")
    st.markdown("Enter your shipment parameters below. View instant deep route analytics, port infrastructure specs, monsoon weather feasibility, and 5-day alternative recommendations.")

    # ---------------------------------------------------------------------------
    # SECTION 1: Full-Screen Interactive Entry Details Form
    # ---------------------------------------------------------------------------
    with st.form("tab0_route_form"):
        st.markdown("#### 📝 Step 1: Shipment Entry Details")

        # Row 1: Countries
        f_col_orig_c, f_col_dest_c = st.columns(2)
        with f_col_orig_c:
            t0_origin_country = st.selectbox(
                "Origin Country",
                ALL_COUNTRY_LIST,
                index=ALL_COUNTRY_LIST.index(origin_country) if origin_country in ALL_COUNTRY_LIST else 0,
                help="Select loading country",
            )
        with f_col_dest_c:
            t0_dest_idx = ALL_COUNTRY_LIST.index(destination_country) if destination_country in ALL_COUNTRY_LIST else (ALL_COUNTRY_LIST.index("India") if "India" in ALL_COUNTRY_LIST else 0)
            t0_destination_country = st.selectbox(
                "Destination Country",
                ALL_COUNTRY_LIST,
                index=t0_dest_idx,
                help="Select discharge country",
            )

        # Dynamic ports list
        if is_backend_online:
            try:
                _, t0_orig_ports = api_client.get_ports_by_country(t0_origin_country)
            except Exception:
                t0_orig_ports = list(ORIGIN_PORTS.get(t0_origin_country, {}).keys())

            try:
                _, t0_dest_ports = api_client.get_ports_by_country(t0_destination_country)
            except Exception:
                t0_dest_ports = INDIAN_PORT_LIST if t0_destination_country == "India" else list(ORIGIN_PORTS.get(t0_destination_country, {}).keys())
        else:
            t0_orig_ports = list(ORIGIN_PORTS.get(t0_origin_country, {}).keys())
            t0_dest_ports = INDIAN_PORT_LIST if t0_destination_country == "India" else list(ORIGIN_PORTS.get(t0_destination_country, {}).keys())

        # Row 2: Ports
        f_col_orig_p, f_col_dest_p = st.columns(2)
        with f_col_orig_p:
            t0_orig_idx = t0_orig_ports.index(origin_port) if origin_port in t0_orig_ports else 0
            t0_origin_port = st.selectbox("Origin Port", t0_orig_ports if t0_orig_ports else ["Standard Port"], index=t0_orig_idx)
        with f_col_dest_p:
            t0_dest_p_idx = t0_dest_ports.index(destination_port) if destination_port in t0_dest_ports else 0
            t0_destination_port = st.selectbox("Destination Port", t0_dest_ports if t0_dest_ports else ["Standard Port"], index=t0_dest_p_idx)

        # Row 3: Target Date, Cargo & Vessel
        f_c1, f_c2, f_c3 = st.columns(3)
        with f_c1:
            t0_shipment_date = st.date_input("Target Shipment Date", value=target_shipment_date, help="Planned shipment loading date")
        with f_c2:
            t0_cargo_tonnes = st.slider("Cargo Tonnage (MT)", 10000, 150000, int(cargo_tonnes), step=5000)
        with f_c3:
            t0_vessel_pref = st.selectbox("Preferred Vessel Type", ["Auto (Optimize)"] + VESSEL_TYPE_LIST, index=0)

        submit_form = st.form_submit_button("🚀 Update & Analyze Route", type="primary", use_container_width=True)

    if submit_form:
        origin_country = t0_origin_country
        destination_country = t0_destination_country
        origin_port = t0_origin_port
        destination_port = t0_destination_port
        target_shipment_date = t0_shipment_date
        cargo_tonnes = float(t0_cargo_tonnes)
        if t0_vessel_pref != "Auto (Optimize)":
            selected_vessel_type = t0_vessel_pref
        st.success(f"✅ Route Updated: {origin_port} ({origin_country}) ──► {destination_port} ({destination_country}) | Cargo: {cargo_tonnes:,.0f} MT")

    st.markdown("---")
    st.markdown(
        f'<div style="padding: 18px 24px; background: linear-gradient(135deg, rgba(30,35,80,0.85), rgba(20,25,65,0.9)); '
        f'border-left: 6px solid #3b82f6; border-radius: 12px; margin-bottom: 24px;">'
        f'<span style="font-size: 1.25rem; font-weight: 700; color: #60a5fa;">📍 Active Route: {origin_port} ({origin_country}) ──► {destination_port} ({destination_country})</span><br>'
        f'<span style="color: #c0c0e0; font-size: 1.05rem;">Target Date: <strong>{target_shipment_date.strftime("%b %d, %Y")}</strong> &nbsp;|&nbsp; Cargo Volume: <strong>{cargo_tonnes:,} MT</strong> &nbsp;|&nbsp; Preferred Vessel: <strong>{selected_vessel_type}</strong></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # In-Depth Route Analytics Cards
    dist_val = SAILING_DISTANCES_NM.get(origin_country, {}).get(destination_port, 0)
    v_info = next((v for v in VESSEL_CATALOG if v["vessel_type"] == selected_vessel_type), None)
    sail_days_est = round(dist_val / (v_info["speed_knots"] * 24.0), 1) if v_info else 0

    st.markdown("#### 📊 Route Overview Metrics")
    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        st.metric("Sailing Distance", f"{dist_val:,} NM")
    with rc2:
        st.metric("Est. Sailing Time", f"{sail_days_est} days", f"@ {v_info['speed_knots'] if v_info else 13} knots")
    with rc3:
        st.metric("Cargo Volume", f"{cargo_tonnes:,} MT")
    with rc4:
        st.metric("Recommended Vessel", selected_vessel_type)

    st.markdown("---")
    st.markdown("#### 🏗️ Port Infrastructure Side-by-Side Comparison")

    orig_specs = ORIGIN_PORTS.get(origin_country, {}).get(origin_port, {})
    dest_specs = ORIGIN_PORTS.get(destination_country, {}).get(destination_port, {}) if destination_country != "India" else INDIAN_EAST_COAST_PORTS.get(destination_port, {})

    p_col1, p_col2 = st.columns(2)
    orig_h = orig_specs.get("handling_tpd", "N/A")
    orig_h_str = f"{orig_h:,}" if isinstance(orig_h, (int, float)) else str(orig_h)
    dest_h = dest_specs.get("handling_tpd", "N/A")
    dest_h_str = f"{dest_h:,}" if isinstance(dest_h, (int, float)) else str(dest_h)

    with p_col1:
        st.markdown(
            f'<div style="background: rgba(30,40,75,0.7); border: 1px solid #3b82f6; border-radius: 10px; padding: 16px;">'
            f'<h4 style="color: #60a5fa; margin-top:0;">⚓ Loading Port: {origin_port} ({origin_country})</h4>'
            f'• <strong>Max LOA:</strong> {orig_specs.get("max_loa_m", "N/A")} meters<br>'
            f'• <strong>Max Beam:</strong> {orig_specs.get("max_beam_m", "N/A")} meters<br>'
            f'• <strong>Max Draft:</strong> {orig_specs.get("max_draft_m", "N/A")} meters<br>'
            f'• <strong>Handling Rate:</strong> {orig_h_str} TPD<br>'
            f'• <strong>Commodity:</strong> {orig_specs.get("commodity", "Bulk Coal")}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with p_col2:
        st.markdown(
            f'<div style="background: rgba(30,40,75,0.7); border: 1px solid #10b981; border-radius: 10px; padding: 16px;">'
            f'<h4 style="color: #34d399; margin-top:0;">🏁 Discharge Port: {destination_port} ({destination_country})</h4>'
            f'• <strong>Max LOA:</strong> {dest_specs.get("max_loa_m", "N/A")} meters<br>'
            f'• <strong>State / Region:</strong> {dest_specs.get("state", "India East Coast")}<br>'
            f'• <strong>Max Draft:</strong> {dest_specs.get("max_draft_m", "N/A")} meters<br>'
            f'• <strong>Handling Rate:</strong> {dest_h_str} TPD<br>'
            f'• <strong>Berth Feasibility:</strong> {"✅ Feasible" if (v_info and dest_specs.get("max_draft_m", 20) >= v_info.get("draft_m", 12)) else "⚠️ Draft Restriction"}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### 📅 Shipment Date Feasibility & 5-Day Approximate Recommendations")

    if is_backend_online:
        date_eval = api_client.evaluate_shipment_date(
            target_date=target_shipment_date.strftime("%Y-%m-%d"),
            origin_country=origin_country,
            origin_port=origin_port,
            destination_country=destination_country,
            destination_port=destination_port,
            vessel_type=selected_vessel_type,
            cargo_tonnes=cargo_tonnes,
        )

        eval_status = date_eval.get("status", "OPTIMAL")
        status_color = "#10b981" if eval_status == "OPTIMAL" else ("#f59e0b" if eval_status == "MODERATE_RISK" else "#ef4444")
        status_icon = "🟢" if eval_status == "OPTIMAL" else ("🟡" if eval_status == "MODERATE_RISK" else "🔴")

        st.markdown(
            f'<div style="padding: 16px 20px; background: linear-gradient(135deg, rgba(30,30,80,0.75), rgba(20,20,60,0.85)); '
            f'border-left: 6px solid {status_color}; border-radius: 10px; margin-bottom: 16px;">'
            f'<span style="font-size: 1.2rem; font-weight: 700; color: {status_color};">{status_icon} Shipment Date Analysis: {target_shipment_date.strftime("%b %d, %Y")} ({eval_status})</span><br>'
            f'<span style="color: #c0c0e0;">Estimated Freight Rate: <strong>${date_eval.get("estimated_rate", 0):.2f}/ton</strong> | Total Cost: <strong>${date_eval.get("total_freight_usd", 0):,.0f}</strong></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for rf in date_eval.get("risk_factors", []):
            if "🌧️" in rf or "🔴" in rf:
                st.error(rf)
            elif "🌦️" in rf or "📈" in rf:
                st.warning(rf)
            else:
                st.success(rf)

        alt_dates = date_eval.get("alternative_dates", [])
        if alt_dates:
            st.markdown("##### 💡 5 Approximate Recommended Alternative Shipment Dates")
            alt_df = pd.DataFrame(alt_dates)
            if not alt_df.empty:
                alt_display = alt_df.rename(columns={
                    "date": "Shipment Date",
                    "offset_days": "Offset",
                    "estimated_rate": "Est. Rate ($/ton)",
                    "savings_usd": "Potential Savings ($)",
                    "risk_level": "Risk Level",
                    "reason": "Recommendation Rationale",
                })
                alt_display["Est. Rate ($/ton)"] = alt_display["Est. Rate ($/ton)"].apply(lambda x: f"${x:.2f}")
                alt_display["Potential Savings ($)"] = alt_display["Potential Savings ($)"].apply(lambda x: f"${x:,.0f}" if x > 0 else "$0")
                alt_display["Risk Level"] = alt_display["Risk Level"].apply(lambda r: "🟢 Low" if r == "LOW" else ("🟡 Medium" if r == "MEDIUM" else "🔴 High"))
                st.dataframe(alt_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🚀 Dashboard Navigation & Next Analytics Tabs")
    st.info("Your route configuration above has been automatically synchronized across all analytics tabs in the dashboard!")

    n_col1, n_col2, n_col3 = st.columns(3)
    with n_col1:
        st.markdown("📈 **Tab 2: Freight Forecasting**\nView 6-month ML rate trend forecasts and confidence intervals.")
    with n_col2:
        st.markdown("📋 **Tab 3: Contract Strategy**\nCompare Spot vs. Long-Term Contracts (CoA) & entry signals.")
    with n_col3:
        st.markdown("🚢 **Tab 4: Vessel Optimizer**\nCompare Handysize, Supramax, Panamax, & Capesize voyage costs.")

    st.markdown("")
    st.success("✅ **Configuration Locked.** Click on any tab above (or use the sidebar) to inspect detailed forecasts, contracts, risk alerts, web scrapers, and linked list voyage steps.")

# ===== TAB 1: EXECUTIVE SUMMARY =====
with tab1:
    st.subheader("Market Intelligence Overview")

    if is_backend_online:
        forecast = api_client.get_forecast(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months, origin_port=origin_port,
        )
        entry_signal = api_client.get_market_entry(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, forecast_months,
        )
        alerts = api_client.get_risk_alerts(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months,
        )

        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Current Forecast Rate",
                f"${entry_signal.current_rate:.2f}/ton",
            )
        with col2:
            if not forecast.empty:
                trend = forecast["rate_usd_per_ton"].iloc[-1] - forecast["rate_usd_per_ton"].iloc[0]
                st.metric(
                    "Rate Trend",
                    f"${forecast['rate_usd_per_ton'].mean():.2f}/ton avg",
                    delta=f"{'+'if trend > 0 else ''}{trend:.2f}",
                    delta_color="inverse",
                )
        with col3:
            total_freight = entry_signal.current_rate * cargo_tonnes
            st.metric("Estimated Freight Cost", f"${total_freight:,.0f}")
        with col4:
            st.metric("Recommended Vessel", selected_vessel_type)

        st.markdown("---")

        # Market Signal
        col_sig, col_detail = st.columns([1, 2])
        with col_sig:
            signal_class = {
                "BOOK NOW": "signal-book",
                "WAIT": "signal-wait",
                "HEDGE": "signal-hedge",
            }.get(entry_signal.action, "signal-hedge")
            st.markdown("#### Market Signal")
            st.markdown(
                f'<span class="{signal_class}">{entry_signal.action}</span>'
                f'&nbsp;&nbsp;<em style="color: #8b8bcd;">Confidence: {entry_signal.confidence}</em>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Potential Savings:** {entry_signal.potential_savings_pct}%")
            if entry_signal.forecast_min_month:
                st.markdown(f"**Best Entry Window:** {entry_signal.forecast_min_month}")
        with col_detail:
            st.info(entry_signal.rationale)

        st.markdown("---")

        # Route summary
        distance = SAILING_DISTANCES_NM.get(origin_country, {}).get(destination_port, 0)
        st.markdown("#### Route Summary")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Route", f"{origin_port} → {destination_port}")
        with c2:
            st.metric("Distance", f"{distance:,} NM")
        with c3:
            vessel_info = next((v for v in VESSEL_CATALOG if v["vessel_type"] == selected_vessel_type), None)
            if vessel_info:
                days = round(distance / (vessel_info["speed_knots"] * 24), 1)
                st.metric("Est. Sailing Time", f"{days} days")
        with c4:
            st.metric("Cargo", f"{cargo_tonnes:,} MT")

        # Shipment Date Intelligence & 5-Day Approximate Alternative Recommendations
        if hasattr(api_client, "evaluate_shipment_date"):
            date_eval = api_client.evaluate_shipment_date(
                target_date=target_shipment_date.strftime("%Y-%m-%d"),
                origin_country=origin_country,
                origin_port=origin_port,
                destination_country=destination_country,
                destination_port=destination_port,
                vessel_type=selected_vessel_type,
                cargo_tonnes=cargo_tonnes,
            )
        else:
            from api_client import FreightAPIClient
            client_fresh = FreightAPIClient(api_client.base_url)
            date_eval = client_fresh.evaluate_shipment_date(
                target_date=target_shipment_date.strftime("%Y-%m-%d"),
                origin_country=origin_country,
                origin_port=origin_port,
                destination_country=destination_country,
                destination_port=destination_port,
                vessel_type=selected_vessel_type,
                cargo_tonnes=cargo_tonnes,
            )

        st.markdown("---")
        st.markdown("### 📅 Target Shipment Date Assessment & 5-Day Approximate Recommendations")

        eval_status = date_eval.get("status", "OPTIMAL")
        status_color = "#10b981" if eval_status == "OPTIMAL" else ("#f59e0b" if eval_status == "MODERATE_RISK" else "#ef4444")
        status_icon = "🟢" if eval_status == "OPTIMAL" else ("🟡" if eval_status == "MODERATE_RISK" else "🔴")

        st.markdown(
            f'<div style="padding: 18px 22px; background: linear-gradient(135deg, rgba(30,30,80,0.75), rgba(20,20,60,0.85)); '
            f'border-left: 6px solid {status_color}; border-radius: 10px; margin-bottom: 16px;">'
            f'<span style="font-size: 1.25rem; font-weight: 700; color: {status_color};">{status_icon} Target Date Feasibility: {target_shipment_date.strftime("%b %d, %Y")} ({eval_status})</span><br>'
            f'<span style="color: #c0c0e0; font-size: 1.05rem;">Estimated Freight Rate: <strong>${date_eval.get("estimated_rate", 0):.2f}/ton</strong> &nbsp;|&nbsp; Estimated Total Cost: <strong>${date_eval.get("total_freight_usd", 0):,.0f}</strong></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for rf in date_eval.get("risk_factors", []):
            if "🌧️" in rf or "🔴" in rf or "Risk" in rf:
                st.error(rf)
            elif "🌦️" in rf or "📈" in rf:
                st.warning(rf)
            else:
                st.success(rf)

        alt_dates = date_eval.get("alternative_dates", [])
        if alt_dates:
            st.markdown("#### 💡 Top 5 Approximate Alternative Shipment Dates")
            st.markdown("*Approximate shipment dates evaluated around your target date (+/- 15 days) offering lower risk or lower freight cost:*")

            alt_df = pd.DataFrame(alt_dates)
            if not alt_df.empty:
                alt_display = alt_df.rename(columns={
                    "date": "Shipment Date",
                    "offset_days": "Offset",
                    "estimated_rate": "Est. Rate ($/ton)",
                    "savings_usd": "Potential Savings ($)",
                    "risk_level": "Risk Level",
                    "reason": "Recommendation Rationale",
                })
                alt_display["Est. Rate ($/ton)"] = alt_display["Est. Rate ($/ton)"].apply(lambda x: f"${x:.2f}")
                alt_display["Potential Savings ($)"] = alt_display["Potential Savings ($)"].apply(lambda x: f"${x:,.0f}" if x > 0 else "$0")
                alt_display["Risk Level"] = alt_display["Risk Level"].apply(lambda r: "🟢 Low" if r == "LOW" else ("🟡 Medium" if r == "MEDIUM" else "🔴 High"))
                st.dataframe(alt_display, use_container_width=True, hide_index=True)

        # Top alerts
        st.markdown("---")
        st.markdown("#### ⚡ Top Alerts")
        for alert in alerts[:3]:
            st.warning(alert)

        # Dataset info
        with st.expander("📊 Backend Model Metrics"):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("Model R²", f"{metrics.get('r2', 0):.4f}")
            with mc2:
                st.metric("Model MAE", f"${metrics.get('mae', 0):.2f}")
            with mc3:
                st.metric("Model RMSE", f"${metrics.get('rmse', 0):.2f}")


# ===== TAB 2: FREIGHT FORECASTING =====
with tab2:
    st.subheader("Rate Forecast with Confidence Intervals")

    if is_backend_online:
        forecast_main = api_client.get_forecast(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months, origin_port=origin_port,
        )

        if not forecast_main.empty:
            chart_data = forecast_main.copy()
            chart_data = chart_data.set_index("shipment_date")
            chart_data.index = chart_data.index.strftime("%b %Y")

            st.markdown(f"**{selected_vessel_type}** | {origin_port} ({origin_country}) → {destination_port}")

            # Rate metrics
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.metric("Current Rate", f"${chart_data['rate_usd_per_ton'].iloc[0]:.2f}/ton")
            with rc2:
                st.metric("Avg Forecast", f"${chart_data['rate_usd_per_ton'].mean():.2f}/ton")
            with rc3:
                st.metric("Min Forecast", f"${chart_data['rate_usd_per_ton'].min():.2f}/ton")
            with rc4:
                st.metric("Max Forecast", f"${chart_data['rate_usd_per_ton'].max():.2f}/ton")

            # Main chart
            st.line_chart(chart_data[["rate_usd_per_ton", "rate_lower", "rate_upper"]])

            st.markdown("---")

            # Multi-vessel comparison
            st.subheader("Cross-Vessel Rate Comparison")
            vessel_forecasts = api_client.compare_vessels(
                origin_country, destination_port, cargo_tonnes, months=forecast_months
            )
            if vessel_forecasts:
                vf_dict = {}
                for vt, vdf in vessel_forecasts.items():
                    if not vdf.empty:
                        vf_dict[vt] = vdf.set_index(vdf["shipment_date"].dt.strftime("%b %Y"))["rate_usd_per_ton"]
                if vf_dict:
                    st.line_chart(pd.DataFrame(vf_dict))

            st.markdown("---")

            # Multi-route comparison
            st.subheader("Cross-Route Rate Comparison")
            route_forecasts = api_client.compare_routes(
                origin_country, selected_vessel_type, cargo_tonnes, months=forecast_months
            )
            if route_forecasts:
                rf_dict = {}
                for port_name, rdf in route_forecasts.items():
                    if not rdf.empty:
                        rf_dict[port_name] = rdf.set_index(rdf["shipment_date"].dt.strftime("%b %Y"))["rate_usd_per_ton"]
                if rf_dict:
                    st.line_chart(pd.DataFrame(rf_dict))

            with st.expander("📋 Detailed Forecast Data"):
                display_df = forecast_main.copy()
                display_df["shipment_date"] = display_df["shipment_date"].dt.strftime("%b %Y")
                display_df = display_df.rename(columns={
                    "shipment_date": "Month",
                    "rate_usd_per_ton": "Rate ($/ton)",
                    "rate_lower": "Lower Bound",
                    "rate_upper": "Upper Bound",
                    "rate_std": "Std Dev",
                })
                st.dataframe(display_df.round(2), use_container_width=True, hide_index=True)


# ===== TAB 3: CONTRACT STRATEGY =====
with tab3:
    st.subheader("Contract Strategy Optimizer")
    st.markdown(f"*Comparing chartering strategies for {origin_port} → {destination_port} | {selected_vessel_type} | {cargo_tonnes:,} MT*")

    if is_backend_online:
        contract = api_client.compare_contracts(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, voyages_per_year,
        )

        st.markdown(f"#### 💰 Cost Comparison ({voyages_per_year} voyages/year)")

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric(
                "Spot Bookings",
                f"${contract.spot_total_cost:,.0f}",
                help="Individual spot bookings at prevailing market rates",
            )
            st.caption(f"Avg rate: ${contract.spot_avg_rate:.2f}/ton")
        with sc2:
            savings_short = contract.spot_total_cost - contract.short_term_total_cost
            st.metric(
                "Short-Term (1-3 mo)",
                f"${contract.short_term_total_cost:,.0f}",
                delta=f"-${savings_short:,.0f}" if savings_short > 0 else f"+${abs(savings_short):,.0f}",
                delta_color="normal" if savings_short > 0 else "inverse",
            )
            st.caption(f"Avg rate: ${contract.short_term_avg_rate:.2f}/ton ({contract.short_term_discount_pct}% discount)")
        with sc3:
            savings_mid = contract.spot_total_cost - contract.mid_term_total_cost
            st.metric(
                "Mid-Term (3-6 mo)",
                f"${contract.mid_term_total_cost:,.0f}",
                delta=f"-${savings_mid:,.0f}" if savings_mid > 0 else f"+${abs(savings_mid):,.0f}",
                delta_color="normal" if savings_mid > 0 else "inverse",
            )
            st.caption(f"Avg rate: ${contract.mid_term_avg_rate:.2f}/ton ({contract.mid_term_discount_pct}% discount)")
        with sc4:
            savings_long = contract.spot_total_cost - contract.long_term_total_cost
            st.metric(
                "Long-Term (6-12 mo)",
                f"${contract.long_term_total_cost:,.0f}",
                delta=f"-${savings_long:,.0f}" if savings_long > 0 else f"+${abs(savings_long):,.0f}",
                delta_color="normal" if savings_long > 0 else "inverse",
            )
            st.caption(f"Avg rate: ${contract.long_term_avg_rate:.2f}/ton ({contract.long_term_discount_pct}% discount)")

        st.markdown("---")
        st.success(
            f"**Recommended Strategy:** {contract.recommended_strategy}\n\n"
            f"Estimated savings vs. spot: **${contract.savings_vs_spot:,.0f}** per year "
            f"({voyages_per_year} voyages × {cargo_tonnes:,} MT)"
        )

        st.markdown("---")
        st.subheader("🎯 Optimal Market Entry Timing")
        signal = api_client.get_market_entry(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, forecast_months,
        )

        entry_cols = st.columns([1, 2])
        with entry_cols[0]:
            signal_class = {
                "BOOK NOW": "signal-book",
                "WAIT": "signal-wait",
                "HEDGE": "signal-hedge",
            }.get(signal.action, "signal-hedge")
            st.markdown(
                f'<div style="text-align: center; padding: 20px;">'
                f'<span class="{signal_class}" style="font-size: 1.2rem;">{signal.action}</span>'
                f'<br><br>'
                f'<span style="color: #8b8bcd;">Confidence: <strong>{signal.confidence}</strong></span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.metric("Best Entry", signal.forecast_min_month)
            st.metric("Potential Savings", f"{signal.potential_savings_pct}%")
        with entry_cols[1]:
            st.info(signal.rationale)

        st.markdown("---")
        st.subheader("🔮 What-If Scenario Simulator")
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            scenario_pct = st.slider("Rate change (%)", -30, 30, 0, step=5)
        with col_sim2:
            scenario = api_client.run_scenario(
                origin_country, destination_port, selected_vessel_type,
                cargo_tonnes, scenario_pct,
            )
            st.metric("Base Cost", f"${scenario.base_total_cost:,.0f}")
            st.metric("Adjusted Cost", f"${scenario.adjusted_total_cost:,.0f}",
                       delta=f"${scenario.cost_impact:+,.0f}")

        st.markdown("---")
        st.subheader("⏸️ Idle Scenario Management")
        idle = api_client.get_idle_analysis(
            origin_country, destination_port, selected_vessel_type, cargo_tonnes,
        )

        idle_c1, idle_c2 = st.columns(2)
        with idle_c1:
            st.metric("Estimated Idle Days", f"{idle.estimated_idle_days:.0f} days/year")
            st.metric("Idle Cost", f"${idle.idle_cost_usd:,.0f}")
            if idle.low_demand_months:
                st.markdown("**Low-Demand Months:**")
                for m in idle.low_demand_months:
                    st.markdown(f"- {m}")
        with idle_c2:
            st.markdown("**Repositioning Suggestions:**")
            for s in idle.repositioning_suggestions:
                st.info(s)
            st.markdown("**Backhaul Opportunities:**")
            for b in idle.backhaul_opportunities:
                st.markdown(f"- {b}")


# ===== TAB 4: VESSEL OPTIMIZER =====
with tab4:
    st.subheader("Vessel Type Optimization")
    st.markdown(f"*{origin_port} ({origin_country}) → {destination_port} | {cargo_tonnes:,} MT*")

    if is_backend_online:
        rec_vessels = api_client.recommend_vessels(origin_country, destination_port, cargo_tonnes, origin_port)

        if rec_vessels.empty:
            st.error(f"No vessel type is feasible for {cargo_tonnes:,} MT at {destination_port}. Consider reducing cargo size or choosing a deeper-draft port.")
        else:
            best = rec_vessels.iloc[0]
            st.success(f"**Recommended:** {best['vessel_type']} (DWT: {best['dwt']:,}) — ${best['cost_per_tonne']:.2f}/ton voyage cost, {best['total_days']:.0f} days total")

            st.markdown("#### Feasible Vessel Comparison")
            display_cols = [
                "vessel_type", "dwt", "voyage_days", "load_days", "unload_days",
                "total_days", "num_voyages", "voyage_cost_usd", "cost_per_tonne",
            ]
            available_cols = [c for c in display_cols if c in rec_vessels.columns]
            display_df = rec_vessels[available_cols].rename(columns={
                "vessel_type": "Vessel Type",
                "dwt": "DWT",
                "voyage_days": "Sailing Days",
                "load_days": "Load Days",
                "unload_days": "Unload Days",
                "total_days": "Total Days",
                "num_voyages": "Voyages Needed",
                "voyage_cost_usd": "Voyage Cost ($)",
                "cost_per_tonne": "Cost/Tonne ($)",
            })
            st.dataframe(display_df.round(1), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Voyage Cost Breakdown")
        all_voyages = api_client.compare_all_voyages(origin_country, origin_port, destination_port, cargo_tonnes)
        if all_voyages:
            voyage_data = []
            for v in all_voyages:
                status = "✅" if (v.feasible_at_origin and v.feasible_at_destination) else "❌"
                voyage_data.append({
                    "Status": status,
                    "Vessel": v.vessel_type,
                    "Distance (NM)": v.distance_nm,
                    "Sailing Days": v.sailing_days,
                    "Load Days": v.load_days,
                    "Unload Days": v.unload_days,
                    "Total Days": v.total_voyage_days,
                    "Vessel Hire ($)": f"{v.vessel_hire_usd:,.0f}",
                    "Fuel Cost ($)": f"{v.fuel_cost_usd:,.0f}",
                    "Port Charges ($)": f"{v.port_charges_load_usd + v.port_charges_discharge_usd:,.0f}",
                    "Total Cost ($)": f"{v.total_cost_usd:,.0f}",
                    "Cost/Tonne ($)": v.cost_per_tonne,
                })
            st.dataframe(pd.DataFrame(voyage_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Port-Vessel Feasibility Matrix")
        feasibility_df = api_client.get_feasibility_matrix()
        if not feasibility_df.empty:
            matrix_display = feasibility_df.copy()
            for col in matrix_display.columns:
                if col != "port":
                    matrix_display[col] = matrix_display[col].apply(lambda x: "✅" if x else "❌")
            st.dataframe(matrix_display.rename(columns={"port": "Port"}), use_container_width=True, hide_index=True)


# ===== TAB 5: RISK DASHBOARD =====
with tab5:
    st.subheader("Risk Intelligence Dashboard")

    if is_backend_online:
        alerts = api_client.get_risk_alerts(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months,
        )

        st.markdown("#### 🔔 Active Alerts")
        for alert in alerts:
            if "⚠️" in alert or "HIGH" in alert:
                st.error(alert)
            elif "📈" in alert or "💰" in alert:
                st.warning(alert)
            elif "✅" in alert:
                st.success(alert)
            else:
                st.info(alert)

        st.markdown("---")
        st.subheader("Route Risk Assessment")
        risk_df = api_client.get_route_assessment(origin_country, selected_vessel_type, cargo_tonnes)
        if not risk_df.empty:
            risk_display = risk_df.rename(columns={
                "port": "Port",
                "avg_rate": "Avg Rate ($/ton)",
                "volatility": "Volatility (σ)",
                "alert_count": "Alert Count",
                "risk_level": "Risk Level",
            })
            risk_display["Risk Level"] = risk_display["Risk Level"].apply(
                lambda r: "🟢 Low" if r == "LOW" else ("🟡 Medium" if r == "MEDIUM" else "🔴 High")
            )
            st.dataframe(risk_display, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🌧️ Monsoon Disruption Calendar")
        monsoon_df = api_client.get_monsoon_calendar()
        if not monsoon_df.empty:
            m_display = monsoon_df.rename(columns={
                "port": "Port",
                "state": "State",
                "severity": "Monsoon Impact (Jun-Sep)",
                "action": "Recommended Action",
            })
            m_display["Monsoon Impact (Jun-Sep)"] = m_display["Monsoon Impact (Jun-Sep)"].apply(
                lambda s: "🔴 Severe" if s == "SEVERE" else ("🟡 Moderate" if s == "MODERATE" else "🟢 Mild")
            )
            st.dataframe(m_display, use_container_width=True, hide_index=True)


# ===== TAB 6: PORT INTELLIGENCE =====
with tab6:
    st.subheader("Indian East Coast Port Infrastructure")

    if is_backend_online:
        port_data = []
        for port_name, port_info in INDIAN_EAST_COAST_PORTS.items():
            port_data.append({
                "Port": port_name,
                "State": port_info["state"],
                "Max LOA (m)": port_info["max_loa_m"],
                "Max Beam (m)": port_info["max_beam_m"],
                "Max Draft (m)": port_info["max_draft_m"],
                "Handling (TPD)": f"{port_info['handling_tpd']:,}",
                "Annual Capacity (MT)": port_info["annual_capacity_mt"],
                "Berths": port_info["berths"],
                "Notes": port_info["notes"],
            })
        st.dataframe(pd.DataFrame(port_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("⚓ Draft Constraint Analysis")
        draft_comp = [{"Port": name, "Max Draft (m)": info["max_draft_m"]} for name, info in INDIAN_EAST_COAST_PORTS.items()]
        st.bar_chart(pd.DataFrame(draft_comp).set_index("Port"))

        st.subheader("📦 Cargo Handling Capacity")
        handling_comp = [{"Port": name, "Handling Rate (TPD)": info["handling_tpd"]} for name, info in INDIAN_EAST_COAST_PORTS.items()]
        st.bar_chart(pd.DataFrame(handling_comp).set_index("Port"))

        st.markdown("---")
        st.subheader("🌍 Origin Loading Ports")
        for country, ports in ORIGIN_PORTS.items():
            with st.expander(f"🏭 {country} ({len(ports)} ports)"):
                origin_data = []
                for pname, pinfo in ports.items():
                    origin_data.append({
                        "Port": pname,
                        "Max LOA (m)": pinfo["max_loa_m"],
                        "Max Draft (m)": pinfo["max_draft_m"],
                        "Handling (TPD)": f"{pinfo['handling_tpd']:,}",
                        "Commodity": pinfo.get("commodity", "Bulk"),
                    })
                st.dataframe(pd.DataFrame(origin_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🗺️ Sailing Distance Matrix (Nautical Miles)")
        dist_data = []
        for country, ports in SAILING_DISTANCES_NM.items():
            row = {"Origin": country}
            for port_name, nm in ports.items():
                row[port_name] = f"{nm:,}"
            dist_data.append(row)
        st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)


# ===== TAB 7: FINAL RESULT & ACTION PLAN =====
with tab7:
    st.markdown(
        "<h2 style='text-align: center; color: #a78bfa;'>✅ Final Result & Action Plan</h2>"
        "<p style='text-align: center; color: #8b8bcd; font-size: 1.05rem;'>"
        "Consolidated recommendation based on your inputs — ready for chartering execution</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if is_backend_online:
        final_forecast = api_client.get_forecast(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months, origin_port=origin_port,
        )
        final_entry = api_client.get_market_entry(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, forecast_months,
        )
        final_contract = api_client.compare_contracts(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, voyages_per_year,
        )
        final_rec = api_client.recommend_vessels(origin_country, destination_port, cargo_tonnes, origin_port)
        final_alerts = api_client.get_risk_alerts(
            origin_country, destination_port, selected_vessel_type,
            cargo_tonnes, months=forecast_months,
        )
        final_idle = api_client.get_idle_analysis(
            origin_country, destination_port, selected_vessel_type, cargo_tonnes,
        )
        final_voyage = api_client.get_voyage_cost(
            origin_country, origin_port, destination_port, selected_vessel_type, cargo_tonnes,
        )

        final_distance = SAILING_DISTANCES_NM.get(origin_country, {}).get(destination_port, 0)
        final_vessel_info = next((v for v in VESSEL_CATALOG if v["vessel_type"] == selected_vessel_type), None)

        action_color = {"BOOK NOW": "#10b981", "WAIT": "#f59e0b", "HEDGE": "#6366f1"}.get(final_entry.action, "#6366f1")
        action_emoji = {"BOOK NOW": "🟢", "WAIT": "🟡", "HEDGE": "🔵"}.get(final_entry.action, "🔵")
        risk_count = len([a for a in final_alerts if "✅" not in a])
        risk_level = "LOW" if risk_count <= 1 else ("MEDIUM" if risk_count <= 2 else "HIGH")
        risk_color = "#10b981" if risk_level == "LOW" else ("#f59e0b" if risk_level == "MEDIUM" else "#ef4444")

        st.markdown(
            f'<div style="text-align: center; padding: 28px 20px; '
            f'background: linear-gradient(135deg, rgba(30,30,80,0.85), rgba(20,20,60,0.95)); '
            f'border: 2px solid {action_color}; border-radius: 16px; margin-bottom: 24px;">'
            f'<span style="font-size: 2.4rem;">{action_emoji}</span><br>'
            f'<span style="font-size: 1.8rem; font-weight: 800; color: {action_color}; letter-spacing: 2px;">'
            f'{final_entry.action}</span><br>'
            f'<span style="color: #c0c0e0; font-size: 1.1rem;">Confidence: <strong>{final_entry.confidence}</strong> &nbsp;|&nbsp; '
            f'Risk Level: <span style="color: {risk_color}; font-weight: 700;">{risk_level}</span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### 🚢 Recommended Route & Vessel")
        rv1, rv2, rv3, rv4 = st.columns(4)
        with rv1:
            st.metric("Route", f"{origin_port} → {destination_port}")
        with rv2:
            st.metric("Distance", f"{final_distance:,} NM")
        with rv3:
            st.metric("Vessel Type", selected_vessel_type)
        with rv4:
            if final_vessel_info:
                sail_days = round(final_distance / (final_vessel_info["speed_knots"] * 24), 1)
                st.metric("Sailing Time", f"{sail_days} days")

        rv5, rv6, rv7, rv8 = st.columns(4)
        with rv5:
            st.metric("Cargo", f"{cargo_tonnes:,} MT")
        with rv6:
            if final_vessel_info:
                st.metric("Vessel DWT", f"{final_vessel_info['dwt']:,} MT")
        with rv7:
            if final_voyage:
                st.metric("Total Voyage Days", f"{final_voyage.total_voyage_days}")
        with rv8:
            if not final_rec.empty:
                st.metric("Feasible Vessels", f"{len(final_rec)} types")

        st.markdown("---")
        st.markdown("### 💰 Pricing & Contract Recommendation")
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.metric("Forecast Rate", f"${final_entry.current_rate:.2f}/ton")
        with pc2:
            per_voyage_cost = final_entry.current_rate * cargo_tonnes
            st.metric("Per Voyage Freight", f"${per_voyage_cost:,.0f}")
        with pc3:
            annual_cost = per_voyage_cost * voyages_per_year
            st.metric(f"Annual Cost ({voyages_per_year} voyages)", f"${annual_cost:,.0f}")
        with pc4:
            st.metric("Best Entry Window", final_entry.forecast_min_month)

        st.markdown("")
        strat_col1, strat_col2 = st.columns([2, 1])
        with strat_col1:
            st.success(
                f"**Recommended Contract Strategy:** {final_contract.recommended_strategy}\n\n"
                f"- Spot rate: ${final_contract.spot_avg_rate:.2f}/ton → "
                f"Contract rate: ${final_contract.long_term_avg_rate:.2f}/ton\n"
                f"- **Annual savings vs. spot: ${final_contract.savings_vs_spot:,.0f}**\n"
                f"- Based on {voyages_per_year} voyages × {cargo_tonnes:,} MT per voyage"
            )
        with strat_col2:
            savings_pct = (final_contract.savings_vs_spot / final_contract.spot_total_cost * 100) if final_contract.spot_total_cost > 0 else 0
            st.metric("Savings %", f"{savings_pct:.1f}%")
            st.metric("Savings (Annual)", f"${final_contract.savings_vs_spot:,.0f}")

        st.markdown("---")
        st.markdown("### 🧮 Voyage Economics")
        if final_voyage:
            ve1, ve2, ve3, ve4 = st.columns(4)
            with ve1:
                st.metric("Vessel Hire", f"${final_voyage.vessel_hire_usd:,.0f}")
            with ve2:
                st.metric("Fuel Cost", f"${final_voyage.fuel_cost_usd:,.0f}")
            with ve3:
                port_total = final_voyage.port_charges_load_usd + final_voyage.port_charges_discharge_usd
                st.metric("Port Charges", f"${port_total:,.0f}")
            with ve4:
                st.metric("Total Voyage Cost", f"${final_voyage.total_cost_usd:,.0f}")

            ve5, ve6, ve7, ve8 = st.columns(4)
            with ve5:
                st.metric("Cost per Tonne", f"${final_voyage.cost_per_tonne}")
            with ve6:
                st.metric("Load Time", f"{final_voyage.load_days} days")
            with ve7:
                st.metric("Unload Time", f"{final_voyage.unload_days} days")
            with ve8:
                total_delivered = final_entry.current_rate * cargo_tonnes + final_voyage.total_cost_usd
                st.metric("Total Delivered Cost", f"${total_delivered:,.0f}")

            st.markdown("#### 🧾 Final Pro-Forma Billing Summary")
            fb_col1, fb_col2, fb_col3 = st.columns(3)
            with fb_col1:
                st.metric("Estimated Subtotal", f"${final_voyage.total_cost_usd + per_voyage_cost:,.0f}")
            with fb_col2:
                billing_tax = (final_voyage.total_cost_usd + per_voyage_cost) * 0.05
                st.metric("Port Tax & Customs (5%)", f"${billing_tax:,.0f}")
            with fb_col3:
                net_billing_total = (final_voyage.total_cost_usd + per_voyage_cost) + billing_tax
                st.metric("Final Net Billing Total", f"${net_billing_total:,.0f}", help="Combined Ocean Freight + Voyage Expenses + Taxes")

            st.info("💡 Complete itemized Pro-Forma Invoice details, tax breakdown, and CSV export are available in the **🧾 Final Billing & Invoice Statement** tab.")
        else:
            st.warning("Voyage cost data unavailable for this route/vessel combination.")

        st.markdown("---")
        st.markdown("### ⚠️ Risk Summary")
        if risk_count == 0:
            st.success("✅ No significant risks identified. Market conditions are favorable for proceeding.")
        else:
            for alert in final_alerts:
                if "✅" not in alert:
                    st.warning(alert)

        if final_idle.estimated_idle_days > 0:
            st.info(
                f"⏸️ **Idle Impact:** Estimated {final_idle.estimated_idle_days:.0f} idle days/year "
                f"(cost: ${final_idle.idle_cost_usd:,.0f}). "
                f"Consider backhaul opportunities to offset: {', '.join(final_idle.backhaul_opportunities[:2])}"
            )

        st.markdown("---")
        st.markdown("### 📋 Recommended Next Steps")

        steps = []
        if final_entry.action == "BOOK NOW":
            steps.append({
                "step": "Initiate Charter Negotiations",
                "detail": f"Current market conditions are favorable. Begin negotiations for a "
                          f"**{final_contract.recommended_strategy.lower()}** immediately. "
                          f"Target rate: **${final_contract.long_term_avg_rate:.2f}/ton** or better.",
                "priority": "🔴 URGENT",
            })
        elif final_entry.action == "WAIT":
            steps.append({
                "step": "Monitor Market & Set Rate Alert",
                "detail": f"Rates are expected to dip to **${final_entry.forecast_min:.2f}/ton** in "
                          f"**{final_entry.forecast_min_month}**. Set a rate alert at "
                          f"${final_entry.forecast_min * 1.02:.2f}/ton and prepare to act when triggered.",
                "priority": "🟡 MEDIUM",
            })
        else:
            steps.append({
                "step": "Split Bookings Across Multiple Entry Points",
                "detail": f"Market outlook is mixed. Book **50%** of volume now at ${final_entry.current_rate:.2f}/ton "
                          f"and reserve **50%** for {final_entry.forecast_min_month} when rates may improve.",
                "priority": "🟡 MEDIUM",
            })

        steps.append({
            "step": f"Confirm {selected_vessel_type} Vessel Availability",
            "detail": f"Verify {selected_vessel_type} tonnage availability for the {origin_port} → {destination_port} route.",
            "priority": "🔴 HIGH",
        })

        steps.append({
            "step": f"Execute {final_contract.recommended_strategy}",
            "detail": f"Negotiate a multi-voyage contract for **{voyages_per_year} voyages** at "
                      f"**${final_contract.long_term_avg_rate:.2f}/ton**. This saves "
                      f"**${final_contract.savings_vs_spot:,.0f}/year** vs. individual spot bookings.",
            "priority": "🔴 HIGH",
        })

        for i, step in enumerate(steps, 1):
            priority_color = {"🔴 URGENT": "#ef4444", "🔴 HIGH": "#ef4444", "🟡 MEDIUM": "#f59e0b", "🟢 ADVISORY": "#10b981"}.get(step["priority"], "#8b8bcd")
            st.markdown(
                f'<div style="background: linear-gradient(135deg, rgba(30,30,80,0.7), rgba(20,20,60,0.8)); '
                f'border-left: 4px solid {priority_color}; border-radius: 8px; padding: 16px 20px; margin-bottom: 12px;">'
                f'<span style="color: #e0e0ff; font-size: 1.1rem; font-weight: 700;">Step {i}: {step["step"]}</span>'
                f'&nbsp;&nbsp;<span style="font-size: 0.8rem; color: {priority_color}; font-weight: 600;">{step["priority"]}</span>'
                f'<br><span style="color: #a0a0d0; font-size: 0.95rem;">{step["detail"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 📊 Decision Summary")
        summary_data = {
            "Parameter": [
                "Origin", "Destination", "Distance",
                "Vessel Type", "Cargo per Voyage", "Voyages per Year",
                "Forecast Rate", "Per Voyage Freight Cost", "Annual Freight Cost",
                "Contract Strategy", "Contract Rate", "Annual Savings vs. Spot",
                "Market Signal", "Best Entry Window", "Risk Level",
                "Estimated Idle Days/Year", "Idle Cost/Year",
            ],
            "Value": [
                f"{origin_port}, {origin_country}",
                f"{destination_port}, India",
                f"{final_distance:,} NM",
                selected_vessel_type,
                f"{cargo_tonnes:,} MT",
                str(voyages_per_year),
                f"${final_entry.current_rate:.2f}/ton",
                f"${per_voyage_cost:,.0f}",
                f"${annual_cost:,.0f}",
                final_contract.recommended_strategy,
                f"${final_contract.long_term_avg_rate:.2f}/ton",
                f"${final_contract.savings_vs_spot:,.0f} ({savings_pct:.1f}%)",
                f"{final_entry.action} ({final_entry.confidence})",
                final_entry.forecast_min_month,
                risk_level,
                f"{final_idle.estimated_idle_days:.0f}",
                f"${final_idle.idle_cost_usd:,.0f}",
            ],
        }
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 📥 Export Shipment Decision Report")
        st.markdown("Generate and download the full AI shipment analytics report directly from the FastAPI backend server.")

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            if is_backend_online:
                try:
                    csv_report_data = api_client.export_shipment_report({
                        "origin_country": origin_country,
                        "origin_port": origin_port,
                        "destination_country": destination_country,
                        "destination_port": destination_port,
                        "cargo_tonnes": cargo_tonnes,
                        "vessel_type": selected_vessel_type,
                        "forecast_months": forecast_months,
                        "voyages_per_year": voyages_per_year,
                    }, fmt="csv")
                    st.download_button(
                        label="📄 Download Full Report (CSV)",
                        data=csv_report_data,
                        file_name=f"Shipment_Report_{origin_port}_to_{destination_port}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as ex:
                    st.error(f"Error generating CSV report: {ex}")
            else:
                st.caption("Backend offline")

        with exp_col2:
            if is_backend_online:
                try:
                    import json
                    json_report_obj = api_client.export_shipment_report({
                        "origin_country": origin_country,
                        "origin_port": origin_port,
                        "destination_country": destination_country,
                        "destination_port": destination_port,
                        "cargo_tonnes": cargo_tonnes,
                        "vessel_type": selected_vessel_type,
                        "forecast_months": forecast_months,
                        "voyages_per_year": voyages_per_year,
                    }, fmt="json")
                    json_str = json.dumps(json_report_obj, indent=2)
                    st.download_button(
                        label="📦 Download Full Report (JSON)",
                        data=json_str,
                        file_name=f"Shipment_Report_{origin_port}_to_{destination_port}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                except Exception as ex:
                    st.error(f"Error generating JSON report: {ex}")
            else:
                st.caption("Backend offline")



# ===== TAB 8: WEB SCRAPER & LIVE MARKET INTELLIGENCE =====
with tab8:
    st.subheader("🌐 Real-Time Web Scraper & Shipping Market Intelligence")
    st.markdown("Scrape live Baltic Dry Indices, global bunker fuel prices, and target shipping webpage URLs to feed real-time intelligence into the AI decision engine.")

    if is_backend_online:
        col_scrape_trigger, col_scrape_info = st.columns([1, 2])
        with col_scrape_trigger:
            trigger_scrape = st.button("🕷️ Trigger Live Shipping Market Scrape", type="primary", use_container_width=True)
        with col_scrape_info:
            st.caption("Scrapes real-time freight market indices (BDI, BCI, BPI, BSI) and global bunker prices across Singapore, Fujairah, Rotterdam, and Houston hubs.")

        if trigger_scrape or "scraped_market_data" in st.session_state:
            if trigger_scrape:
                with st.spinner("Scraping live shipping portals and market feeds..."):
                    st.session_state.scraped_market_data = api_client.get_live_scraped_indices()

            s_data = st.session_state.get("scraped_market_data", {})
            if s_data:
                st.success(f"✅ Market data scraped successfully! Source: {s_data.get('market_indices', {}).get('scraped_source', 'Live Feed')} | Updated: {s_data.get('last_updated')}")

                st.markdown("#### 📊 Live Freight Market Indices")
                indices_dict = s_data.get("market_indices", {})
                idx_c1, idx_c2, idx_c3, idx_c4 = st.columns(4)
                with idx_c1:
                    bdi = indices_dict.get("baltic_dry_index", {})
                    st.metric("Baltic Dry Index (BDI)", f"{bdi.get('value', 0)} pts", delta=bdi.get("change"))
                with idx_c2:
                    bci = indices_dict.get("capesize_index", {})
                    st.metric("Capesize Index (BCI)", f"{bci.get('value', 0)} pts", delta=bci.get("change"))
                with idx_c3:
                    bpi = indices_dict.get("panamax_index", {})
                    st.metric("Panamax Index (BPI)", f"{bpi.get('value', 0)} pts", delta=bpi.get("change"))
                with idx_c4:
                    bsi = indices_dict.get("supramax_index", {})
                    st.metric("Supramax Index (BSI)", f"{bsi.get('value', 0)} pts", delta=bsi.get("change"))

                st.markdown("---")
                st.markdown("#### ⛽ Global Bunker Fuel Prices ($/MT)")
                bunker_dict = s_data.get("bunker_prices", {})
                bunker_df = pd.DataFrame(bunker_dict).T
                if not bunker_df.empty:
                    bunker_df = bunker_df.reset_index().rename(columns={"index": "Bunkering Hub", "change_usd": "24h Change ($)"})
                    st.dataframe(bunker_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔗 Custom Target Shipping Webpage Scraper")
        st.markdown("Enter any target shipping news, carrier tariff, or freight rate webpage URL to extract parsed data tables, rates, and article summaries.")

        target_url = st.text_input("Target Webpage URL", value="https://en.wikipedia.org/wiki/Baltic_Dry_Index", help="Enter any shipping website URL to scrape")
        scrape_url_btn = st.button("🔍 Scrape Target Webpage", type="secondary")

        if scrape_url_btn and target_url:
            with st.spinner(f"Scraping webpage: {target_url}..."):
                scraped_url_data = api_client.scrape_custom_url(target_url)
                st.session_state.scraped_url_result = scraped_url_data

        url_res = st.session_state.get("scraped_url_result", {})
        if url_res:
            if url_res.get("status") == "success":
                st.success(f"✅ Webpage Scraped: **{url_res.get('page_title')}**")
                st.markdown(f"**URL:** `{url_res.get('url')}` | **Scraped At:** {url_res.get('scraped_at')}")

                if url_res.get("meta_description"):
                    st.info(f"**Meta Summary:** {url_res.get('meta_description')}")

                if url_res.get("detected_freight_rates"):
                    st.markdown("#### 💵 Extracted Pricing Figures & Rates ($/ton)")
                    rates = url_res.get("detected_freight_rates", [])
                    st.write([f"${r:,.2f}" for r in rates])

                if url_res.get("summary_text"):
                    st.markdown("#### 📝 Article Preview & Text Summary")
                    st.write(url_res.get("summary_text"))

                tables = url_res.get("tables", [])
                if tables:
                    st.markdown(f"#### 📋 Extracted Data Tables ({len(tables)} found)")
                    for tbl in tables:
                        st.caption(tbl.get("table_id"))
                        st.dataframe(pd.DataFrame(tbl.get("rows", [])), use_container_width=True, hide_index=True)

                st.markdown("---")
                if st.button("🤖 Ingest Scraped Data into AI Forecasting Model", type="primary"):
                    with st.spinner("Ingesting scraped data into ML model state..."):
                        ingest_res = api_client.ingest_scraped_data(url_res)
                        st.success(f"🎉 {ingest_res.get('message')}")
            else:
                st.error(f"❌ Scraping Failed: {url_res.get('error_message')}")
    else:
        st.warning("⚠️ Please start the FastAPI backend server to run the Web Scraper.")


# ===== TAB 9: LINKED LIST VOYAGE NAVIGATOR =====
with tab9:
    st.subheader("🔗 Doubly Linked List Voyage Sequence Navigator")
    st.markdown("Step-by-step voyage leg navigation using **Doubly Linked List Algorithms** (`Node.prev ◄──► Node ◄──► Node.next`). Models port loading, ocean transit legs, bunkering hubs, and destination discharge sequentially.")

    # Header Tile & Feature Banner
    st.markdown(
        f'<div style="padding: 18px 24px; background: linear-gradient(135deg, rgba(45,30,85,0.85), rgba(25,20,65,0.9)); '
        f'border-left: 6px solid #8b5cf6; border-radius: 12px; margin-bottom: 20px;">'
        f'<span style="font-size: 1.25rem; font-weight: 700; color: #a78bfa;">🔗 Doubly Linked List Architecture: Head ◄──► Transit ◄──► Tail</span><br>'
        f'<span style="color: #c0c0e0; font-size: 0.95rem;">Doubly-linked pointer traversal provides bidirectional voyage auditing, dynamic waypoint insertion, and leg-by-leg cost & risk aggregation.</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if is_backend_online:
        # Build or get current linked list state
        if "linked_list_nodes" not in st.session_state or st.button("🔄 Rebuild Route Linked List", type="secondary"):
            with st.spinner("Building Doubly Linked List for selected route..."):
                res_ll = api_client.build_route_linked_list(
                    origin_country=origin_country,
                    origin_port=origin_port,
                    destination_country=destination_country,
                    destination_port=destination_port,
                    vessel_type=selected_vessel_type,
                    cargo_tonnes=cargo_tonnes,
                )
                st.session_state.linked_list_nodes = res_ll.get("nodes", [])
                st.session_state.linked_list_summary = res_ll.get("summary", {})
                st.session_state.linked_list_active_index = 0

        nodes = st.session_state.get("linked_list_nodes", [])
        summary = st.session_state.get("linked_list_summary", {})

        if nodes:
            # 1. Summary Cards from Linked List
            st.markdown("#### 📊 Aggregated Linked List Route Metrics")
            ll_c1, ll_c2, ll_c3, ll_c4 = st.columns(4)
            with ll_c1:
                st.metric("Total Linked Nodes", f"{summary.get('total_nodes', len(nodes))} nodes")
            with ll_c2:
                st.metric("Total Route Distance", f"{summary.get('total_distance_nm', 0):,} NM")
            with ll_c3:
                st.metric("Total Voyage Days", f"{summary.get('total_voyage_days', 0):.1f} days")
            with ll_c4:
                st.metric("Aggregated Voyage Cost", f"${summary.get('total_cost_usd', 0):,.0f}")

            st.markdown("---")
            st.markdown("#### 🎴 Doubly Linked List Node Sequence Visualizer")

            # Render sequence badges with pointer arrows
            sequence_html = '<div style="display: flex; align-items: center; gap: 8px; overflow-x: auto; padding: 12px 0;">'
            for idx, nd in enumerate(nodes):
                is_active = (idx == st.session_state.get("linked_list_active_index", 0))
                badge_bg = "#8b5cf6" if is_active else "rgba(40,40,90,0.8)"
                border_style = "2px solid #a78bfa" if is_active else "1px solid rgba(100,100,160,0.4)"

                sequence_html += (
                    f'<div style="background: {badge_bg}; border: {border_style}; border-radius: 8px; padding: 10px 14px; min-width: 160px; text-align: center;">'
                    f'<div style="font-size: 0.75rem; color: #d0d0ff;">Node {idx+1} ({nd["node_type"]})</div>'
                    f'<div style="font-size: 0.95rem; font-weight: 700; color: #ffffff;">{nd["location_name"]}</div>'
                    f'</div>'
                )
                if idx < len(nodes) - 1:
                    sequence_html += '<div style="font-size: 1.3rem; color: #a78bfa; font-weight: bold;">◄──►</div>'
            sequence_html += '</div>'
            st.markdown(sequence_html, unsafe_allow_html=True)

            # Node Selection Slider / Traversal
            active_idx = st.slider(
                "Navigate Linked List Node",
                min_value=0,
                max_value=len(nodes) - 1,
                value=min(st.session_state.get("linked_list_active_index", 0), len(nodes) - 1),
                format="Node %d",
            )
            st.session_state.linked_list_active_index = active_idx
            curr_node = nodes[active_idx]

            # Detailed Card for Selected Node
            st.markdown("---")
            st.markdown(f"### 📍 Selected Node Details: {curr_node.get('title')}")

            col_ptr1, col_ptr2, col_ptr3 = st.columns(3)
            with col_ptr1:
                prev_str = f"Node {active_idx} ({nodes[active_idx-1]['location_name']})" if active_idx > 0 else "None (HEAD)"
                st.info(f"**◀ Prev Pointer (`prev_node`):** {prev_str}")
            with col_ptr2:
                st.success(f"**📍 Current Node ID:** `{curr_node.get('node_id')}`")
            with col_ptr3:
                next_str = f"Node {active_idx+2} ({nodes[active_idx+1]['location_name']})" if active_idx < len(nodes) - 1 else "None (TAIL)"
                st.info(f"**Next Pointer (`next_node`): ▶** {next_str}")

            nc1, nc2, nc3, nc4 = st.columns(4)
            with nc1:
                st.metric("Location / Port", curr_node.get("location_name"))
            with nc2:
                st.metric("Country", curr_node.get("country"))
            with nc3:
                st.metric("Distance Leg", f"{curr_node.get('distance_nm', 0):,} NM")
            with nc4:
                st.metric("Estimated Cost", f"${curr_node.get('cost_usd', 0):,.0f}")

            # Vessel & Destination Specifics inside Node
            st.markdown("##### 🚢 Node Vessel & Port Infrastructure Attributes")
            details = curr_node.get("details", {})
            if details:
                d_cols = st.columns(len(details))
                for d_idx, (k, v) in enumerate(details.items()):
                    with d_cols[d_idx]:
                        st.caption(k.replace("_", " ").title())
                        st.markdown(f"**{v}**")

            # Interactive Linked List Operations (Insert & Delete)
            st.markdown("---")
            st.markdown("#### 🛠️ Linked List Dynamic Operations (Insert & Remove Node)")

            col_ins, col_del = st.columns(2)
            with col_ins:
                st.markdown("##### ➕ Insert Waypoint Node")
                ins_title = st.text_input("New Node Title", value="Bunker / Waypoint Refueling")
                ins_location = st.text_input("Location Name", value="Port Said / Suez Canal")
                ins_cost = st.number_input("Est. Leg Cost ($)", value=35000.0, step=5000.0)

                if st.button(f"➕ Insert Node After {curr_node.get('location_name')}", type="primary"):
                    res_ins = api_client.insert_route_node(
                        target_node_id=curr_node.get("node_id"),
                        new_node_title=ins_title,
                        location_name=ins_location,
                        country="Transit Hub",
                        vessel_type=selected_vessel_type,
                        distance_nm=300.0,
                        cost_usd=ins_cost,
                        current_nodes=nodes,
                    )
                    if res_ins.get("status") == "success":
                        st.session_state.linked_list_nodes = res_ins.get("nodes", [])
                        st.session_state.linked_list_summary = res_ins.get("summary", {})
                        st.success(f"✅ Inserted new node after `{curr_node.get('node_id')}`!")
                        st.rerun()

            with col_del:
                st.markdown("##### 🗑️ Delete Node")
                st.warning(f"Target for removal: Node `{curr_node.get('node_id')}` ({curr_node.get('location_name')})")
                if len(nodes) <= 2:
                    st.caption("Cannot delete node. Linked List must maintain at least 2 nodes.")
                else:
                    if st.button(f"🗑️ Delete Node {curr_node.get('location_name')}", type="secondary"):
                        res_del = api_client.remove_route_node(
                            node_id=curr_node.get("node_id"),
                            current_nodes=nodes,
                        )
                        if res_del.get("status") == "success":
                            st.session_state.linked_list_nodes = res_del.get("nodes", [])
                            st.session_state.linked_list_summary = res_del.get("summary", {})
                            st.session_state.linked_list_active_index = max(0, active_idx - 1)
                            st.success(f"✅ Removed node `{curr_node.get('node_id')}`!")
                            st.rerun()
    else:
        st.warning("⚠️ Please start the FastAPI backend server to run the Linked List Voyage Navigator.")


# ===== TAB 10: FINAL BILLING & INVOICE STATEMENT =====
with tab10:
    st.markdown(
        "<h2 style='text-align: center; color: #38bdf8;'>🧾 Itemized Final Billing & Charter Invoice</h2>"
        "<p style='text-align: center; color: #94a3b8; font-size: 1.05rem;'>"
        "Pro-forma maritime billing statement, line-item voyage charges, taxes, discounts, and payment export</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if is_backend_online:
        current_rate_val = 25.0
        try:
            fe = api_client.get_market_entry(origin_country, destination_port, selected_vessel_type, cargo_tonnes)
            if hasattr(fe, "current_rate"):
                current_rate_val = fe.current_rate
        except Exception:
            pass

        disc_val = 0.0
        try:
            fc = api_client.compare_contracts(origin_country, destination_port, selected_vessel_type, cargo_tonnes)
            if hasattr(fc, "recommended_strategy") and "Long-term" in fc.recommended_strategy:
                disc_val = 5.0
        except Exception:
            pass

        bill_res = api_client.get_billing_statement(
            origin_country=origin_country,
            origin_port=origin_port,
            destination_port=destination_port,
            vessel_type=selected_vessel_type,
            cargo_tonnes=cargo_tonnes,
            spot_rate_per_ton=current_rate_val,
            discount_pct=disc_val,
            tax_pct=5.0,
        )

        b_summary = bill_res.get("billing_summary", {})
        inv_no = bill_res.get("invoice_number", "INV-2026-FRT-9842")

        if b_summary:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(30,41,59,0.95)); '
                f'border: 1px solid #38bdf8; border-radius: 12px; padding: 24px; margin-bottom: 24px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px;">'
                f'<div><h3 style="margin: 0; color: #f8fafc;">🚢 MARITIME CHARTER PRO-FORMA INVOICE</h3>'
                f'<span style="color: #38bdf8; font-weight: 600;">Reference: {inv_no}</span></div>'
                f'<div style="text-align: right;"><span style="background: #10b981; color: #ffffff; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">'
                f'{b_summary.get("payment_status", "PRO-FORMA GENERATED")}</span><br>'
                f'<span style="color: #94a3b8; font-size: 0.85rem;">Date: {date.today().strftime("%d %b %Y")}</span></div></div>'
                f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 16px;">'
                f'<div><span style="color: #94a3b8; font-size: 0.85rem;">Loading Port</span><br><strong style="color: #e2e8f0;">{b_summary.get("origin")}</strong></div>'
                f'<div><span style="color: #94a3b8; font-size: 0.85rem;">Discharge Port</span><br><strong style="color: #e2e8f0;">{b_summary.get("destination")}</strong></div>'
                f'<div><span style="color: #94a3b8; font-size: 0.85rem;">Vessel Tonnage</span><br><strong style="color: #e2e8f0;">{b_summary.get("vessel_type")} ({b_summary.get("cargo_tonnes"):,} MT)</strong></div>'
                f'<div><span style="color: #94a3b8; font-size: 0.85rem;">Net Unit Rate</span><br><strong style="color: #38bdf8;">${b_summary.get("cost_per_ton_usd"):.2f} / MT</strong></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown("### 📋 Itemized Charter Cost Breakdown")
            items = b_summary.get("line_items", [])
            df_bill = pd.DataFrame(items)
            if not df_bill.empty:
                df_bill["amount_usd"] = df_bill["amount_usd"].apply(lambda x: f"${x:,.2f}")
                df_bill.columns = ["Billing Item Description", "Basis / Computation Notes", "Amount (USD)"]
                st.table(df_bill)

            st.markdown("---")
            b_col1, b_col2 = st.columns([2, 1])
            with b_col1:
                st.info(
                    f"💡 **Contract Discount Applied:** {b_summary.get('discount_pct')}% discount applied "
                    f"(-${b_summary.get('discount_amount_usd'):,.2f}).\n\n"
                    f"Port Charges & Statutory Customs Tax included at {b_summary.get('tax_pct')}% (+${b_summary.get('tax_amount_usd'):,.2f})."
                )
            with b_col2:
                st.markdown(
                    f'<div style="background: rgba(15,23,42,0.8); border: 1px solid #10b981; border-radius: 12px; padding: 20px; text-align: right;">'
                    f'<span style="color: #94a3b8; font-size: 0.9rem;">SUBTOTAL</span><br>'
                    f'<span style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">${b_summary.get("subtotal_usd"):,.2f}</span><br>'
                    f'<span style="color: #10b981; font-size: 0.85rem;">DISCOUNT ({b_summary.get("discount_pct")}%)</span><br>'
                    f'<span style="font-size: 1rem; color: #10b981;">-${b_summary.get("discount_amount_usd"):,.2f}</span><br>'
                    f'<span style="color: #f59e0b; font-size: 0.85rem;">TAXES & PORT DUES ({b_summary.get("tax_pct")}%)</span><br>'
                    f'<span style="font-size: 1rem; color: #f59e0b;">+${b_summary.get("tax_amount_usd"):,.2f}</span><br>'
                    f'<hr style="border-color: #334155; margin: 12px 0;">'
                    f'<span style="color: #38bdf8; font-size: 0.9rem; font-weight: 700;">FINAL NET PAYABLE</span><br>'
                    f'<span style="font-size: 1.8rem; font-weight: 800; color: #10b981;">${b_summary.get("grand_total_usd"):,.2f} USD</span><br>'
                    f'<span style="color: #94a3b8; font-size: 0.95rem;">(approx. ₹{b_summary.get("grand_total_inr"):,.0f} INR)</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### 📄 Official Human-Readable Pro-Forma Invoice Document")
            formatted_txt = b_summary.get("formatted_text_invoice", "")
            if formatted_txt:
                st.code(formatted_txt, language="text")

            st.markdown("### 📥 Download Official Invoice Statement")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    label="📄 Download Official Statement (TXT)",
                    data=formatted_txt.encode("utf-8") if formatted_txt else b"",
                    file_name=f"Official_Invoice_{inv_no}.txt",
                    mime="text/plain",
                    type="primary",
                    use_container_width=True,
                )
            with dl_col2:
                inv_csv = df_bill.to_csv(index=False).encode('utf-8') if not df_bill.empty else b""
                st.download_button(
                    label="📊 Download Line Items (CSV)",
                    data=inv_csv,
                    file_name=f"ProForma_Invoice_{inv_no}.csv",
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True,
                )
    else:
        st.warning("⚠️ Please start the FastAPI backend server to view the live Final Billing & Invoice statement.")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #6b6b9e; font-size: 0.85rem;'>"
    "AI Freight Forecasting Decision Center • Connected via FastAPI REST Backend Server</p>",
    unsafe_allow_html=True,
)
