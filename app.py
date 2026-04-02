import streamlit as st
from login import render_login_page, render_admin_panel
from carboo_coach import render_coach
from carbomax import render_carbomax
from raceprep import render_raceprep
from optimeal import render_optimeal
from carboo_chat import render_chatbot   # ← nieuw

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

/* Chat FAB knop — klein en rechtsonder */
div[data-testid="stButton"] button[kind="secondary"][data-test="chat_fab_btn"] {
    position: fixed !important;
    bottom: 24px !important;
    right: 24px !important;
    width: 50px !important;
    height: 50px !important;
    border-radius: 50% !important;
    background: #f97316 !important;
    color: white !important;
    font-size: 20px !important;
    padding: 0 !important;
    box-shadow: 0 4px 16px rgba(249,115,22,0.45) !important;
    z-index: 9999 !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in [
    ("logged_in", False),
    ("current_user", None),
    ("module", "menu"),
    ("chat_open", False),
    ("chat_messages", []),
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
CARBOO_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            background:#1e293b;border-radius:14px;padding:14px 22px;margin-bottom:18px;
            border:1px solid #334155">
  <div style="font-size:1.7rem;font-weight:900;letter-spacing:3px;color:#f8fafc">
    CAR<span style="color:#f97316">BOO</span>
  </div>
  <div style="font-size:0.82rem;color:#64748b">
    Ingelogd als <b style="color:#f8fafc">{naam}</b>
    {'&nbsp;&nbsp;<span style="background:#f97316;color:white;border-radius:4px;padding:1px 7px;font-size:0.72rem">ADMIN</span>' if is_admin else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# ─── NAVIGATIE / MODULE ROUTING ───────────────────────────────────────────────
module = st.session_state.module

if module == "menu":
    st.markdown(f"<div style='font-size:1.1rem;color:#94a3b8;margin-bottom:20px'>Welkom, <b style='color:#f8fafc'>{naam}</b> 👋 — Kies een module:</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏆 Carboo Coach\nRace Nutrition Wizard", key="btn_coach"):
            st.session_state.module = "coach"
            st.rerun()
        if st.button("🧪 CarboMax\nCarboloading Calculator", key="btn_carbomax"):
            st.session_state.module = "carbomax"
            st.rerun()
    with c2:
        if st.button("🗓 RacePrep\nWedstrijd Voorbereiding", key="btn_raceprep"):
            st.session_state.module = "raceprep"
            st.rerun()
        if st.button("🥗 OptiMeal\nMaaltijdoptimalisatie", key="btn_optimeal"):
            st.session_state.module = "optimeal"
            st.rerun()

    if is_admin:
        st.markdown("---")
        if st.button("⚙️ Admin Panel", key="btn_admin"):
            st.session_state.module = "admin"
            st.rerun()

    # Uitloggen
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Uitloggen", key="btn_logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

elif module == "coach":
    render_coach()

elif module == "carbomax":
    render_carbomax()

elif module == "raceprep":
    render_raceprep()

elif module == "optimeal":
    render_optimeal()

elif module == "admin":
    render_admin_panel()

# ─── CHATBOT — altijd zichtbaar als ingelogd ──────────────────────────────────
render_chatbot()
