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

# ─── AVATAR GECACHED (voorkomt infinite loading) ──────────────────────────────
@st.cache_data
def get_carboo_avatar():
    # Laad avatar vanuit bestand ipv inline base64 string
    import base64, os
    avatar_path = os.path.join(os.path.dirname(__file__), "carboo_avatar.png")
    if os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    # Fallback: lege placeholder
    return ""

CARBOO_AVATAR = get_carboo_avatar()

# HEADER
col_brand, col_user = st.columns([4, 1])
with col_brand:
    st.markdown('''
    <div style="display:flex; align-items:center; gap:14px; padding:10px 0;">
        <img src="{}" style="width:52px; height:52px; object-fit:contain;">
        <div class="brand-header" style="padding:0; margin:0;">CAR<span>BOO</span></div>
    </div>
    '''.format(CARBOO_AVATAR), unsafe_allow_html=True)
with col_user:
    st.markdown(f"""
    <div style="text-align:right; padding-top:20px; color:#94a3b8; font-size:0.8rem;">
        👤 <b style="color:#f8fafc;">{naam}</b>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Uitloggen", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ─── NAVIGATIE ────────────────────────────────────────────────────────────────
if st.session_state.module != "menu":
    if st.button("← TERUG NAAR MENU", key="back_btn"):
        st.session_state.module = "menu"
        st.rerun()
    st.markdown("<hr style='border-color:#1e293b; margin:8px 0 20px 0;'>", unsafe_allow_html=True)

# ─── MENU ─────────────────────────────────────────────────────────────────────
if st.session_state.module == "menu":

    # CARBOO COACH SECTIE
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a); border:1px solid #334155; 
         border-radius:20px; padding:24px; margin-bottom:28px; border-left:5px solid #f97316;">
        <div style="font-size:0.7rem; color:#f97316; font-weight:800; letter-spacing:2px; margin-bottom:4px;">JOUW PERSOONLIJKE COACH</div>
        <div style="font-size:1.2rem; font-weight:900; color:#f8fafc; margin-bottom:4px;">🏃 Carboo begeleidt jou naar raceday</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Volg de interactieve wizard voor een volledig voedingsplan op maat — van carboloading tot uurschema tijdens de race.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀  START MET CARBOO COACH", key="open_coach"):
        st.session_state.module = "coach"
        st.rerun()

    st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown('<div style="color:#64748b; font-size:0.75rem; font-weight:700; letter-spacing:2px; margin-bottom:16px;">OF OPEN EEN MODULE RECHTSTREEKS</div>', unsafe_allow_html=True)

    cols = st.columns(3 if not is_admin else 4)
    tiles = [
        ("carbomax", "🍝", "CARBOMAX", "#f97316", "2-daags koolhydratenplan"),
        ("raceprep", "🏁", "RACEPREP", "#3b82f6", "Slim uurschema voor de race"),
        ("optimeal", "🥗", "OPTIMEAL", "#22c55e", "Dagelijkse voedingsoptimalisatie"),
    ]
    if is_admin:
        tiles.append(("admin", "⚙️", "ADMIN", "#8b5cf6", "Gebruikersbeheer"))

    for col, (mod_id, icon, titel, kleur, beschrijving) in zip(cols, tiles):
        with col:
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:14px; padding:30px 16px; text-align:center; border-bottom:4px solid {kleur}; margin-bottom:8px;">
                <div style="font-size:1.8rem; margin-bottom:8px;">{icon}</div>
                <div style="font-weight:900; font-size:1rem; letter-spacing:1px; color:#f8fafc;">{titel}</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:6px;">{beschrijving}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"OPEN {titel}", key=f"open_{mod_id}"):
                st.session_state.module = mod_id
                st.rerun()

# ─── MODULES ─────────────────────────────────────────────────────────────────
elif st.session_state.module == "coach":
    render_coach(user)

elif st.session_state.module == "carbomax":
    render_carbomax()

elif st.session_state.module == "raceprep":
    render_raceprep()

elif st.session_state.module == "optimeal":
    render_optimeal()

elif st.session_state.module == "admin" and is_admin:
    render_admin_panel()
