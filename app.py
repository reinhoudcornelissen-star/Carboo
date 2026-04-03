import streamlit as st
import streamlit.components.v1
from login import render_login_page, render_admin_panel
from carboo_coach import render_coach
from carbomax import render_carbomax
from raceprep import render_raceprep
from optimeal import render_optimeal
from carboo_assets import MASCOT_B64 as CARBOO_AVATAR

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
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
            background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:16px;
            padding:16px 24px; margin-bottom:20px; border:1px solid #334155;">
  <div style="display:flex; align-items:center; gap:14px;">
    <img src="{CARBOO_AVATAR}" style="width:44px; height:44px; border-radius:50%;
         border:2px solid #f97316; object-fit:cover;">
    <div>
      <div style="font-size:1.5rem; font-weight:900; letter-spacing:3px; color:#f8fafc;">
        CAR<span style="color:#f97316;">BOO</span>
      </div>
      <div style="font-size:0.68rem; color:#64748b; letter-spacing:1px;">RACE NUTRITION COACH</div>
    </div>
  </div>
  <div style="text-align:right; font-size:0.82rem; color:#64748b;">
    Ingelogd als <b style="color:#f8fafc;">{naam}</b>
    {'&nbsp;&nbsp;<span style="background:#f97316;color:white;border-radius:4px;padding:1px 7px;font-size:0.72rem;">ADMIN</span>' if is_admin else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# ─── NAVIGATIE / MODULE ROUTING ───────────────────────────────────────────────
# Toon credits + admin knop in navigatiebalk
_credits = st.session_state.get("current_user", {}).get("credits", 0)
nav_cols = st.columns([6, 1, 1, 1]) if is_admin else st.columns([7, 1, 1])
with nav_cols[-3] if is_admin else nav_cols[-2]:
    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #334155;border-radius:8px;'
        f'padding:6px 12px;text-align:center;">'
        f'<div style="font-size:8px;color:#64748b;font-weight:bold;">CREDITS</div>'
        f'<div style="font-size:16px;font-weight:900;color:#f97316;">{_credits}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with nav_cols[-2] if is_admin else nav_cols[-1]:
    if is_admin:
        if st.button("⚙️", key="nav_admin", help="Admin panel", use_container_width=True):
            st.session_state.module = "admin"
            st.rerun()
with nav_cols[-1] if is_admin else nav_cols[-1]:
    if st.button("↩️", key="nav_logout", help="Uitloggen", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

module = st.session_state.module

if module == "menu":
    render_coach(user)

elif module == "coach":
    render_coach(user)

elif module == "carbomax":
    render_carbomax()

elif module == "raceprep":
    render_raceprep()

elif module == "optimeal":
    render_optimeal()

elif module == "admin":
    render_admin_panel()

elif module == "rapport":
    html = st.session_state.get("rapport_html", "")
    if html:
        # Toon rapport inline + download knop bovenaan
        data = st.session_state.get("coach_data", {})
        atleet   = data.get("atleet_naam", naam).replace(" ", "_")
        wedstrijd = data.get("wedstrijd_naam", "race").replace(" ", "_")
        bestandsnaam = f"Carboo_RacePlan_{atleet}_{wedstrijd}.html"

        col_terug, col_dl = st.columns([1, 1])
        with col_terug:
            if st.button("🔄 Nieuw plan starten", key="rapport_terug"):
                # Wis raceplan data maar bewaar gebruikersprofiel
                for k in list(st.session_state.keys()):
                    if k.startswith(("cl_", "rp_", "rd_", "p_", "w_", "prev_",
                                     "coach_stap", "coach_data", "rapport_html")):
                        del st.session_state[k]
                st.session_state.module = "coach"
                st.rerun()
        with col_dl:
            st.download_button(
                label="⬇️  Download rapport",
                data=html.encode("utf-8"),
                file_name=bestandsnaam,
                mime="text/html",
                use_container_width=True,
                key="rapport_download"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.components.v1.html(html, height=3000, scrolling=True)
    else:
        st.session_state.module = "coach"
        st.rerun()
