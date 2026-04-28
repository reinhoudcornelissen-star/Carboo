import streamlit as st
import hashlib
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── Secrets & Supabase ──────────────────────────────────────────────────────
def _get_secrets(key: str, default: str = "") -> str:
    import os
    val = os.environ.get(key, "")
    if val: return val
    try: return st.secrets[key]
    except: return default

def _get_supabase():
    return create_client(_get_secrets("SUPABASE_URL"), _get_secrets("SUPABASE_KEY"))

def _hash(ww: str) -> str:
    return hashlib.sha256(ww.encode()).hexdigest()

def _get_user(email: str):
    try:
        r = _get_supabase().table("carboo_users").select("*").eq("email", email.lower().strip()).execute()
        return r.data[0] if r.data else None
    except: return None

def _get_user_by_id(user_id: str):
    try:
        r = _get_supabase().table("carboo_users").select("*").eq("id", user_id).execute()
        return r.data[0] if r.data else None
    except: return None

# ─── Credits ─────────────────────────────────────────────────────────────────
def get_credits(user_id: str) -> int:
    user = _get_user_by_id(user_id)
    return user["credits"] if user else 0

def gebruik_credit(user_id: str, beschrijving: str = "Rapport gegenereerd") -> bool:
    try:
        sb = _get_supabase()
        user = _get_user_by_id(user_id)
        if not user or user["credits"] <= 0: return False
        sb.table("carboo_users").update({"credits": user["credits"] - 1}).eq("id", user_id).execute()
        sb.table("carboo_transacties").insert({
            "user_id": user_id, "type": "gebruik",
            "credits": -1, "beschrijving": beschrijving,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij credit aftrek: {e}"); return False

def voeg_credits_toe(user_id: str, aantal: int, beschrijving: str = "Credits toegevoegd") -> bool:
    try:
        sb = _get_supabase()
        user = _get_user_by_id(user_id)
        if not user: return False
        sb.table("carboo_users").update({"credits": user["credits"] + aantal}).eq("id", user_id).execute()
        sb.table("carboo_transacties").insert({
            "user_id": user_id, "type": "aankoop",
            "credits": aantal, "beschrijving": beschrijving,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij credits toevoegen: {e}"); return False

# ─── Coach data ───────────────────────────────────────────────────────────────
def sla_coach_data_op(user_id: str, coach_data: dict) -> bool:
    try:
        import json
        _get_supabase().table("carboo_users").update({
            "coach_data_json": json.dumps(coach_data)
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Fout bij opslaan coach_data: {e}"); return False

def herstel_coach_data(user_id: str) -> dict | None:
    try:
        import json
        r = _get_supabase().table("carboo_users").select("coach_data_json").eq("id", user_id).execute()
        if r.data and r.data[0].get("coach_data_json"):
            return json.loads(r.data[0]["coach_data_json"])
        return None
    except Exception as e:
        print(f"Fout bij herstellen coach_data: {e}"); return None

def wis_coach_data(user_id: str):
    try:
        _get_supabase().table("carboo_users").update({"coach_data_json": None}).eq("id", user_id).execute()
    except: pass

# ─── Wachtwoord reset ─────────────────────────────────────────────────────────
import secrets
from datetime import datetime, timedelta

def stuur_reset_mail(email: str) -> bool:
    try:
        sb = _get_supabase()
        user = _get_user(email)
        if not user: return False
        token  = secrets.token_urlsafe(32)
        expiry = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        sb.table("carboo_users").update({
            "reset_token": token, "reset_token_expiry": expiry,
        }).eq("id", user["id"]).execute()
        app_url   = _get_secrets("APP_URL", "https://carboo.onrender.com")
        reset_url = f"{app_url}?reset_token={token}"
        afzender  = _get_secrets("MAIL_FROM", "")
        ww_mail   = _get_secrets("MAIL_PASSWORD", "")
        smtp_host = _get_secrets("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(_get_secrets("MAIL_PORT", 587))
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Carboo — Wachtwoord opnieuw instellen"
        msg["From"] = afzender; msg["To"] = email
        html_body = f"""<html><body style="font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px;">
        <div style="max-width:500px;margin:0 auto;background:#1e293b;border-radius:10px;padding:24px;">
            <div style="font-size:22px;font-weight:900;color:#f97316;margin-bottom:16px;">CAR<span style="color:#f1f5f9">BOO</span></div>
            <p style="color:#94a3b8;">Hallo {user['naam']},</p>
            <p style="color:#f1f5f9;">Je hebt een wachtwoordreset aangevraagd.</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{reset_url}" style="background:#f97316;color:white;padding:12px 28px;border-radius:8px;font-weight:700;text-decoration:none;">
                   🔑 Wachtwoord opnieuw instellen</a>
            </div>
            <p style="color:#64748b;font-size:0.8rem;">Deze link is 2 uur geldig.</p>
        </div></body></html>"""
        msg.attach(MIMEText(html_body, "html"))
        if ww_mail:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(); server.login(afzender, ww_mail)
                server.sendmail(afzender, email, msg.as_string())
        return True
    except Exception as e:
        print(f"Reset mail fout: {e}"); return False

def verifieer_reset_token(token: str) -> dict | None:
    try:
        r = _get_supabase().table("carboo_users").select("*").eq("reset_token", token).execute()
        if not r.data: return None
        user   = r.data[0]
        expiry = user.get("reset_token_expiry")
        if not expiry: return None
        if datetime.utcnow() > datetime.fromisoformat(expiry.replace("Z", "")): return None
        return user
    except: return None

def stel_nieuw_wachtwoord_in(token: str, nieuw_ww: str) -> bool:
    try:
        user = verifieer_reset_token(token)
        if not user: return False
        _get_supabase().table("carboo_users").update({
            "wachtwoord": _hash(nieuw_ww),
            "reset_token": None, "reset_token_expiry": None,
        }).eq("id", user["id"]).execute()
        return True
    except: return False

def render_wachtwoord_reset():
    token = st.query_params.get("reset_token", "")
    if not token: return False
    st.markdown("""<div style="max-width:420px;margin:40px auto 0 auto;text-align:center;">
        <div style="font-size:2rem;font-weight:900;letter-spacing:4px;color:#f8fafc;">
            CAR<span style="color:#f97316;">BOO</span></div>
        <div style="font-size:0.8rem;color:#64748b;letter-spacing:2px;margin-top:4px;margin-bottom:24px;">
            WACHTWOORD OPNIEUW INSTELLEN</div></div>""", unsafe_allow_html=True)
    user = verifieer_reset_token(token)
    if not user:
        st.error("❌ Deze link is ongeldig of verlopen.")
        st.query_params.clear(); return True
    st.success(f"Hallo {user['naam']}! Stel je nieuw wachtwoord in.")
    nw1 = st.text_input("Nieuw wachtwoord", type="password", key="reset_ww1")
    nw2 = st.text_input("Herhaal wachtwoord", type="password", key="reset_ww2")
    if st.button("✅ Wachtwoord opslaan", use_container_width=True):
        if len(nw1) < 6: st.error("Minimaal 6 tekens.")
        elif nw1 != nw2: st.error("Wachtwoorden komen niet overeen.")
        else:
            if stel_nieuw_wachtwoord_in(token, nw1):
                st.success("✅ Gewijzigd! Je kan nu inloggen.")
                st.query_params.clear()
            else: st.error("Fout bij opslaan.")
    return True

# ─── Promo codes ──────────────────────────────────────────────────────────────
def controleer_promo_code(code: str) -> dict | None:
    if not code: return None
    try:
        from datetime import date
        r = _get_supabase().table("carboo_codes").select("*").eq("code", code.upper().strip()).execute()
        if not r.data: return None
        c = r.data[0]
        if not c.get("actief", False): return None
        if c.get("vervaldatum") and date.fromisoformat(c["vervaldatum"]) < date.today(): return None
        if c.get("gebruik", 0) >= c.get("max_gebruik", 100): return None
        return c
    except Exception as e:
        print(f"Code check fout: {e}"); return None

def gebruik_promo_code(code_id: str, user_id: str, credits: int):
    try:
        sb = _get_supabase()
        huidig = sb.table("carboo_codes").select("gebruik").eq("id", code_id).execute()
        huidig_gebruik = huidig.data[0]["gebruik"] if huidig.data else 0
        sb.table("carboo_codes").update({"gebruik": huidig_gebruik + 1}).eq("id", code_id).execute()
        voeg_credits_toe(user_id, credits, f"Promo code — {credits} gratis rapport(en)")
        code_data = sb.table("carboo_codes").select("code").eq("id", code_id).execute()
        code_str = code_data.data[0]["code"] if code_data.data else ""
        sb.table("carboo_users").update({"promo_code": code_str}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Promo gebruik fout: {e}")

def get_alle_codes() -> list:
    try:
        return _get_supabase().table("carboo_codes").select("*").order("aangemaakt", desc=True).execute().data or []
    except: return []

def maak_code_aan(code: str, firma: str, credits: int, max_gebruik: int, vervaldatum: str) -> bool:
    try:
        _get_supabase().table("carboo_codes").insert({
            "code": code.upper().strip(), "firma": firma, "credits": credits,
            "max_gebruik": max_gebruik, "gebruik": 0, "actief": True,
            "vervaldatum": vervaldatum if vervaldatum else None,
        }).execute()
        return True
    except Exception as e:
        print(f"Code aanmaken fout: {e}"); return False

def toggle_code_actief(code_id: str, actief: bool):
    try:
        _get_supabase().table("carboo_codes").update({"actief": actief}).eq("id", code_id).execute()
    except: pass

# ─── Mail registratie ─────────────────────────────────────────────────────────
def _stuur_registratie_mail(naam: str, email: str):
    try:
        ontvanger = "info@sportlab-achterbos.be"
        afzender  = _get_secrets("MAIL_FROM", "noreply@carboo.app")
        ww_mail   = _get_secrets("MAIL_PASSWORD", "")
        smtp_host = _get_secrets("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(_get_secrets("MAIL_PORT", 587))
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏃 Nieuwe Carboo registratie: {naam}"
        msg["From"] = afzender; msg["To"] = ontvanger
        html_body = f"""<html><body style="font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px;">
        <div style="max-width:500px;margin:0 auto;background:#1e293b;border-radius:10px;padding:20px;">
            <div style="font-size:20px;font-weight:900;color:#f97316;margin-bottom:16px;">CARBOO — Nieuwe registratie</div>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px;color:#64748b;font-size:12px;font-weight:bold;">NAAM</td>
                    <td style="padding:8px;color:#f1f5f9;font-weight:bold;">{naam}</td></tr>
                <tr style="background:rgba(255,255,255,0.03)">
                    <td style="padding:8px;color:#64748b;font-size:12px;font-weight:bold;">E-MAIL</td>
                    <td style="padding:8px;color:#f1f5f9;">{email}</td></tr>
            </table>
        </div></body></html>"""
        msg.attach(MIMEText(html_body, "html"))
        if ww_mail:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(); server.login(afzender, ww_mail)
                server.sendmail(afzender, ontvanger, msg.as_string())
    except Exception as e:
        print(f"Mail fout (niet kritiek): {e}")

# ─── LANDING PAGE ─────────────────────────────────────────────────────────────
def render_landing_page():
    """Toont de volledige Carboo landing page via st.markdown."""
    # Check query params voor actie
    actie = st.query_params.get("actie", "")
    if actie == "register":
        st.query_params.clear()
        st.session_state["toon_landing"] = False
        st.session_state["_login_tab"]   = "register"
        st.rerun()
    elif actie == "login":
        st.query_params.clear()
        st.session_state["toon_landing"] = False
        st.session_state["_login_tab"]   = "login"
        st.rerun()

    # Verberg alle Streamlit UI elementen
    st.markdown("""
    <style>
    #MainMenu, header, footer, .stDeployButton,
    section[data-testid="stSidebar"],
    .stApp > div:first-child > div:first-child > div:first-child > div:first-child > div:first-child > div:first-child {
        display: none !important;
    }
    .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
    .stApp { background: #0c0c0c !important; }
    </style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
    <style>
    
*, *::before, *::after {{{{ box-sizing: border-box; margin: 0; padding: 0; }}}}
:root {{{{
  --oranje: #f97316;
  --oranje-hover: #ea6c0a;
  --oranje-licht: #fff7ed;
  --zwart: #0c0c0c;
  --donker: #141414;
  --kaart: #1a1a1a;
  --rand: #2a2a2a;
  --wit: #f5f3ef;
  --grijs: #888;
  --lichtgrijs: #222;
}}}}
html {{{{ scroll-behavior: smooth; }}}}
body {{{{
  font-family: 'Instrument Sans', sans-serif;
  background: var(--zwart);
  color: var(--wit);
  overflow-x: hidden;
}}}}

/* ── NAV ── */
nav {{{{
  position: fixed; top: 0; z-index: 100; width: 100%;
  padding: 20px clamp(20px,5vw,80px);
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(12,12,12,0.85); backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}}}}
.nav-logo {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.3rem; font-weight: 800;
  letter-spacing: -0.5px; color: var(--wit);
  text-decoration: none;
}}}}
.nav-logo span {{{{ color: var(--oranje); }}}}
.nav-tag {{{{
  font-size: 0.65rem; font-weight: 600; letter-spacing: 2px;
  text-transform: uppercase; color: var(--grijs);
  border: 1px solid var(--rand); padding: 4px 10px; border-radius: 100px;
}}}}
.nav-right {{{{ display: flex; align-items: center; gap: 12px; }}}}
.nav-login {{{{
  font-size: 0.82rem; color: var(--grijs); text-decoration: none;
  padding: 8px 16px; transition: color 0.2s;
}}}}
.nav-login:hover {{{{ color: var(--wit); }}}}
.btn-cta {{{{
  font-size: 0.82rem; font-weight: 600; color: var(--zwart);
  background: var(--oranje); padding: 9px 20px; border-radius: 8px;
  text-decoration: none; transition: background 0.2s, transform 0.15s;
  display: inline-flex; align-items: center; gap: 6px;
}}}}
.btn-cta:hover {{{{ background: var(--oranje-hover); transform: translateY(-1px); }}}}
@media(max-width:600px){{{{ .nav-tag {{{{ display:none; }}}} }}}}

/* ── HERO ── */
.hero {{{{
  min-height: 100vh;
  padding: 140px clamp(20px,6vw,100px) 80px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
  max-width: 1300px;
  margin: 0 auto;
}}}}
@media(max-width:900px){{{{ .hero {{{{ grid-template-columns:1fr; padding-top:120px; }}}} .hero-right {{{{ display:none; }}}} }}}}

.hero-tag {{{{
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 0.7rem; font-weight: 600; letter-spacing: 2.5px;
  text-transform: uppercase; color: var(--oranje);
  margin-bottom: 28px;
}}}}
.hero-tag::before {{{{
  content: '';
  width: 24px; height: 1px; background: var(--oranje);
}}}}
.hero h1 {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(3.5rem, 7vw, 6.5rem);
  font-weight: 400;
  line-height: 0.95;
  letter-spacing: 2px;
  color: var(--wit);
  margin-bottom: 28px;
}}}}
.hero h1 em {{{{ color: var(--oranje); font-style: normal; }}}}
.hero h1 .outline {{{{
  -webkit-text-stroke: 2px rgba(245,243,239,0.25);
  color: transparent;
}}}}
.hero-sub {{{{
  font-size: 1.05rem; color: var(--grijs);
  line-height: 1.75; max-width: 420px; margin-bottom: 44px;
}}}}
.hero-cta {{{{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }}}}
.btn-primary {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 0.9rem; font-weight: 700; color: var(--zwart);
  background: var(--oranje); padding: 14px 28px; border-radius: 10px;
  text-decoration: none; transition: background 0.2s, transform 0.15s;
  box-shadow: 0 8px 24px rgba(249,115,22,0.3);
}}}}
.btn-primary:hover {{{{ background: var(--oranje-hover); transform: translateY(-2px); }}}}
.btn-ghost {{{{
  font-size: 0.9rem; font-weight: 500; color: var(--grijs);
  text-decoration: none; padding: 14px 0;
  display: inline-flex; align-items: center; gap: 8px;
  border-bottom: 1px solid transparent;
  transition: color 0.2s, border-color 0.2s;
}}}}
.btn-ghost:hover {{{{ color: var(--wit); border-color: var(--wit); }}}}
.hero-proof {{{{ display: flex; gap: 24px; flex-wrap: wrap; }}}}
.proof-item {{{{
  font-size: 0.78rem; color: #555;
  display: flex; align-items: center; gap: 6px;
}}}}
.proof-item::before {{{{ content: '✓'; color: var(--oranje); font-weight: 700; }}}}

/* Mockup */
.hero-right {{{{}}}}
.mockup {{{{
  background: #111;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 40px 100px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06);
  transform: perspective(1000px) rotateY(-3deg) rotateX(2deg);
  transition: transform 0.4s ease;
}}}}
.mockup:hover {{{{ transform: perspective(1000px) rotateY(0deg) rotateX(0deg); }}}}
.mock-bar {{{{
  background: #1a1a1a; padding: 12px 16px;
  display: flex; align-items: center; gap: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}}}}
.dot {{{{ width:10px; height:10px; border-radius:50%; }}}}
.mock-url {{{{
  flex:1; background:#222; border-radius:6px;
  padding:4px 12px; font-size:0.65rem; color:#555; text-align:center;
}}}}
.mock-body {{{{ padding: 20px; }}}}
.ml {{{{ font-size:.6rem; font-weight:700; color:var(--oranje); letter-spacing:2px; margin-bottom:10px; }}}}
.mt {{{{ font-size:1rem; font-weight:700; color:#f5f3ef; margin-bottom:16px; }}}}
.mc {{{{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:16px; }}}}
.mc-card {{{{ background:#1e293b; border-radius:8px; padding:10px; }}}}
.mc-lbl {{{{ font-size:.55rem; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:3px; }}}}
.mc-val {{{{ font-size:1rem; font-weight:800; line-height:1; }}}}
.mc-bar {{{{ height:3px; border-radius:2px; margin-top:6px; background:#f97316; }}}}
.mch-lbl {{{{ font-size:.62rem; color:#64748b; margin-bottom:8px; }}}}
.mch {{{{ display:flex; align-items:flex-end; gap:4px; height:50px; margin-bottom:14px; }}}}
.mb {{{{ flex:1; border-radius:3px 3px 0 0; background:#1e293b; }}}}
.mb.a {{{{ background:#f97316; }}}}
.mlist {{{{ display:flex; flex-direction:column; gap:5px; }}}}
.mlist-item {{{{
  display:flex; justify-content:space-between; align-items:center;
  font-size:.62rem; color:#94a3b8;
  background:#1e293b; border-radius:6px; padding:6px 10px;
}}}}
.mlist-item span {{{{ color:#f97316; font-weight:700; }}}}

/* ── APP OVERZICHT SECTIE ── */
.app-sectie {{{{
  padding: clamp(80px,12vw,120px) clamp(20px,6vw,100px);
  max-width: 1300px; margin: 0 auto;
}}}}
.sectie-lbl {{{{
  font-size: 0.68rem; font-weight: 700; letter-spacing: 3px;
  text-transform: uppercase; color: var(--oranje); margin-bottom: 20px;
  display: flex; align-items: center; gap: 10px;
}}}}
.sectie-lbl::after {{{{ content: ''; flex:1; height:1px; background:var(--rand); }}}}

.app-grid {{{{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 2px;
  margin-top: 56px;
  border: 1px solid var(--rand);
  border-radius: 16px;
  overflow: hidden;
}}}}
@media(max-width:900px){{{{ .app-grid {{{{ grid-template-columns:1fr; }}}} }}}}

.app-kaart {{{{
  background: var(--kaart);
  padding: 44px 36px;
  position: relative;
  overflow: hidden;
  transition: background 0.3s;
  cursor: default;
}}}}
.app-kaart:hover {{{{ background: #1f1f1f; }}}}
.app-kaart::before {{{{
  content: '';
  position: absolute; top:0; left:0; right:0; height:3px;
  background: var(--oranje);
  transform: scaleX(0); transform-origin: left;
  transition: transform 0.3s;
}}}}
.app-kaart:hover::before {{{{ transform: scaleX(1); }}}}

.app-kaart-nr {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 5rem; font-weight: 800;
  color: rgba(249,115,22,0.07);
  position: absolute; top: 16px; right: 24px;
  line-height: 1;
}}}}
.app-kaart-icon {{{{ font-size: 2rem; margin-bottom: 20px; display: block; }}}}
.app-kaart-titel {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.25rem; font-weight: 700;
  color: var(--wit); margin-bottom: 14px; letter-spacing: -0.3px;
}}}}
.app-kaart-tekst {{{{ font-size: 0.88rem; color: var(--grijs); line-height: 1.75; margin-bottom: 20px; }}}}
.app-kaart-tags {{{{ display: flex; gap: 6px; flex-wrap: wrap; }}}}
.tag {{{{
  font-size: 0.68rem; font-weight: 600; color: var(--oranje);
  background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.2);
  padding: 3px 10px; border-radius: 100px;
}}}}

/* ── BEKENTENIS SECTIE ── */
.bekentenis-sectie {{{{
  background: var(--donker);
  border-top: 1px solid var(--rand);
  border-bottom: 1px solid var(--rand);
  padding: clamp(60px,8vw,100px) clamp(20px,6vw,100px);
}}}}
.bekentenis-inner {{{{ max-width: 1300px; margin: 0 auto; }}}}
.bekentenis-titel {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2rem,4vw,3.2rem);
  font-weight: 800; letter-spacing: -1px;
  color: var(--wit); margin-bottom: 48px; line-height: 1.1; max-width: 640px;
}}}}
.bekentenis-grid {{{{
  display: grid; grid-template-columns: repeat(3,1fr);
  gap: 16px;
}}}}
@media(max-width:768px){{{{ .bekentenis-grid {{{{ grid-template-columns:1fr; }}}} }}}}
.bek-kaart {{{{
  background: #111;
  border-radius: 12px; padding: 28px 24px;
  border: 1px solid var(--rand);
}}}}
.bek-kaart-emoji {{{{ font-size: 1.6rem; margin-bottom: 14px; display: block; font-style: normal; }}}}
.bek-kaart-tekst {{{{ font-size: 0.9rem; color: #777; line-height: 1.65; font-style: italic; }}}}
.bek-strip {{{{
  margin-top: 32px;
  background: rgba(249,115,22,0.08);
  border: 1px solid rgba(249,115,22,0.2);
  border-radius: 12px; padding: 20px 28px;
  font-size: 0.95rem; color: #aaa; text-align: center; line-height: 1.6;
}}}}
.bek-strip strong {{{{ color: var(--oranje); font-weight: 700; }}}}

/* ── FUELING SECTIE ── */
.fueling-sectie {{{{
  padding: clamp(80px,12vw,120px) clamp(20px,6vw,100px);
  max-width: 1300px; margin: 0 auto;
}}}}
.fueling-header {{{{
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 80px; align-items: start; margin-bottom: 64px;
}}}}
@media(max-width:900px){{{{ .fueling-header {{{{ grid-template-columns:1fr; gap:32px; }}}} }}}}
.fueling-h2 {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2rem,4vw,3.2rem); font-weight: 800;
  letter-spacing: -1px; color: var(--wit); line-height: 1.1;
}}}}
.fueling-h2 em {{{{ color: var(--oranje); font-style: normal; }}}}
.fueling-tekst {{{{ font-size: 0.92rem; color: var(--grijs); line-height: 1.75; }}}}

.fueling-grid {{{{
  display: grid; grid-template-columns: repeat(2,1fr); gap: 16px;
}}}}
@media(max-width:768px){{{{ .fueling-grid {{{{ grid-template-columns:1fr; }}}} }}}}
.fuel-kaart {{{{
  background: var(--kaart); border-radius: 12px;
  padding: 28px; border: 1px solid var(--rand);
  display: flex; gap: 18px; align-items: flex-start;
  transition: border-color 0.2s, background 0.2s;
}}}}
.fuel-kaart:hover {{{{ border-color: rgba(249,115,22,0.3); background: #1d1d1d; }}}}
.fuel-icon {{{{
  width: 42px; height: 42px; border-radius: 10px;
  background: rgba(249,115,22,0.12);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; flex-shrink: 0;
}}}}
.fuel-kaart-titel {{{{ font-size: 0.92rem; font-weight: 700; color: var(--wit); margin-bottom: 6px; }}}}
.fuel-kaart-tekst {{{{ font-size: 0.82rem; color: var(--grijs); line-height: 1.65; }}}}

/* ── ALGO SECTIE ── */
.algo-sectie {{{{
  background: var(--donker);
  border-top: 1px solid var(--rand);
  padding: clamp(80px,12vw,120px) clamp(20px,6vw,100px);
}}}}
.algo-inner {{{{ max-width: 1300px; margin: 0 auto; }}}}
.algo-grid {{{{
  display: grid; grid-template-columns: 1.2fr 1fr;
  gap: 80px; align-items: center;
}}}}
@media(max-width:900px){{{{ .algo-grid {{{{ grid-template-columns:1fr; }}}} }}}}
.algo-h2 {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2rem,3.5vw,2.8rem); font-weight: 800;
  letter-spacing: -1px; color: var(--wit);
  margin-bottom: 20px; line-height: 1.1;
}}}}
.algo-h2 em {{{{ color: var(--oranje); font-style: normal; }}}}
.algo-tekst {{{{ font-size: 0.9rem; color: var(--grijs); line-height: 1.75; margin-bottom: 28px; }}}}
.algo-pijlers {{{{ display: flex; flex-direction: column; gap: 10px; }}}}
.algo-pijler {{{{
  background: var(--kaart); border-radius: 10px;
  padding: 14px 18px; border: 1px solid var(--rand);
  display: flex; align-items: center; gap: 14px;
}}}}
.pijler-nr {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 0.75rem; font-weight: 800;
  color: var(--oranje); min-width: 24px;
}}}}
.pijler-naam {{{{ font-size: 0.85rem; font-weight: 600; color: var(--wit); margin-bottom: 2px; }}}}
.pijler-sub {{{{ font-size: 0.72rem; color: var(--grijs); }}}}
.algo-score-kaart {{{{
  background: var(--kaart); border-radius: 16px;
  padding: 28px; border: 1px solid var(--rand);
}}}}
.algo-score-titel {{{{ font-size: 0.65rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--grijs); margin-bottom: 16px; }}}}
.algo-score-getal {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 5rem; font-weight: 800; color: var(--oranje); line-height: 1;
  margin-bottom: 4px;
}}}}
.algo-score-sub {{{{ font-size: 0.78rem; color: var(--grijs); margin-bottom: 24px; }}}}
.algo-bars {{{{ display: flex; flex-direction: column; gap: 10px; }}}}
.algo-bar-rij {{{{ display: flex; flex-direction: column; gap: 4px; }}}}
.algo-bar-label {{{{ display: flex; justify-content: space-between; font-size: 0.7rem; }}}}
.algo-bar-lbl-naam {{{{ color: #aaa; }}}}
.algo-bar-lbl-pts {{{{ color: var(--oranje); font-weight: 600; }}}}
.algo-bar-track {{{{
  background: var(--rand); border-radius: 3px; height: 5px;
}}}}
.algo-bar-fill {{{{ height: 100%; border-radius: 3px; background: var(--oranje); transition: width 1s ease; }}}}

/* ── ABOUT ── */
.about-sectie {{{{
  padding: clamp(80px,12vw,120px) clamp(20px,6vw,100px);
  max-width: 1300px; margin: 0 auto;
}}}}
.about-grid {{{{
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 80px; align-items: center;
}}}}
@media(max-width:900px){{{{ .about-grid {{{{ grid-template-columns:1fr; }}}} }}}}
.about-foto-wrap {{{{ position: relative; }}}}
.about-foto {{{{
  width:100%; aspect-ratio:4/5; border-radius:16px;
  background:linear-gradient(160deg,#f97316 0%,#1e293b 60%,#0f172a 100%);
  display:flex; align-items:center; justify-content:center;
  font-size: 4rem; color: rgba(255,255,255,0.1);
}}}}
.about-badge {{{{
  position:absolute; bottom:20px; left:20px; right:20px;
  background:rgba(245,243,239,0.95); backdrop-filter:blur(10px);
  border-radius:12px; padding:14px 16px;
  display:flex; align-items:center; gap:12px;
}}}}
.badge-dot {{{{ width:8px; height:8px; border-radius:50%; background:var(--oranje); flex-shrink:0; animation:blink 2s ease infinite; }}}}
@keyframes blink {{{{ 0%,100%{{{{opacity:1;}}}} 50%{{{{opacity:.3;}}}} }}}}
.badge-titel {{{{ font-size:.85rem; font-weight:800; color:#0c0c0c; }}}}
.badge-sub {{{{ font-size:.7rem; color:#666; margin-top:2px; }}}}
.about-h2 {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(1.8rem,3.5vw,2.8rem); font-weight: 800;
  letter-spacing: -1px; color: var(--wit);
  margin-bottom: 20px; line-height: 1.1;
}}}}
.about-tekst {{{{ font-size: 0.9rem; color: var(--grijs); line-height: 1.75; margin-bottom: 16px; }}}}
.about-quote {{{{
  border-left: 3px solid var(--oranje); padding-left: 20px; margin-top: 28px;
}}}}
.about-quote p {{{{ font-size: 1rem; color: var(--wit); font-style: italic; line-height: 1.6; margin-bottom: 8px; }}}}
.about-quote cite {{{{ font-size: 0.8rem; color: var(--oranje); font-style: normal; font-weight: 700; }}}}

/* ── CTA ── */
.cta-sectie {{{{
  background: var(--oranje);
  padding: clamp(80px,14vw,140px) clamp(20px,6vw,100px);
  text-align: center;
}}}}
.cta-h2 {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.5rem,5vw,4.5rem); font-weight: 800;
  letter-spacing: -2px; color: var(--zwart);
  margin-bottom: 20px; line-height: 1.0;
}}}}
.cta-sub {{{{ font-size: 1rem; color: rgba(12,12,12,0.6); margin-bottom: 40px; max-width: 400px; margin-left:auto; margin-right:auto; line-height:1.7; }}}}
.btn-dark {{{{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1rem; font-weight: 700; color: var(--oranje);
  background: var(--zwart); padding: 16px 36px; border-radius: 10px;
  text-decoration: none; display: inline-flex; align-items: center; gap: 10px;
  transition: transform 0.15s, box-shadow 0.2s;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}}}}
.btn-dark:hover {{{{ transform: translateY(-2px); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }}}}
.cta-proof {{{{ display:flex; justify-content:center; gap:24px; margin-top:28px; flex-wrap:wrap; }}}}
.cta-proof-item {{{{ font-size:.8rem; color:rgba(12,12,12,0.5); display:flex; align-items:center; gap:5px; }}}}
.cta-proof-item::before {{{{ content:'✓'; color:var(--zwart); font-weight:700; }}}}

/* ── FOOTER ── */
footer {{{{
  background: var(--zwart);
  border-top: 1px solid var(--rand);
  padding: 28px clamp(20px,5vw,80px);
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;
}}}}
.f-logo {{{{ font-family:'Bebas Neue',sans-serif; font-size:1.1rem; font-weight:800; color:var(--wit); }}}}
.f-logo span {{{{ color:var(--oranje); }}}}
.f-copy {{{{ font-size:.75rem; color:#444; }}}}

/* ── ANIMATIES ── */
@keyframes fadeUp {{{{ from{{{{opacity:0;transform:translateY(20px);}}}} to{{{{opacity:1;transform:translateY(0);}}}} }}}}
.hero-tag, .hero h1, .hero-sub, .hero-cta, .hero-proof {{{{
  animation: fadeUp 0.7s ease both;
}}}}
.hero h1 {{{{ animation-delay: 0.08s; }}}}
.hero-sub {{{{ animation-delay: 0.16s; }}}}
.hero-cta {{{{ animation-delay: 0.24s; }}}}
.hero-proof {{{{ animation-delay: 0.32s; }}}}

    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<!-- NAV -->
<nav>
  <a href="#" class="nav-logo">Car<span>b</span>oo</a>
  <div class="nav-tag">Sports Nutrition Coach</div>
  <div class="nav-right">
    <a href="javascript:void(0)" onclick="window.top.location.href=window.top.location.pathname+'?actie=register'" class="nav-login">Inloggen</a>
    <a href="javascript:void(0)" onclick="window.top.location.href=window.top.location.pathname+'?actie=register'" class="btn-cta">Gratis starten →</a>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div>
    <div class="hero-tag">Voeding × Prestatie</div>
    <h1>Eet zoals<br>je traint.<br><em>Met een plan.</em></h1>
    <p class="hero-sub">Periodiseer je voeding op basis van je trainingsbelasting. Stop met gissen. Begin met fuelen.</p>
    <div class="hero-cta">
      <a href="javascript:void(0)" onclick="window.top.location.href=window.top.location.pathname+'?actie=register'" class="btn-primary">Gratis starten →</a>
      <a href="#fueling" class="btn-ghost">Bekijk features ↓</a>
    </div>
    <div class="hero-proof">
      <div class="proof-item">7 dagen gratis</div>
      <div class="proof-item">Geen creditcard</div>
      <div class="proof-item">€9,99/maand</div>
    </div>
  </div>
  <div class="hero-right">
    <div class="mockup">
      <div class="mock-bar">
        <div class="dot" style="background:#ff5f57"></div>
        <div class="dot" style="background:#febc2e"></div>
        <div class="dot" style="background:#28c840"></div>
        <div class="mock-url">carboo.app/dagschema</div>
      </div>
      <div class="mock-body">
        <div class="ml">DAGSCHEMA — WOENSDAG</div>
        <div class="mt">Zware trainingsdag ⚡</div>
        <div class="mc">
          <div class="mc-card"><div class="mc-lbl">Kcal</div><div class="mc-val" style="color:#f97316">2840</div><div class="mc-bar" style="width:82%;background:#f97316"></div></div>
          <div class="mc-card"><div class="mc-lbl">KH</div><div class="mc-val" style="color:#22c55e">348g</div><div class="mc-bar" style="width:88%;background:#22c55e"></div></div>
          <div class="mc-card"><div class="mc-lbl">Eiwit</div><div class="mc-val" style="color:#3b82f6">162g</div><div class="mc-bar" style="width:91%;background:#3b82f6"></div></div>
        </div>
        <div class="mch-lbl">Energietiming vs trainingsbelasting</div>
        <div class="mch">
          <div class="mb" style="height:25%"></div>
          <div class="mb" style="height:20%"></div>
          <div class="mb a" style="height:90%"></div>
          <div class="mb" style="height:50%"></div>
          <div class="mb a" style="height:72%"></div>
          <div class="mb" style="height:30%"></div>
          <div class="mb" style="height:20%"></div>
        </div>
        <div class="mlist">
          <div class="mlist-item">🥗 Ontbijt op target <span>✓</span></div>
          <div class="mlist-item">⚡ Extra KH na training <span>+40g</span></div>
          <div class="mlist-item">💪 Eiwit vandaag <span>162g</span></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- APP OVERZICHT -->
<section class="app-sectie" id="app">
  <div class="sectie-lbl">De app</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:end;margin-bottom:0;">
    <div>
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-1px;color:var(--wit);line-height:1.1;">Drie pijlers.<br>Eén platform.</h2>
    </div>
    <div>
      <p style="font-size:0.9rem;color:var(--grijs);line-height:1.75;">Carboo bundelt dagelijkse voedingsbegeleiding, race-strategie en darmtraining in één intuïtieve app — gebouwd voor sporters die écht willen presteren.</p>
    </div>
  </div>
  <div class="app-grid">
    <div class="app-kaart">
      <div class="app-kaart-nr">01</div>
      <span class="app-kaart-icon">⚡</span>
      <div class="app-kaart-titel">Fueling</div>
      <p class="app-kaart-tekst">Jouw dagelijkse voedingscoach. Carboo berekent per dag hoeveel je nodig hebt op basis van training, lichaam en doelstelling — en past je macrodoelen automatisch aan.</p>
      <p class="app-kaart-tekst">Dagschema per maaltijdmoment, AI-etiketscan, 100+ NEVO-producten, community recepten en een eigen prestatie-algoritme dat je voedingskwaliteit beoordeelt.</p>
      <div class="app-kaart-tags">
        <span class="tag">Dagschema</span>
        <span class="tag">Macros</span>
        <span class="tag">Recepten</span>
        <span class="tag">Analyses</span>
      </div>
    </div>
    <div class="app-kaart">
      <div class="app-kaart-nr">02</div>
      <span class="app-kaart-icon">🏁</span>
      <div class="app-kaart-titel">Race Nutrition Plan</div>
      <p class="app-kaart-tekst">Bouw een stap-voor-stap voedingsstrategie voor je wedstrijddag. Carboo berekent je koolhydraatbehoefte per uur op basis van duur en intensiteit.</p>
      <p class="app-kaart-tekst">Plan je gels, bars, dranken en vast voedsel per checkpoint. Van sprintafstand tot Ironman — jij komt aan op de finish, niet bij het verzorgingspost.</p>
      <div class="app-kaart-tags">
        <span class="tag">g KH/uur</span>
        <span class="tag">Gel timing</span>
        <span class="tag">Hydratatie</span>
        <span class="tag">Per discipline</span>
      </div>
    </div>
    <div class="app-kaart">
      <div class="app-kaart-nr">03</div>
      <span class="app-kaart-icon">🫀</span>
      <div class="app-kaart-titel">Train the Gut</div>
      <p class="app-kaart-tekst">GI-klachten tijdens de wedstrijd? Je darmen hebben ook training nodig. Carboo begeleidt je door een gestructureerd darmtrainingsprotocol om koolhydraatopname te maximaliseren.</p>
      <div style="margin-top:20px;display:flex;flex-direction:column;gap:10px;">
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="color:#f97316;font-size:1.1rem;">▸</span>
          <span style="font-size:0.85rem;color:#aaa;">Wekelijkse tests op verschillende intensiteitsniveaus</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="color:#f97316;font-size:1.1rem;">▸</span>
          <span style="font-size:0.85rem;color:#aaa;">Trapsgewijs koolhydraatopname verhogen</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="color:#f97316;font-size:1.1rem;">▸</span>
          <span style="font-size:0.85rem;color:#aaa;">Zoek en test je perfecte wedstrijdstrategie</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- BEKENTENISSEN -->
<section class="bekentenis-sectie">
  <div class="bekentenis-inner">
    <div class="sectie-lbl">Herkenbaar?</div>
    <h2 class="bekentenis-titel">Je traint keihard.<br>Maar je voeding?<br>Dat is gissen.</h2>
    <div class="bekentenis-grid">
      <div class="bek-kaart">
        <span class="bek-kaart-emoji">🏃</span>
        <p class="bek-kaart-tekst">"Ik train 12 uur per week maar heb geen idee of ik genoeg eet om goed te herstellen."</p>
        <div style="font-size:0.72rem;color:var(--oranje);font-weight:600;margin-top:10px;">— Jonas V., triatleet</div>
      </div>
      <div class="bek-kaart">
        <span class="bek-kaart-emoji">🚴</span>
        <p class="bek-kaart-tekst">"Ik bonk op elke lange rit na 2 uur. Ik weet niet hoe ik dat moet voorkomen."</p>
        <div style="font-size:0.72rem;color:var(--oranje);font-weight:600;margin-top:10px;">— Silke D., wielrenster</div>
      </div>
      <div class="bek-kaart">
        <span class="bek-kaart-emoji">🏊</span>
        <p class="bek-kaart-tekst">"Als triatleet volg ik een dieet dat totaal niet aansluit bij mijn trainingsschema."</p>
        <div style="font-size:0.72rem;color:var(--oranje);font-weight:600;margin-top:10px;">— Pieter M., Ironman finisher</div>
      </div>
    </div>
    <div class="bek-strip">
      De meeste voedingsapps tellen calorieën. <strong>Carboo periodiseert je voeding mee met je training.</strong>
    </div>
  </div>
</section>

<!-- FUELING FEATURES -->
<section class="fueling-sectie" id="fueling">
  <div class="sectie-lbl">Fueling</div>
  <div class="fueling-header">
    <h2 class="fueling-h2">Dagelijks fuelen<br>zoals een <em>prof</em>.</h2>
    <p class="fueling-tekst">Carboo kijkt verder dan calorieën. Je krijgt een volledig dagschema dat aanpast aan trainings- en rustdagen, met persoonlijke macrodelen, maaltijdtiming en een wekelijks wisselend receptenaanbod van de community.</p>
  </div>
  <div class="fueling-grid">
    <div class="fuel-kaart">
      <div class="fuel-icon">📅</div>
      <div>
        <div class="fuel-kaart-titel">Slim dagschema per moment</div>
        <p class="fuel-kaart-tekst">Plan ontbijt, lunch, avondmaal en tussendoortjes afzonderlijk. Trainingsdag? Extra KH. Rustdag? Ander profiel. Automatisch.</p>
      </div>
    </div>
    <div class="fuel-kaart">
      <div class="fuel-icon">📷</div>
      <div>
        <div class="fuel-kaart-titel">AI etiketscan</div>
        <p class="fuel-kaart-tekst">Foto van een etiket — AI leest de voedingswaarden uit en voegt het product toe aan je bibliotheek. Geen handmatig invoeren meer.</p>
      </div>
    </div>
    <div class="fuel-kaart">
      <div class="fuel-icon">🍴</div>
      <div>
        <div class="fuel-kaart-titel">Elke week nieuwe recepten</div>
        <p class="fuel-kaart-tekst">De Carboo-community deelt wekelijks nieuwe recepten afgestemd op sporters. Bouw je eigen bibliotheek of gebruik die van anderen.</p>
      </div>
    </div>
    <div class="fuel-kaart">
      <div class="fuel-icon">📊</div>
      <div>
        <div class="fuel-kaart-titel">Micronutriënten analyse</div>
        <p class="fuel-kaart-tekst">Kalium, calcium, ijzer, vitamine D, B12, omega-3 — bijgehouden op basis van NEVO-waarden. Zie waar je tekort of overschot zit.</p>
      </div>
    </div>
    <div class="fuel-kaart">
      <div class="fuel-icon">🌍</div>
      <div>
        <div class="fuel-kaart-titel">Community recepten</div>
        <p class="fuel-kaart-tekst">Scoor, reageer en deel. Recepten van andere sporters, gefilterd op jouw doelstelling. Samen eten beter.</p>
      </div>
    </div>
    <div class="fuel-kaart">
      <div class="fuel-icon">💾</div>
      <div>
        <div class="fuel-kaart-titel">Opgeslagen dagschema's</div>
        <p class="fuel-kaart-tekst">Sla je perfecte trainingsdag of rustdag op als sjabloon. Laad het in één klik op elke gewenste datum.</p>
      </div>
    </div>
  </div>
</section>

<!-- ALGORITME SECTIE -->
<section class="algo-sectie">
  <div class="algo-inner">
    <div class="sectie-lbl">Eigen algoritme</div>
    <div class="algo-grid">
      <div>
        <h2 class="algo-h2">Voeding × Prestatie.<br>Elke dag <em>gemeten</em>.</h2>
        <p class="algo-tekst">Carboo berekent dagelijks een performance score van 0 tot 100 op basis van zes voedingspijlers — wetenschappelijk onderbouwd, afgestemd op jouw profiel en doelstelling.</p>
        <p class="algo-tekst">Geen vage adviezen. Geen standaard dieetregels. Een concreet getal per dag, met een breakdown per pijler en een duidelijk verbeterpunt.</p>
        <div class="algo-pijlers">
          <div class="algo-pijler">
            <div class="pijler-nr">01</div>
            <div>
              <div class="pijler-naam">Energiebalans</div>
            </div>
          </div>
          <div class="algo-pijler">
            <div class="pijler-nr">02</div>
            <div>
              <div class="pijler-naam">Macrokwaliteit</div>
            </div>
          </div>
          <div class="algo-pijler">
            <div class="pijler-nr">03</div>
            <div>
              <div class="pijler-naam">Micronutriëntendichtheid</div>
            </div>
          </div>
          <div class="algo-pijler">
            <div class="pijler-nr">04</div>
            <div>
              <div class="pijler-naam">Maaltijdtiming</div>
            </div>
          </div>
          <div class="algo-pijler">
            <div class="pijler-nr">05</div>
            <div>
              <div class="pijler-naam">Voedingskwaliteit</div>
            </div>
          </div>
          <div class="algo-pijler">
            <div class="pijler-nr">06</div>
            <div>
              <div class="pijler-naam">Hydratatie & GI</div>
            </div>
          </div>
        </div>

      </div>
      <div>
        <div class="algo-score-kaart">
          <div class="algo-score-titel">PRESTATIE SCORE — VANDAAG</div>
          <div class="algo-score-getal">82</div>
          <div class="algo-score-sub">/ 100 — Uitstekend</div>
          <div class="algo-bars">
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">⚡ Energiebalans</span>
                <span class="algo-bar-lbl-pts">18/20</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:90%"></div></div>
            </div>
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">🥗 Macrokwaliteit</span>
                <span class="algo-bar-lbl-pts">20/25</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:80%"></div></div>
            </div>
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">💊 Micronutriënten</span>
                <span class="algo-bar-lbl-pts">16/20</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:80%"></div></div>
            </div>
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">📅 Maaltijdtiming</span>
                <span class="algo-bar-lbl-pts">14/15</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:93%"></div></div>
            </div>
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">🌿 Voedingskwaliteit</span>
                <span class="algo-bar-lbl-pts">9/15</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:60%"></div></div>
            </div>
            <div class="algo-bar-rij">
              <div class="algo-bar-label">
                <span class="algo-bar-lbl-naam">💧 Hydratatie</span>
                <span class="algo-bar-lbl-pts">5/5</span>
              </div>
              <div class="algo-bar-track"><div class="algo-bar-fill" style="width:100%"></div></div>
            </div>
          </div>
          <div style="margin-top:16px;background:#1e1e1e;border-radius:8px;padding:12px;border-left:3px solid #f97316;">
            <div style="font-size:0.65rem;font-weight:700;color:#f97316;margin-bottom:4px;">💡 VERBETERPUNT</div>
            <div style="font-size:0.78rem;color:#888;line-height:1.5;">Meer variatie in voedingsgroepen. Voeg peulvruchten of extra groenten toe aan je lunch.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ABOUT -->
<section class="about-sectie">
  <div class="sectie-lbl">Achter Carboo</div>
  <div class="about-grid" style="grid-template-columns:1fr;max-width:720px;margin:0 auto;">
    <div>
      <h2 class="about-h2">Gebouwd vanuit de praktijk, voor de sporter.</h2>
      <p class="about-tekst">Carboo is ontwikkeld door een erkend sportdiëtist met jarenlange ervaring in voedingsperiodisering voor duursporters. Geen theoretisch model — een tool gebouwd vanuit de praktijk.</p>
      <p class="about-tekst">Elke functie, elk algoritme, elke aanbeveling is gebaseerd op echte atleten en echte prestaties.</p>
      <div class="about-quote">
        <p>"Ik bouwde de tool die ik zelf nodig had voor mijn atleten."</p>
        <cite>— Oprichter, Carboo</cite>
      </div>
    </div>
  </div>
</section>

<!-- CTA -->
<section class="cta-sectie">
  <h2 class="cta-h2">Klaar om te fuelen<br>zoals een prof?</h2>
  <p class="cta-sub">Maak een gratis account aan en ontdek wat Carboo voor jouw prestaties kan doen.</p>
  <a href="javascript:void(0)" onclick="window.top.location.href=window.top.location.pathname+'?actie=register'" class="btn-dark">Gratis starten →</a>
  <div class="cta-proof">
    <div class="cta-proof-item">7 dagen gratis</div>
    <div class="cta-proof-item">Geen creditcard</div>
    <div class="cta-proof-item">Annuleer wanneer je wil</div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="f-logo">Car<span>b</span>oo</div>
  <div class="f-copy">© 2025 Carboo · Sports Nutrition Coach · Alle rechten voorbehouden</div>
</footer>

<script>
// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});
</script>""", unsafe_allow_html=True)



# ─── LOGIN PAGINA ─────────────────────────────────────────────────────────────
def render_login_page():
    # Tab voorkeur (register of login)
    tab_voorkeur = st.session_state.pop("_login_tab", "register")

    st.markdown("""
    <div style="max-width:420px;margin:60px auto 0 auto;">
      <div style="text-align:center;margin-bottom:30px;">
        <div style="font-size:2.5rem;font-weight:900;letter-spacing:4px;color:#f8fafc;">
          CAR<span style="color:#f97316;">BOO</span>
        </div>
        <div style="font-size:0.8rem;color:#64748b;letter-spacing:2px;margin-top:4px;">
          SPORTS NUTRITION COACH
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Terug naar home", key="terug_landing"):
        st.session_state["toon_landing"] = True
        st.rerun()

    if tab_voorkeur == "login":
        tab_inloggen, tab_registreren = st.tabs(["  Inloggen  ", "  Registreren  "])
    else:
        tab_registreren, tab_inloggen = st.tabs(["  Registreren  ", "  Inloggen  "])

    with tab_registreren:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:1rem;font-weight:700;color:#f8fafc;margin-bottom:4px;">Maak een account aan</div>
            <div style="font-size:0.82rem;color:#94a3b8;">en begin meteen met je schema</div>
        </div>""", unsafe_allow_html=True)
        r_naam  = st.text_input("Naam", key="reg_naam", placeholder="Voornaam en naam")
        r_email = st.text_input("E-mailadres", key="reg_email", placeholder="jouw@email.com")
        r_ww    = st.text_input("Wachtwoord", type="password", key="reg_ww")
        r_ww2   = st.text_input("Herhaal wachtwoord", type="password", key="reg_ww2")
        r_code  = st.text_input("Promotiecode (optioneel)", key="reg_code",
                                placeholder="bijv. CARBOO2026",
                                help="Heb je een promotiecode? Vul die hier in voor een gratis rapport.")
        if st.button("Account aanmaken →", key="reg_btn", use_container_width=True):
            if not all([r_naam, r_email, r_ww, r_ww2]):
                st.error("Vul alle velden in.")
            elif r_ww != r_ww2:
                st.error("Wachtwoorden komen niet overeen.")
            elif len(r_ww) < 6:
                st.error("Wachtwoord moet minstens 6 tekens zijn.")
            else:
                try:
                    sb = _get_supabase()
                    try:
                        bestaande = sb.table("carboo_users").select("id").eq("email", r_email.lower().strip()).execute()
                        if bestaande.data:
                            st.error("Dit e-mailadres is al geregistreerd. Gebruik de Inloggen tab.")
                            st.stop()
                    except: pass
                    promo_data = None
                    if r_code and r_code.strip():
                        promo_data = controleer_promo_code(r_code.strip())
                        if not promo_data:
                            st.warning("⚠️ Ongeldige promotiecode. Registratie gaat door zonder code.")
                    result = sb.table("carboo_users").insert({
                        "email": r_email.lower().strip(), "naam": r_naam.strip(),
                        "wachtwoord": _hash(r_ww), "rol": "user", "credits": 0,
                    }).execute()
                    if result.data:
                        new_user = result.data[0]
                        if promo_data:
                            gebruik_promo_code(promo_data["id"], new_user["id"], promo_data["credits"])
                        try: _stuur_registratie_mail(r_naam.strip(), r_email.lower().strip())
                        except: pass
                        st.session_state.logged_in    = True
                        st.session_state.current_user = new_user
                        st.session_state.module       = "menu"
                        if promo_data:
                            st.session_state["_welkom_promo"] = promo_data["credits"]
                except Exception as e:
                    st.error(f"Fout bij registratie: {e}")

    with tab_inloggen:
        st.markdown("<br>", unsafe_allow_html=True)
        email = st.text_input("E-mailadres", key="login_email", placeholder="jouw@email.com")
        ww    = st.text_input("Wachtwoord", type="password", key="login_ww")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        col_in, col_verg = st.columns([2, 1])
        with col_in:
            login_klik = st.button("Inloggen →", key="login_btn", use_container_width=True)
        with col_verg:
            verg_klik = st.button("Vergeten?", key="login_verg", use_container_width=True)
        if verg_klik:
            st.session_state["toon_reset"] = True
        if st.session_state.get("toon_reset"):
            verg_email = st.text_input("Vul je e-mailadres in voor reset", key="verg_email")
            if st.button("📧 Stuur resetlink", key="stuur_reset", use_container_width=True):
                stuur_reset_mail(verg_email)
                st.success("Als dit e-mailadres bestaat, ontvang je een resetlink.")
                st.session_state.pop("toon_reset", None)
        if login_klik:
            if not email or not ww:
                st.error("Vul alle velden in.")
            else:
                user = _get_user(email)
                if not user:
                    st.error("Gebruiker niet gevonden.")
                elif user["wachtwoord"] != _hash(ww) and user["wachtwoord"] != ww:
                    st.error("Verkeerd wachtwoord.")
                else:
                    st.session_state.logged_in    = True
                    st.session_state.current_user = {
                        "id": user["id"], "name": user["naam"],
                        "email": user["email"], "role": user["rol"],
                        "credits": user["credits"],
                    }
                    st.rerun()


# ─── ADMIN PANEL ──────────────────────────────────────────────────────────────
def render_admin_panel():
    st.markdown('<div style="font-size:1.2rem;font-weight:900;color:#f97316;margin-bottom:20px;">⚙️ ADMIN PANEL</div>', unsafe_allow_html=True)
    try:
        sb = _get_supabase()
        users = sb.table("carboo_users").select("*").order("aangemaakt", desc=True).execute().data
    except Exception as e:
        st.error(f"Fout: {e}"); return

    totaal_users   = len([u for u in users if u["rol"] == "user"])
    totaal_credits = sum(u["credits"] for u in users if u["rol"] == "user")
    try: alle_trans = sb.table("carboo_transacties").select("*").execute().data
    except: alle_trans = []
    trans_gebruik = [t for t in alle_trans if t["type"] == "gebruik"]
    trans_aankoop = [t for t in alle_trans if t["type"] == "aankoop"]
    omzet_credits = sum(abs(t["credits"]) for t in trans_aankoop)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👤 Gebruikers", totaal_users)
    with col2: st.metric("📄 Rapporten", len(trans_gebruik))
    with col3: st.metric("🎟 Credits resterend", totaal_credits)
    with col4: st.metric("💰 Credits verkocht", omzet_credits)

    st.markdown("---")
    st.markdown('<div style="font-weight:800;color:#f97316;margin-bottom:8px;">📊 RECENTE ACTIVITEIT</div>', unsafe_allow_html=True)
    recente_trans = sorted(alle_trans, key=lambda x: x.get("datum",""), reverse=True)[:20]
    if recente_trans:
        user_map = {u["id"]: u["naam"] for u in users}
        for t in recente_trans:
            naam  = user_map.get(t.get("user_id",""), "?")
            datum = str(t.get("datum",""))[:16]
            cred  = t["credits"]
            kleur = "#22c55e" if cred > 0 else "#ef4444"
            icoon = "💰" if t["type"] == "aankoop" else ("📄" if t["type"] == "gebruik" else "🎁")
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:4px 8px;'
                f'border-bottom:1px solid #1e293b;font-size:0.82rem;">'
                f'<span style="color:#94a3b8">{datum}</span>'
                f'<span style="color:#f1f5f9">{icoon} {naam}</span>'
                f'<span style="color:#64748b">{t.get("beschrijving","")}</span>'
                f'<span style="color:{kleur};font-weight:bold">{cred:+d}</span></div>',
                unsafe_allow_html=True)
    else: st.info("Nog geen transacties.")

    st.markdown("---")
    with st.expander("➕ Nieuwe gebruiker toevoegen"):
        c1, c2 = st.columns(2)
        with c1:
            n_naam  = st.text_input("Naam", key="admin_naam")
            n_email = st.text_input("E-mail", key="admin_email")
        with c2:
            n_ww      = st.text_input("Wachtwoord", key="admin_ww", type="password")
            n_credits = st.number_input("Credits", 0, 999, 5, key="admin_credits")
            n_rol     = st.selectbox("Rol", ["user", "admin"], key="admin_rol")
        if st.button("Gebruiker aanmaken", key="admin_add", use_container_width=True):
            if not all([n_naam, n_email, n_ww]): st.error("Vul alle velden in.")
            elif _get_user(n_email): st.error("E-mail bestaat al.")
            else:
                try:
                    result = sb.table("carboo_users").insert({
                        "email": n_email.lower().strip(), "naam": n_naam.strip(),
                        "wachtwoord": _hash(n_ww), "rol": n_rol, "credits": n_credits,
                    }).execute()
                    if result.data:
                        sb.table("carboo_transacties").insert({
                            "user_id": result.data[0]["id"], "type": "admin",
                            "credits": n_credits, "beschrijving": "Credits toegevoegd door admin",
                        }).execute()
                        st.success(f"✅ {n_naam} aangemaakt."); st.rerun()
                except Exception as e: st.error(f"Fout: {e}")

    st.markdown("---")
    st.markdown('<div style="font-weight:800;color:#f8fafc;margin-bottom:10px;">GEBRUIKERS</div>', unsafe_allow_html=True)
    for user in users:
        if user["rol"] == "admin": continue
        with st.expander(f"👤 {user['naam']}  —  {user['email']}  —  {user['credits']} credits"):
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                st.markdown(f'<div style="font-size:0.8rem;color:#64748b;">Aangemaakt: {str(user["aangemaakt"])[:10]}</div>', unsafe_allow_html=True)
            with col_b:
                extra = st.number_input("Credits toevoegen", 0, 100, 5, key=f"add_c_{user['id']}")
                if st.button("➕ Toevoegen", key=f"add_btn_{user['id']}", use_container_width=True):
                    if voeg_credits_toe(user["id"], extra, "Credits toegevoegd door admin"):
                        st.success(f"✅ {extra} credits toegevoegd."); st.rerun()
            with col_c:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑 Verwijderen", key=f"del_{user['id']}", use_container_width=True):
                    try:
                        sb.table("carboo_transacties").delete().eq("user_id", user["id"]).execute()
                        sb.table("carboo_users").delete().eq("id", user["id"]).execute()
                        st.success("Gebruiker verwijderd."); st.rerun()
                    except Exception as e: st.error(f"Fout: {e}")
            try:
                trans = sb.table("carboo_transacties").select("*").eq("user_id", user["id"]).order("datum", desc=True).limit(5).execute().data
                if trans:
                    st.markdown('<div style="font-size:0.75rem;color:#64748b;margin-top:8px;">LAATSTE TRANSACTIES</div>', unsafe_allow_html=True)
                    for t in trans:
                        kleur = "#22c55e" if t["credits"] > 0 else "#ef4444"
                        st.markdown(
                            f'<div style="font-size:0.78rem;display:flex;justify-content:space-between;padding:2px 0;">'
                            f'<span style="color:#94a3b8">{str(t["datum"])[:10]} — {t["beschrijving"]}</span>'
                            f'<span style="color:{kleur};font-weight:bold">{t["credits"]:+d}</span></div>',
                            unsafe_allow_html=True)
            except: pass

    st.markdown("---")
    st.markdown('<div style="font-weight:800;color:#f97316;margin-bottom:12px;font-size:1rem;">🎟 PROMO CODES</div>', unsafe_allow_html=True)
    codes = get_alle_codes()
    if codes:
        for c in codes:
            kleur  = "#22c55e" if c.get("actief") else "#ef4444"
            status = "✅ Actief" if c.get("actief") else "❌ Inactief"
            verval = c.get("vervaldatum","—") or "—"
            st.markdown(f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                        padding:10px 14px;margin-bottom:8px;display:flex;
                        justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div><span style="font-family:monospace;font-weight:700;color:#f97316;font-size:1rem;">{c['code']}</span>
                    <span style="color:#64748b;font-size:0.8rem;margin-left:10px;">{c.get('firma','—')}</span></div>
                <div style="display:flex;gap:16px;align-items:center;font-size:0.8rem;">
                    <span style="color:#94a3b8;">🎟 {c.get('credits',1)} credit(s)</span>
                    <span style="color:#94a3b8;">👥 {c.get('gebruik',0)}/{c.get('max_gebruik',100)}</span>
                    <span style="color:#94a3b8;">📅 {verval}</span>
                    <span style="color:{kleur};">{status}</span>
                </div></div>""", unsafe_allow_html=True)
            ca, cb = st.columns([1,1])
            with ca:
                if c.get("actief"):
                    if st.button("⏸ Deactiveer", key=f"deact_{c['id']}", use_container_width=True):
                        toggle_code_actief(c["id"], False); st.rerun()
                else:
                    if st.button("▶ Activeer", key=f"act_{c['id']}", use_container_width=True):
                        toggle_code_actief(c["id"], True); st.rerun()
    else: st.info("Nog geen promo codes aangemaakt.")

    st.markdown('<div style="font-weight:600;color:#f1f5f9;margin:16px 0 8px;">Nieuwe code aanmaken</div>', unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        n_code    = st.text_input("Code", placeholder="bijv. DECATHLON2026", key="new_code").upper()
        n_firma   = st.text_input("Firma / organisatie", placeholder="bijv. Decathlon", key="new_firma")
        n_credits = st.number_input("Gratis credits", 1, 10, 1, key="new_credits")
    with nc2:
        n_max    = st.number_input("Max. gebruik", 1, 10000, 100, key="new_max")
        n_verval = st.date_input("Vervaldatum", key="new_verval")
    if st.button("✅ Code aanmaken", key="code_aanmaken", use_container_width=True):
        if not n_code or not n_firma: st.error("Vul code en firma in.")
        else:
            if maak_code_aan(n_code, n_firma, n_credits, n_max, str(n_verval)):
                st.success(f"✅ Code '{n_code}' aangemaakt!"); st.rerun()
            else: st.error("Code al in gebruik of fout opgetreden.")

    if st.button("← Terug naar menu", key="admin_terug"):
        st.session_state.module = "menu"; st.rerun()
