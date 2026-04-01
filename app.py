import streamlit as st
import base64
from login import render_login_page, render_admin_panel
from carboo_coach import render_coach
from carbomax import render_carbomax
from raceprep import render_raceprep
from optimeal import render_optimeal
from chat import show_chat

st.set_page_config(
    page_title="Carboo — Race Nutrition",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── MASCOT ──────────────────────────────────────────────────────────────────
from carboo_assets import MASCOT_B64 as CARBOO_AVATAR

# ─── GLOBALE CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700;900&family=Inter:wght@300;400;600;700;900&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; background-color:#050a18; color:#f8fafc; }
#MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}
[data-testid="stToolbar"]{display:none!important;}
[data-testid="stDecoration"]{display:none!important;}
[data-testid="stHeader"]{display:none!important;height:0!important;}
.stApp{background:#050a18;}
.block-container{padding-top:0!important;max-width:1100px;margin:0 auto;}
.stMainBlockContainer{padding-top:0!important;}
/* Buttons */
.stButton>button{
    background:linear-gradient(135deg,#f97316,#ea580c)!important;
    color:white!important;border:none!important;border-radius:10px!important;
    font-weight:700!important;font-size:0.9rem!important;padding:12px 20px!important;
    width:100%!important;letter-spacing:0.05em!important;
    box-shadow:0 4px 15px rgba(249,115,22,0.3)!important;transition:all 0.2s!important;}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(249,115,22,0.5)!important;}
/* Inputs */
.stNumberInput input,.stTextInput input,.stTimeInput input{
    background:#0f172a!important;color:white!important;
    border:1px solid #334155!important;border-radius:8px!important;}
.stSelectbox>div>div{background:#0f172a!important;color:white!important;
    border:1px solid #334155!important;border-radius:8px!important;}
div[data-baseweb="select"]>div{background:#0f172a!important;border-color:#334155!important;color:white!important;}
label{color:#94a3b8!important;font-size:0.78rem!important;text-transform:uppercase;font-weight:700!important;}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:transparent;gap:6px;border-bottom:1px solid #1e293b;}
.stTabs [data-baseweb="tab"]{background:#0f172a;color:#64748b;border-radius:8px 8px 0 0;
    font-weight:700;border:1px solid #1e293b;border-bottom:none;padding:10px 24px;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#f97316,#ea580c)!important;
    color:white!important;border-color:transparent!important;}
/* Cards */
.meal-card{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:18px;margin-bottom:12px;}
.meal-card-title{color:#f97316;font-weight:800;font-size:0.85rem;text-transform:uppercase;
    margin-bottom:10px;border-bottom:1px solid #1e293b;padding-bottom:6px;}
.section-title{font-size:1.4rem;font-weight:800;color:#f97316;border-bottom:2px solid #1e293b;
    padding-bottom:8px;margin-bottom:20px;}
.result-ok{background:#f0fdf4;border-left:5px solid #22c55e;border-radius:8px;padding:14px;margin-bottom:10px;color:#1e293b;}
.result-low{background:#fef2f2;border-left:5px solid #ef4444;border-radius:8px;padding:14px;margin-bottom:10px;color:#1e293b;}
.boost-tip{background:#fee2e2;border-radius:6px;padding:8px 12px;font-size:0.8rem;color:#991b1b;margin-top:6px;}
.timeline-block{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:14px;color:#1e293b;}
.timeline-uur{font-weight:900;font-size:0.95rem;border-bottom:2px solid #3b82f6;padding-bottom:5px;
    margin-bottom:10px;display:flex;justify-content:space-between;}
.timeline-row{font-size:0.85rem;margin-bottom:6px;display:flex;gap:10px;}
.min-label{color:#3b82f6;font-weight:700;min-width:45px;}
.alert-orange{background:#fff7ed;border-left:5px solid #f97316;padding:12px 16px;border-radius:8px;color:#9a3412;font-size:0.85rem;margin-bottom:12px;}
.alert-red{background:#fef2f2;border-left:5px solid #ef4444;padding:12px 16px;border-radius:8px;color:#991b1b;font-size:0.85rem;margin-bottom:12px;}
/* Menu specifiek */
.carboo-hero-title{
    font-family:'Rajdhani',sans-serif;font-size:2.8rem;font-weight:900;
    letter-spacing:0.15em;text-align:center;line-height:1;margin-bottom:4px;
    background:linear-gradient(135deg,#ffffff 10%,#f97316 55%,#fb923c 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.carboo-subtitle{
    font-size:0.65rem;font-weight:800;letter-spacing:0.4em;color:#3b82f6;
    text-transform:uppercase;text-align:center;}
.coach-card{
    background:linear-gradient(135deg,#0d1829,#162033);
    border:1px solid #253450;border-radius:20px;padding:28px 32px;
    box-shadow:0 25px 80px rgba(0,0,0,0.5);position:relative;}
.wizard-card{
    background:linear-gradient(135deg,#0d1829 0%,#162033 100%);
    border:1px solid #253450;border-radius:22px;padding:32px 28px;
    text-align:center;position:relative;overflow:hidden;}
.wizard-card-title{
    font-family:'Rajdhani',sans-serif;font-size:1.5rem;font-weight:900;
    color:#f97316;letter-spacing:0.12em;margin-bottom:10px;}
.tool-card{
    background:#0d1829;border:1px solid #1e293b;border-radius:14px;
    padding:18px 14px;text-align:center;margin-bottom:8px;}
@keyframes float{0%,100%{transform:translateY(0px);}50%{transform:translateY(-10px);}}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in [("logged_in", False), ("current_user", None), ("module", "menu")]:
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state.logged_in:
    render_login_page()
    st.stop()

user     = st.session_state.current_user
naam     = user.get("name", "Atleet")
is_admin = user.get("role") == "admin"

# ─── MODULE ROUTER ────────────────────────────────────────────────────────────
mod = st.session_state.module

if mod != "menu":
    if st.button("← Terug naar menu", key="btn_back"):
        st.session_state.module = "menu"
        st.rerun()
    if mod == "coach":
        render_coach(user)
    elif mod == "admin":
        render_admin_panel()
    st.stop()

# ─── MENU: ACHTERGROND GLOW ──────────────────────────────────────────────────
st.markdown("""
<div style="position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:0;
    background:radial-gradient(ellipse at 20% 20%,rgba(249,115,22,0.07) 0%,transparent 50%),
               radial-gradient(ellipse at 80% 80%,rgba(59,130,246,0.07) 0%,transparent 50%);"></div>
""", unsafe_allow_html=True)

# ─── MASCOT + BRANDING ───────────────────────────────────────────────────────
st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

col_l, col_mid, col_r = st.columns([1, 3, 1])
with col_mid:
    st.markdown('''
    <div class="carboo-hero-title">CARBOO</div>
    <div class="carboo-subtitle">RACE NUTRITION PLATFORM</div>
    ''', unsafe_allow_html=True)
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─── COACH BUBBLE ────────────────────────────────────────────────────────────
col_l2, col_bubble, col_r2 = st.columns([1, 3, 1])
with col_bubble:
    st.markdown(
        f'''<div class="coach-card">
            <div style="position:absolute;top:-13px;left:50%;transform:translateX(-50%);
                background:linear-gradient(135deg,#f97316,#ea580c);border-radius:20px;
                padding:4px 18px;font-size:0.6rem;font-weight:900;letter-spacing:0.2em;
                color:white;text-transform:uppercase;white-space:nowrap;
                box-shadow:0 4px 15px rgba(249,115,22,0.5);">✦ CARBOO COACH ✦</div>
            <p style="color:#e2e8f0;font-size:0.96rem;line-height:1.75;margin:0;text-align:center;">
                Hey <b style="color:#fb923c;">{naam}</b>! Ik ben blij je te zien. 🙌<br>
                <span style="color:#94a3b8;font-size:0.88rem;">
                We gaan stap voor stap werken aan een
                <b style="color:#f8fafc;">perfecte voorbereiding</b> op jouw wedstrijd.<br><br>
                Want weet je wat het mooie is? 
                <b style="color:#f97316;">Koolhydraten zijn géén vijand — ze zijn je raketbrandstof.</b> 🍝⚡<br>
                <span style="color:#64748b;">We love carbs. Carb with Carboo!</span>
                </span>
            </p>
        </div>''',
        unsafe_allow_html=True
    )

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# ─── WIZARD CARD ─────────────────────────────────────────────────────────────
col_l3, col_wiz, col_r3 = st.columns([1, 3, 1])
with col_wiz:
    st.markdown('''
    <div class="wizard-card">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;
            background:linear-gradient(90deg,#f97316,#3b82f6,#8b5cf6,#f97316);
            background-size:300% 100%;"></div>
        <div style="margin-bottom:6px; margin-top:4px;">
    ''' + '<img src="' + CARBOO_AVATAR + '" style="height:120px;width:auto;object-fit:contain;filter:drop-shadow(0 0 16px rgba(249,115,22,0.55));">' + '''
        </div>
        <div class="wizard-card-title">CARBOO COACH WIZARD</div>
        <div style="color:#94a3b8;font-size:0.88rem;line-height:1.7;margin-bottom:18px;">
            Jouw volledig gepersonaliseerd voedingsplan in 7 stappen.<br>
            <span style="color:#64748b;font-size:0.78rem;">
                Profiel · Wedstrijd · Carboloading · Racedag · Raceplan · Samenvatting
            </span>
        </div>
        <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
            <span style="background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);
                padding:5px 14px;border-radius:20px;font-size:0.72rem;color:#22c55e;font-weight:700;">
                🍝 Carboloading</span>
            <span style="background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.3);
                padding:5px 14px;border-radius:20px;font-size:0.72rem;color:#60a5fa;font-weight:700;">
                🌅 Racedag voeding</span>
            <span style="background:rgba(249,115,22,0.12);border:1px solid rgba(249,115,22,0.3);
                padding:5px 14px;border-radius:20px;font-size:0.72rem;color:#fb923c;font-weight:700;">
                ⏱️ Slim raceplan</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🚀  START DE WIZARD", key="start_coach", use_container_width=True):
        st.session_state.module = "coach"
        st.rerun()

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.markdown("---", unsafe_allow_html=False)

fc1, fc2 = st.columns([3, 1])
with fc1:
    admin_badge = (
        '<span style="background:rgba(249,115,22,0.15);border:1px solid rgba(249,115,22,0.3);'
        'border-radius:12px;padding:2px 10px;font-size:0.65rem;color:#fb923c;font-weight:800;">'
        '👑 ADMIN</span>'
    ) if is_admin else (
        '<span style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);'
        'border-radius:12px;padding:2px 10px;font-size:0.65rem;color:#22c55e;font-weight:800;">'
        '🏃 ATLEET</span>'
    )
    st.markdown(f'''
    <div style="display:flex;align-items:center;gap:12px;padding:8px 0;">
        <div style="background:linear-gradient(135deg,#f97316,#ea580c);border-radius:50%;
            width:36px;height:36px;display:flex;align-items:center;justify-content:center;
            font-weight:900;font-size:0.95rem;color:white;flex-shrink:0;">{naam[0].upper()}</div>
        <div>
            <div style="font-weight:700;color:#f8fafc;font-size:0.9rem;">{naam}</div>
            <div style="margin-top:3px;">{admin_badge}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

with fc2:
    btn_cols = st.columns(2 if is_admin else 1)
    if is_admin:
        with btn_cols[0]:
            if st.button("⚙️", key="btn_admin", use_container_width=True, help="Admin paneel"):
                st.session_state.module = "admin"
                st.rerun()
        with btn_cols[1]:
            if st.button("🚪", key="btn_logout_admin", use_container_width=True, help="Uitloggen"):
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()
    else:
        with btn_cols[0]:
            if st.button("🚪  Uitloggen", key="btn_logout", use_container_width=True):
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()
# --- CHATBOT FLOATING BUTTON ---
# Dit stukje code zorgt voor de knop rechtsonderin
st.markdown("""
    <style>
    div[data-testid="stButton"] > button[key="chat_btn"] {
        position: fixed;
        bottom: 25px;
        right: 25px;
        background-color: #f97316;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        z-index: 1000;
        font-size: 24px;
        border: none;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Als er op de zwevende knop geklikt wordt, toon de chat
if st.button("💬", key="chat_btn"):
    st.session_state.module = "chat"
    st.rerun()

# Als de module op 'chat' staat, voer de functie uit chat.py uit
if st.session_state.module == "chat":
    show_chat()
