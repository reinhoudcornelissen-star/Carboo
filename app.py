
import streamlit as st
import streamlit.components.v1
from login import render_login_page, render_admin_panel, render_wachtwoord_reset
from mollie_payments import render_credits_kopen, controleer_betaling_url
from carboo_coach import render_coach
try:
    from module_testing import render_testing
except ImportError:
    def render_testing(user): st.info("Module nog niet beschikbaar.")
try:
    from fuelc import render_fuelc
except ImportError:
    def render_fuelc(user): st.info("Module niet beschikbaar.")
try:
    from carbomax import render_carbomax
except ImportError:
    def render_carbomax(): st.info("Module niet beschikbaar.")
try:
    from raceprep import render_raceprep
except ImportError:
    def render_raceprep(): st.info("Module niet beschikbaar.")
try:
    from optimeal import render_optimeal
except ImportError:
    def render_optimeal(): st.info("Module niet beschikbaar.")
try:
    from carboo_assets import MASCOT_B64 as CARBOO_AVATAR
except ImportError:
    CARBOO_AVATAR = ""

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
    if render_wachtwoord_reset():
        st.stop()
    render_login_page()
    st.stop()

# ─── INGELOGD ─────────────────────────────────────────────────────────────────
user = st.session_state.get("current_user")
if not user or not st.session_state.get("logged_in"):
    render_login_page()
    st.stop()
naam     = user.get("name", "Atleet") if user else "Atleet"
is_admin = user.get("role") == "admin" if user else False

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
        if st.button("⚙️", key="nav_admin_top", help="Admin panel", use_container_width=True):
            st.session_state.module = "admin"
            st.rerun()
with nav_cols[-1] if is_admin else nav_cols[-1]:
    if st.button("↩️", key="nav_logout_top", help="Uitloggen", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

module = st.session_state.module

# Controleer of gebruiker terugkomt van Mollie betaling
controleer_betaling_url()

if module == "menu":
    st.markdown("""
    <div style="text-align:center;padding:16px 0 20px;">
        <div style="font-size:0.7rem;color:#64748b;letter-spacing:3px;margin-bottom:6px;">
            JOUW NUTRITION TOOLS</div>
        <div style="font-size:1.3rem;font-weight:800;color:#f8fafc;">
            Kies een module om te starten</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Race Nutrition Plan ───────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a);
                border:2px solid #f97316;border-radius:16px;padding:24px;
                margin-bottom:6px;">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="font-size:2.5rem;">🏁</div>
            <div>
                <div style="font-size:1.2rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">
                    Race Nutrition Plan</div>
                <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                    Carboloading · Laatste maaltijd · Uur-per-uur raceplan · PDF rapport
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏁  Start Race Nutrition Plan", key="mod_coach",
                 use_container_width=True):
        st.session_state.module = "coach"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Admin modules ─────────────────────────────────────────────────────────
    if is_admin:
        st.markdown(
            '<div style="font-size:0.65rem;color:#8b5cf6;letter-spacing:2px;'
            'font-weight:700;margin-bottom:10px;">EXTRA MODULES — ENKEL ADMIN</div>',
            unsafe_allow_html=True)

        # Train the Gut
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #8b5cf6;border-radius:12px;
                    padding:18px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:1.8rem;">🧪</div>
                <div>
                    <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:3px;">
                        Train the Gut</div>
                    <div style="font-size:0.78rem;color:#64748b;">
                        Systematisch de maag trainen met oplopende KH-hoeveelheden.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧪  Open Train the Gut", key="open_testing",
                     use_container_width=True):
            st.session_state.module = "testing"
            st.rerun()

        st.markdown("<br style='margin-bottom:6px;'>", unsafe_allow_html=True)

        # FuelC
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #22c55e;border-radius:12px;
                    padding:18px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:1.8rem;">⚡</div>
                <div>
                    <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:3px;">
                        FuelC — Energie Coach</div>
                    <div style="font-size:0.78rem;color:#64748b;">
                        TDEE · Trainingszone · Voedselbibliotheek · Dagschema · Dashboard</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡  Open FuelC", key="open_fuelc",
                     use_container_width=True):
            st.session_state.module = "fuelc"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Binnenkort beschikbaar ────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;'
        'margin-bottom:10px;">BINNENKORT BESCHIKBAAR</div>',
        unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                padding:18px;opacity:0.6;">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="font-size:1.8rem;">🔄</div>
            <div>
                <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:3px;">
                    Race Weight Plan</div>
                <div style="font-size:0.78rem;color:#64748b;">
                    Optimaal gewichtsplan richting je wedstrijd.</div>
                <div style="font-size:10px;color:#f97316;margin-top:4px;">
                    Binnenkort beschikbaar</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

elif module == "fuelc":
    render_fuelc(user)

elif module == "testing":
    render_testing(user)

elif module == "rapport":
    html = st.session_state.get("rapport_html", "")
    if not html:
        st.session_state.module = "coach"
        st.rerun()
    else:
        data     = st.session_state.get("coach_data", {})
        atleet   = data.get("atleet_naam", naam).replace(" ", "_")
        wedstrijd= data.get("wedstrijd_naam", "race").replace(" ", "_")
        pdf_naam = f"Carboo_RacePlan_{atleet}_{wedstrijd}.pdf"

        from login import get_credits, gebruik_credit
        _uid = st.session_state.get("current_user", {}).get("id", "")

        if st.session_state.get("bevestig_nieuw_plan"):
            st.warning("⚠️ Ben je zeker? Je huidige rapport verdwijnt en je hebt een nieuwe credit nodig.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Ja, nieuw plan starten", key="bevestig_ja",
                             use_container_width=True):
                    wis_keys = [k for k in list(st.session_state.keys())
                                if k.startswith(("cl_","rp_","rd_","p_","w_","prev_",
                                                 "coach_stap","coach_data","rapport",
                                                 "bevestig"))]
                    for k in wis_keys:
                        del st.session_state[k]
                    st.session_state.module = "coach"
                    st.rerun()
            with c2:
                if st.button("❌ Annuleren", key="bevestig_nee",
                             use_container_width=True):
                    del st.session_state["bevestig_nieuw_plan"]
                    st.rerun()
            st.stop()

        if st.session_state.get("rapport_ontgrendeld"):
            credits_nu = 1
        elif "rapport_credits_gecheckt" not in st.session_state:
            credits_nu = get_credits(_uid) if _uid else 0
            st.session_state["rapport_credits_gecheckt"] = credits_nu
        else:
            credits_nu = st.session_state["rapport_credits_gecheckt"]

        if credits_nu <= 0:
            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(249,115,22,0.15),rgba(30,58,138,0.15));
                        border:2px solid #f97316;border-radius:12px;padding:20px;text-align:center;
                        margin-bottom:16px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">🔒</div>
                <div style="font-size:1.1rem;font-weight:900;color:#f8fafc;margin-bottom:6px;">
                    Jouw rapport staat klaar!</div>
                <div style="font-size:0.85rem;color:#94a3b8;margin-bottom:4px;">
                    Koop een credit om te downloaden.</div>
            </div>
            """, unsafe_allow_html=True)

            col_koop, col_terug = st.columns([2, 1])
            with col_koop:
                if st.button("🛒  Koop credit & download rapport", key="koop_unlock",
                             use_container_width=True):
                    from login import sla_coach_data_op
                    sla_coach_data_op(_uid, data)
                    st.session_state["rapport_html_pending"] = html
                    st.session_state.module = "credits"
                    st.rerun()
            with col_terug:
                if st.button("🔄 Nieuw plan", key="rapport_terug_blur",
                             use_container_width=True):
                    st.session_state["bevestig_nieuw_plan"] = True
                    st.rerun()

            blurred_html = html.replace("</body>",
                """<style>body{filter:blur(5px)!important;pointer-events:none!important;
                user-select:none!important;}</style>
                <div style="position:fixed;top:0;left:0;right:0;bottom:0;
                            background:rgba(15,23,42,0.5);z-index:9999;
                            display:flex;align-items:center;justify-content:center;">
                    <div style="background:#1e293b;border:2px solid #f97316;border-radius:16px;
                                padding:30px 40px;text-align:center;max-width:400px;">
                        <div style="font-size:2rem;">🔒</div>
                        <div style="font-size:1.2rem;font-weight:900;color:#f8fafc;margin:10px 0 6px;">
                            Jouw rapport staat klaar!</div>
                        <div style="font-size:0.85rem;color:#94a3b8;">
                            Koop een credit om te downloaden.</div>
                    </div>
                </div></body>""")
            st.components.v1.html(blurred_html, height=2000, scrolling=False)

        else:
            if not st.session_state.get("rapport_credit_afgetrokken"):
                gebruik_credit(_uid, "Race Nutrition Rapport gegenereerd")
                st.session_state.current_user["credits"] = get_credits(_uid)
                st.session_state["rapport_credit_afgetrokken"] = True
                st.session_state["rapport_ontgrendeld"] = True

            col_terug, col_pdf = st.columns([1, 1])
            with col_terug:
                if st.button("🔄 Nieuw plan starten", key="rapport_terug"):
                    st.session_state["bevestig_nieuw_plan"] = True
                    st.rerun()
            with col_pdf:
                if st.button("📄  Download PDF", key="rapport_dl_pdf_btn",
                             use_container_width=True):
                    with st.spinner("PDF wordt gegenereerd..."):
                        try:
                            from carboo_coach import _genereer_pdf
                            gn = st.session_state.get("current_user",{}).get("name","Atleet")
                            data_pdf = dict(data)
                            data_pdf["logo_b64"]  = st.session_state.get("coach_logo_b64", "")
                            data_pdf["logo_mime"] = st.session_state.get("coach_logo_mime", "image/png")
                            pdf_bytes = _genereer_pdf(data_pdf, gn)
                            st.session_state["rapport_pdf"] = pdf_bytes
                            st.rerun()
                        except Exception as e:
                            st.error(f"PDF fout: {e}")
                if st.session_state.get("rapport_pdf"):
                    st.download_button(
                        label="⬇️  Sla PDF op",
                        data=st.session_state["rapport_pdf"],
                        file_name=pdf_naam,
                        mime="application/pdf",
                        use_container_width=True,
                        key="rapport_pdf_save"
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.components.v1.html(html, height=3000, scrolling=True)

elif module == "credits":
    _uid   = st.session_state.get("current_user", {}).get("id", "")
    _email = st.session_state.get("current_user", {}).get("email", "")
    render_credits_kopen(_uid, _email)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Terug", key="credits_terug"):
        st.session_state.module = "coach"
        st.rerun()
