import streamlit as st
from data import FOOD_DB, MOMENT_CONFIGS, RACE_PRODUCTS, BOOST_TIPS
from carbomax import render_carbomax
from raceprep import render_raceprep
from optimeal import render_optimeal

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NutriFlow Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL STYLES ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0f1e;
    color: #f8fafc;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* App background */
.stApp {
    background: #0a0f1e;
}

/* Main container */
.block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

/* Brand header */
.brand-header {
    text-align: center;
    padding: 20px 0 10px 0;
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 4px;
    color: #f8fafc;
    cursor: pointer;
}
.brand-header span { color: #f97316; }

/* Module tiles */
.tile-card {
    background: #1e293b;
    border-radius: 16px;
    padding: 50px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    border-bottom: 5px solid transparent;
}
.tile-card:hover { opacity: 0.85; }

/* Metric card */
.metric-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    margin-bottom: 10px;
}

/* Section header */
.section-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #f97316;
    border-bottom: 2px solid #334155;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

/* Input labels */
label { color: #94a3b8 !important; font-size: 0.78rem !important; text-transform: uppercase; font-weight: 700 !important; }

/* Buttons */
.stButton > button {
    background: #f97316;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 800;
    font-size: 1rem;
    padding: 14px;
    width: 100%;
    cursor: pointer;
}
.stButton > button:hover { background: #ea6c0a; border: none; color: white; }

/* Inputs */
.stNumberInput input, .stTextInput input, .stSelectbox select, .stTimeInput input {
    background: #0f172a !important;
    color: white !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #0a0f1e; gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #1e293b;
    color: #94a3b8;
    border-radius: 8px 8px 0 0;
    font-weight: 700;
    border: none;
    padding: 10px 30px;
}
.stTabs [aria-selected="true"] { background: #f97316 !important; color: white !important; }

/* Cards binnen modules */
.meal-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
}
.meal-card-title {
    color: #f97316;
    font-weight: 800;
    font-size: 0.85rem;
    text-transform: uppercase;
    margin-bottom: 10px;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 6px;
}

/* Result cards */
.result-ok {
    background: #f0fdf4;
    border-left: 5px solid #22c55e;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
    color: #1e293b;
}
.result-low {
    background: #fef2f2;
    border-left: 5px solid #ef4444;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
    color: #1e293b;
}
.boost-tip {
    background: #fee2e2;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: #991b1b;
    margin-top: 6px;
}

/* Timeline blocks */
.timeline-block {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
    color: #1e293b;
}
.timeline-uur {
    font-weight: 900;
    font-size: 0.95rem;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 5px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
}
.timeline-row {
    font-size: 0.85rem;
    margin-bottom: 6px;
    display: flex;
    gap: 10px;
}
.min-label {
    color: #3b82f6;
    font-weight: 700;
    min-width: 45px;
}

/* Alert banners */
.alert-orange {
    background: #fff7ed;
    border-left: 5px solid #f97316;
    padding: 12px 16px;
    border-radius: 8px;
    color: #9a3412;
    font-size: 0.85rem;
    margin-bottom: 12px;
}
.alert-red {
    background: #fef2f2;
    border-left: 5px solid #ef4444;
    padding: 12px 16px;
    border-radius: 8px;
    color: #991b1b;
    font-size: 0.85rem;
    margin-bottom: 12px;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: #0f172a !important;
    border-color: #334155 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "module" not in st.session_state:
    st.session_state.module = "menu"

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown('<div class="brand-header">NUTRI<span>FLOW</span> <span style="font-size:0.5em;color:#64748b;">PRO</span></div>', unsafe_allow_html=True)

# ─── BACK BUTTON ─────────────────────────────────────────────────────────────
if st.session_state.module != "menu":
    if st.button("← TERUG NAAR MENU", key="back_btn"):
        st.session_state.module = "menu"
        st.rerun()
    st.markdown("<hr style='border-color:#1e293b; margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

# ─── MAIN MENU ────────────────────────────────────────────────────────────────
if st.session_state.module == "menu":
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="tile-card" style="border-bottom-color: #f97316;">
            <div style="font-size:2rem; margin-bottom:10px;">🍝</div>
            <h2 style="color:#f8fafc; font-weight:900; letter-spacing:2px;">CARBOMAX</h2>
            <p style="color:#64748b; font-size:0.8rem; margin-top:8px;">2-daags koolhydratenplan op basis van gewicht & wedstrijdduur</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("OPEN CARBOMAX", key="open_carbomax"):
            st.session_state.module = "carbomax"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="tile-card" style="border-bottom-color: #3b82f6;">
            <div style="font-size:2rem; margin-bottom:10px;">🏁</div>
            <h2 style="color:#f8fafc; font-weight:900; letter-spacing:2px;">RACEPREP</h2>
            <p style="color:#64748b; font-size:0.8rem; margin-top:8px;">Slim raceplan op uur-basis met voeding & hydratatieschema</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("OPEN RACEPREP", key="open_raceprep"):
            st.session_state.module = "raceprep"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="tile-card" style="border-bottom-color: #22c55e;">
            <div style="font-size:2rem; margin-bottom:10px;">🥗</div>
            <h2 style="color:#f8fafc; font-weight:900; letter-spacing:2px;">OPTIMEAL</h2>
            <p style="color:#64748b; font-size:0.8rem; margin-top:8px;">Optimaliseer je dagelijkse voeding rondom training</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("OPEN OPTIMEAL", key="open_optimeal"):
            st.session_state.module = "optimeal"
            st.rerun()

# ─── MODULES ─────────────────────────────────────────────────────────────────
elif st.session_state.module == "carbomax":
    render_carbomax()

elif st.session_state.module == "raceprep":
    render_raceprep()

elif st.session_state.module == "optimeal":
    render_optimeal()
