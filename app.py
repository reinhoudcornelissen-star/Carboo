import streamlit as st
from login import render_login_page, render_admin_panel
from carboo_coach import render_coach
from carbomax import render_carbomax
from raceprep import render_raceprep
from optimeal import render_optimeal

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carboo — Race Nutrition",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL STYLES ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0a0f1e; color: #f8fafc; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp { background: #0a0f1e; }
.block-container { padding-top: 1.5rem; max-width: 1200px; }

/* Brand */
.brand-header { text-align:center; padding:20px 0 10px 0; font-size:2.2rem; font-weight:900; letter-spacing:4px; }
.brand-header span { color: #f97316; }

/* Buttons */
.stButton > button { background:#f97316; color:white; border:none; border-radius:10px; font-weight:800; font-size:1rem; padding:14px; width:100%; }
.stButton > button:hover { background:#ea6c0a; border:none; color:white; }
.stButton > button[kind="secondary"] { background:#1e293b; color:#f8fafc; border:1px solid #334155; }
.stButton > button[kind="secondary"]:hover { background:#334155; border:1px solid #475569; }

/* Inputs */
.stNumberInput input, .stTextInput input, .stSelectbox > div > div, .stTimeInput input {
    background: #0f172a !important; color: white !important; border: 1px solid #334155 !important; border-radius: 8px !important;
}
label { color: #94a3b8 !important; font-size: 0.78rem !important; text-transform: uppercase; font-weight: 700 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#0a0f1e; gap:8px; }
.stTabs [data-baseweb="tab"] { background:#1e293b; color:#94a3b8; border-radius:8px 8px 0 0; font-weight:700; border:none; padding:10px 30px; }
.stTabs [aria-selected="true"] { background:#f97316 !important; color:white !important; }

/* Meal cards */
.meal-card { background:#0f172a; border:1px solid #334155; border-radius:12px; padding:18px; margin-bottom:12px; }
.meal-card-title { color:#f97316; font-weight:800; font-size:0.85rem; text-transform:uppercase; margin-bottom:10px; border-bottom:1px solid #1e293b; padding-bottom:6px; }
.section-title { font-size:1.4rem; font-weight:800; color:#f97316; border-bottom:2px solid #334155; padding-bottom:8px; margin-bottom:20px; }

/* Results */
.result-ok { background:#f0fdf4; border-left:5px solid #22c55e; border-radius:8px; padding:14px; margin-bottom:10px; color:#1e293b; }
.result-low { background:#fef2f2; border-left:5px solid #ef4444; border-radius:8px; padding:14px; margin-bottom:10px; color:#1e293b; }
.boost-tip { background:#fee2e2; border-radius:6px; padding:8px 12px; font-size:0.8rem; color:#991b1b; margin-top:6px; }
.metric-box { background:#1e293b; border:1px solid #334155; border-radius:12px; padding:18px; text-align:center; margin-bottom:10px; }

/* Timeline */
.timeline-block { background:#f8fafc; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; color:#1e293b; }
.timeline-uur { font-weight:900; font-size:0.95rem; border-bottom:2px solid #3b82f6; padding-bottom:5px; margin-bottom:10px; display:flex; justify-content:space-between; }
.timeline-row { font-size:0.85rem; margin-bottom:6px; display:flex; gap:10px; }
.min-label { color:#3b82f6; font-weight:700; min-width:45px; }

/* Alerts */
.alert-orange { background:#fff7ed; border-left:5px solid #f97316; padding:12px 16px; border-radius:8px; color:#9a3412; font-size:0.85rem; margin-bottom:12px; }
.alert-red { background:#fef2f2; border-left:5px solid #ef4444; padding:12px 16px; border-radius:8px; color:#991b1b; font-size:0.85rem; margin-bottom:12px; }

/* Selectbox dropdown */
div[data-baseweb="select"] > div { background:#0f172a !important; border-color:#334155 !important; color:white !important; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in [
    ("logged_in", False),
    ("current_user", None),
    ("module", "menu"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── NIET INGELOGD → LOGIN PAGINA ────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login_page()
    st.stop()

# ─── INGELOGD ─────────────────────────────────────────────────────────────────
user = st.session_state.current_user
naam = user.get("name", "Atleet")
is_admin = user.get("role") == "admin"

# HEADER
CARBOO_AVATAR = "data:image/png;base64,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"

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:10px 20px; background:#0f172a; border-radius:12px; margin-bottom:20px; border:1px solid #1e293b;">
    <div style="display:flex; align-items:center; gap:12px;">
        <img src="{CARBOO_AVATAR}" style="width:40px; height:40px; border-radius:50%; border:2px solid #f97316;">
        <span style="font-size:1.4rem; font-weight:900; letter-spacing:3px; color:#f8fafc;">CARB<span style="color:#f97316;">OO</span></span>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
        <span style="color:#94a3b8; font-size:0.85rem;">👤 {naam}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── LOGOUT BUTTON ────────────────────────────────────────────────────────────
col_spacer, col_logout = st.columns([6, 1])
with col_logout:
    if st.button("🚪 Uitloggen", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ─── MODULE ROUTER ────────────────────────────────────────────────────────────
module = st.session_state.module

if module == "menu":
    # ── MAIN MENU ──────────────────────────────────────────────────────────────
    st.markdown("<div class='brand-header'>CARB<span>OO</span> RACE NUTRITION</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; margin-bottom:30px;'>Kies een module om te starten</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='meal-card' style='text-align:center; cursor:pointer;'>
            <div style='font-size:2.5rem; margin-bottom:10px;'>🤖</div>
            <div class='meal-card-title'>CARBOO COACH</div>
            <p style='color:#64748b; font-size:0.85rem;'>Persoonlijk voedingsplan via interactieve wizard</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Coach →", key="btn_coach"):
            st.session_state.module = "coach"
            st.rerun()

    with col2:
        st.markdown("""
        <div class='meal-card' style='text-align:center; cursor:pointer;'>
            <div style='font-size:2.5rem; margin-bottom:10px;'>🍝</div>
            <div class='meal-card-title'>CARBOLOADING</div>
            <p style='color:#64748b; font-size:0.85rem;'>Bereken je carboloading schema voor race dag</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Carboloading →", key="btn_carbomax"):
            st.session_state.module = "carbomax"
            st.rerun()

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""
        <div class='meal-card' style='text-align:center; cursor:pointer;'>
            <div style='font-size:2.5rem; margin-bottom:10px;'>🗓️</div>
            <div class='meal-card-title'>RACEPLAN</div>
            <p style='color:#64748b; font-size:0.85rem;'>Voedingsplanning rondom jouw wedstrijd</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Raceplan →", key="btn_raceprep"):
            st.session_state.module = "raceprep"
            st.rerun()

    with col4:
        st.markdown("""
        <div class='meal-card' style='text-align:center; cursor:pointer;'>
            <div style='font-size:2.5rem; margin-bottom:10px;'>🏁</div>
            <div class='meal-card-title'>RACE DAG</div>
            <p style='color:#64748b; font-size:0.85rem;'>Optimale voeding op de wedstrijddag zelf</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Race Dag →", key="btn_optimeal"):
            st.session_state.module = "optimeal"
            st.rerun()

    if is_admin:
        st.markdown("---")
        if st.button("⚙️ Admin Paneel", key="btn_admin"):
            st.session_state.module = "admin"
            st.rerun()

elif module == "coach":
    render_coach(st.session_state.current_user)   # ← FIX APPLIED

elif module == "carbomax":
    render_carbomax(st.session_state.current_user)

elif module == "raceprep":
    render_raceprep(st.session_state.current_user)

elif module == "optimeal":
    render_optimeal(st.session_state.current_user)

elif module == "admin":
    if is_admin:
        render_admin_panel()
    else:
        st.error("Geen toegang.")
        st.session_state.module = "menu"
        st.rerun()
