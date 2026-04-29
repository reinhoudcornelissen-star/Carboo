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

# ─── Abonnement & Trial ───────────────────────────────────────────────────────
from datetime import date, datetime, timedelta

def get_abonnement(user_id: str) -> dict:
    """Haal abonnement status op. Geeft dict terug met actieve modules."""
    user = _get_user_by_id(user_id)
    if not user:
        return {"trial": False, "fueling": False, "gut": False, "rapport": False, "alles": False}

    abo       = user.get("abonnement") or "geen"
    verval    = user.get("abo_verval")
    abo_cred  = int(user.get("abo_credits") or 0)
    credits   = int(user.get("credits") or 0)

    # Check of verval nog geldig is
    actief = False
    if verval:
        try:
            verval_dt = date.fromisoformat(str(verval)[:10])
            actief = verval_dt >= date.today()
        except: actief = False

    is_trial   = abo == "trial" and actief
    is_alles   = abo == "alles" and actief
    is_fueling = abo in ("alles", "fueling") and actief
    is_gut     = abo in ("alles", "gut") and actief
    heeft_rapport = credits > 0 or (is_alles and abo_cred > 0)

    return {
        "trial":   is_trial,
        "alles":   is_alles,
        "fueling": is_fueling or is_trial or is_alles,
        "gut":     is_gut or is_trial or is_alles,
        "rapport": heeft_rapport,
        "abo":     abo,
        "verval":  str(verval)[:10] if verval else None,
        "abo_credits": abo_cred,
        "dagen_resterend": (date.fromisoformat(str(verval)[:10]) - date.today()).days if verval and actief else 0,
    }

def activeer_trial(user_id: str) -> bool:
    """Activeer 7-daagse trial bij registratie."""
    try:
        verval = (date.today() + timedelta(days=7)).isoformat()
        _get_supabase().table("carboo_users").update({
            "abonnement": "trial",
            "abo_verval": verval,
            "abo_credits": 0,
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Trial activatie fout: {e}"); return False

def activeer_abonnement(user_id: str, pakket: str, maanden: int = 1) -> bool:
    """Activeer een betaald abonnement."""
    try:
        # Maandelijks rapport credit bij alles-in-1
        abo_credits = 1 if pakket == "alles" else 0
        verval = (date.today() + timedelta(days=30 * maanden)).isoformat()
        _get_supabase().table("carboo_users").update({
            "abonnement": pakket,
            "abo_verval": verval,
            "abo_credits": abo_credits,
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Abonnement activatie fout: {e}"); return False

def render_login_page():
    tab_voorkeur = st.session_state.pop("_login_tab", "register")
    if tab_voorkeur == "login":
        st.session_state["_actieve_tab"] = "login"
    actieve_tab = st.session_state.get("_actieve_tab", "register")

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

    if actieve_tab == "login":
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
        r_code  = st.text_input("Promotiecode (optioneel)", key="reg_code", placeholder="bijv. CARBOO2026")
        st.markdown(
            '<div style="font-size:0.8rem;color:#64748b;margin:8px 0;">'
            '<a href="?actie=disclaimer" target="_blank" style="color:#f97316;">'
            'Lees onze gebruiksvoorwaarden & disclaimer</a></div>',
            unsafe_allow_html=True)
        r_akkoord = st.checkbox("Ik ga akkoord met de gebruiksvoorwaarden & disclaimer", key="reg_akkoord")
        if st.button("Account aanmaken →", key="reg_btn", use_container_width=True):
            if not r_akkoord:
                st.error("Je moet akkoord gaan met de gebruiksvoorwaarden.")
            elif not all([r_naam, r_email, r_ww, r_ww2]):
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
                        activeer_trial(new_user["id"])
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
                    st.session_state.pop("_actieve_tab", None)
                    st.session_state.logged_in    = True
                    st.session_state.current_user = {
                        "id": user["id"], "name": user["naam"],
                        "email": user["email"], "role": user["rol"],
                        "credits": user["credits"],
                    }
                    st.rerun()


def render_abonnement_keuze(user_id: str, user_email: str):
    """Toon abonnementskeuze als trial verlopen is."""
    st.markdown("""
    <div style="max-width:700px;margin:40px auto 0 auto;text-align:center;">
      <div style="font-size:2.5rem;font-weight:900;letter-spacing:4px;color:#f8fafc;margin-bottom:8px;">
        CAR<span style="color:#f97316;">BOO</span>
      </div>
      <div style="font-size:0.82rem;color:#64748b;margin-bottom:8px;">Je gratis proefperiode is afgelopen.</div>
      <div style="font-size:1.1rem;font-weight:700;color:#f8fafc;margin-bottom:32px;">Kies je pakket om verder te gaan.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background:#1e293b;border:2px solid #f97316;border-radius:12px;padding:20px;text-align:center;height:260px;box-sizing:border-box;">
          <div style="font-size:0.6rem;color:#f97316;font-weight:700;letter-spacing:2px;margin-bottom:8px;">POPULAIRSTE</div>
          <div style="font-size:0.9rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">Alles-in-1</div>
          <div style="font-size:1.8rem;font-weight:900;color:#f97316;margin:8px 0;">€9,99</div>
          <div style="font-size:0.65rem;color:#64748b;margin-bottom:12px;">/maand</div>
          <div style="font-size:0.72rem;color:#94a3b8;line-height:1.8;">
            ⚡ Fueling<br>🧪 Train the Gut<br>🏁 1 wedstrijdrapport/maand
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Kies Alles-in-1", key="abo_alles", use_container_width=True, type="primary"):
            st.session_state["_abo_keuze"] = "alles"
            st.session_state["_abo_prijs"] = 9.99
            st.session_state.module = "credits"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;height:260px;box-sizing:border-box;">
          <div style="font-size:0.6rem;color:#64748b;font-weight:700;letter-spacing:2px;margin-bottom:8px;">&nbsp;</div>
          <div style="font-size:0.9rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">Fueling</div>
          <div style="font-size:1.8rem;font-weight:900;color:#f97316;margin:8px 0;">€5,99</div>
          <div style="font-size:0.65rem;color:#64748b;margin-bottom:12px;">/maand</div>
          <div style="font-size:0.72rem;color:#94a3b8;line-height:1.8;">
            ⚡ Dagschema<br>📊 Analyses<br>🍽️ Voedselbibliotheek
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Kies Fueling", key="abo_fueling", use_container_width=True):
            st.session_state["_abo_keuze"] = "fueling"
            st.session_state["_abo_prijs"] = 5.99
            st.session_state.module = "credits"
            st.rerun()

    with col3:
        st.markdown("""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;height:260px;box-sizing:border-box;">
          <div style="font-size:0.6rem;color:#64748b;font-weight:700;letter-spacing:2px;margin-bottom:8px;">&nbsp;</div>
          <div style="font-size:0.9rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">Train the Gut</div>
          <div style="font-size:1.8rem;font-weight:900;color:#f97316;margin:8px 0;">€3,99</div>
          <div style="font-size:0.65rem;color:#64748b;margin-bottom:12px;">/maand</div>
          <div style="font-size:0.72rem;color:#94a3b8;line-height:1.8;">
            🧪 Darmprotocol<br>📈 Intensiteitstests<br>🏆 Wedstrijdstrategie
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Kies Train the Gut", key="abo_gut", use_container_width=True):
            st.session_state["_abo_keuze"] = "gut"
            st.session_state["_abo_prijs"] = 3.99
            st.session_state.module = "credits"
            st.rerun()

    with col4:
        st.markdown("""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;height:260px;box-sizing:border-box;">
          <div style="font-size:0.6rem;color:#64748b;font-weight:700;letter-spacing:2px;margin-bottom:8px;">&nbsp;</div>
          <div style="font-size:0.9rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">Wedstrijdrapport</div>
          <div style="font-size:1.8rem;font-weight:900;color:#f97316;margin:8px 0;">€4,99</div>
          <div style="font-size:0.65rem;color:#64748b;margin-bottom:12px;">/stuk</div>
          <div style="font-size:0.72rem;color:#94a3b8;line-height:1.8;">
            🏁 Race Nutrition Plan<br>📄 PDF rapport<br>⏱️ Uur-per-uur schema
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Koop rapport", key="abo_rapport", use_container_width=True):
            st.session_state["_abo_keuze"] = "credit"
            st.session_state["_abo_prijs"] = 4.99
            st.session_state.module = "credits"
            st.rerun()


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
        ontvanger = "Carboo"
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

def render_disclaimer():
    """Toont de volledige disclaimer/gebruiksvoorwaarden."""
    st.markdown("""
    <style>
    #MainMenu,header,footer{display:none!important}
    .block-container{max-width:800px!important;padding-top:2rem!important}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:24px;">
      <a href="/" style="font-size:0.82rem;color:#f97316;text-decoration:none;">← Terug naar Carboo</a>
    </div>
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:#f8fafc;letter-spacing:2px;margin-bottom:8px;">
      Car<span style="color:#f97316;">b</span>oo
    </div>
    <div style="font-size:0.7rem;color:#64748b;letter-spacing:2px;text-transform:uppercase;margin-bottom:40px;">
      Gebruiksvoorwaarden & Disclaimer
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **Laatste update:** april 2026

    ---

    ### 1. Geen medisch advies

    Carboo is een digitale sportvoedingstool ontwikkeld ter ondersteuning van duursporters.
    De berekeningen, schema's en aanbevelingen in de app zijn **geen vervanging voor professioneel
    medisch of diëtistisch advies**. Raadpleeg altijd een erkende professional bij gezondheidsproblemen,
    voedingsstoornissen of specifieke medische aandoeningen.

    ### 2. Gebruik op eigen verantwoordelijkheid

    De gebruiker is zelf verantwoordelijk voor de keuzes die hij of zij maakt op basis van de
    informatie in de app. Carboo en haar ontwikkelaars zijn niet aansprakelijk voor directe of
    indirecte schade die voortvloeit uit het gebruik van de applicatie.

    ### 3. Nauwkeurigheid van gegevens

    De voedingswaarden in Carboo zijn gebaseerd op de NEVO-databank en andere wetenschappelijke
    bronnen. Ondanks onze zorgvuldigheid kunnen afwijkingen voorkomen. Carboo geeft geen garantie
    op de absolute nauwkeurigheid van de getoonde waarden.

    ### 4. Persoonsgegevens & privacy

    Je persoonlijke gegevens (naam, e-mailadres, voedingsdata) worden uitsluitend gebruikt om
    de app correct te laten functioneren. We verkopen of delen jouw gegevens **nooit** met derden.
    Je kan je account en alle bijhorende data op elk moment laten verwijderen via een schriftelijk
    verzoek aan Carboo.

    ### 5. Intellectueel eigendom

    Alle content, algoritmen en ontwerpen in Carboo zijn exclusief eigendom van Carboo.
    Het is niet toegestaan om de app of delen ervan te kopiëren, reproduceren of commercieel te
    gebruiken zonder voorafgaande schriftelijke toestemming.

    ### 6. Technische beschikbaarheid & aansprakelijkheid

    Carboo maakt gebruik van externe hosting- en infrastructuurdiensten van derden. Carboo kan
    niet garanderen dat de applicatie te allen tijde ononderbroken, foutloos of volledig
    beschikbaar zal zijn.

    Carboo wijst uitdrukkelijk elke aansprakelijkheid af voor schade of verlies die voortvloeit uit:

    - tijdelijke of permanente onderbrekingen van de dienst ten gevolge van storingen, onderhoud
    of technische defecten bij externe dienstverleners;
    - verlies of beschadiging van gebruikersgegevens als gevolg van omstandigheden buiten de
    redelijke controle van Carboo;
    - schade van welke aard dan ook — direct, indirect, incidenteel of gevolgschade — die verband
    houdt met de gehele of gedeeltelijke onbeschikbaarheid van de applicatie.

    De gebruiker erkent dat het gebruik van een online applicatie inherent verbonden is aan een
    zeker risico op technische storingen en aanvaardt dit risico uitdrukkelijk bij aanvang van
    het gebruik van Carboo.

    ### 7. Wijzigingen

    Carboo behoudt het recht om deze voorwaarden op elk moment te wijzigen. Bij belangrijke
    wijzigingen word je via e-mail op de hoogte gesteld.

    ---

    *Door een account aan te maken bij Carboo aanvaard je deze gebruiksvoorwaarden volledig.*
    """)

    if st.button("← Terug", key="disclaimer_terug"):
        st.session_state["toon_landing"] = True
        st.rerun()


def render_landing_page():
    """Mooie landing/login pagina in Streamlit — mobile-first."""
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

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Instrument+Sans:wght@400;500;600&display=swap');
    #MainMenu,header,footer,.stDeployButton{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    .stApp{background:#0c0c0c!important}

    /* ── Mobile-first responsive ── */
    .cb-nav{
        position:sticky;top:0;z-index:100;width:100%;
        padding:14px 5vw;
        display:flex;align-items:center;justify-content:space-between;
        background:rgba(12,12,12,0.95);backdrop-filter:blur(16px);
        border-bottom:1px solid rgba(255,255,255,0.06);
        box-sizing:border-box;
    }
    .cb-nav-logo{font-family:'Bebas Neue',sans-serif;font-size:1.6rem;color:#f5f3ef;letter-spacing:1px;}
    .cb-nav-tag{font-size:0.55rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;
                color:#888;border:1px solid #2a2a2a;padding:3px 8px;border-radius:100px;}
    .cb-nav-right{display:flex;gap:8px;}
    .cb-nav-login{font-size:0.78rem;color:#888;text-decoration:none;padding:7px 12px;}
    .cb-btn-primary{font-size:0.78rem;font-weight:600;color:#0c0c0c;
                    background:#f97316;padding:7px 14px;border-radius:8px;text-decoration:none;}

    /* Hero */
    .cb-hero{
        padding:60px 5vw 50px;
        max-width:1300px;margin:0 auto;
        display:grid;grid-template-columns:1fr;gap:32px;
    }
    .cb-hero-tag{font-size:0.65rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;
                 color:#f97316;margin-bottom:20px;display:flex;align-items:center;gap:8px;}
    .cb-hero-tag::before{content:'';display:inline-block;width:20px;height:1px;background:#f97316;}
    .cb-hero h1{font-family:'Bebas Neue',sans-serif;font-size:clamp(2.8rem,10vw,6rem);
                line-height:0.95;letter-spacing:2px;color:#f5f3ef;margin:0 0 20px;}
    .cb-hero h1 em{color:#f97316;font-style:normal;}
    .cb-hero-sub{font-size:0.95rem;color:#888;line-height:1.75;margin-bottom:32px;max-width:420px;}
    .cb-hero-cta{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:24px;}
    .cb-btn-big{font-family:'Bebas Neue',sans-serif;font-size:0.95rem;
                color:#0c0c0c;background:#f97316;padding:12px 24px;
                border-radius:10px;text-decoration:none;letter-spacing:1px;}
    .cb-btn-ghost{font-size:0.85rem;color:#666;text-decoration:none;padding:12px 0;}
    .cb-hero-proof{display:flex;gap:16px;flex-wrap:wrap;}
    .cb-proof-item{font-size:0.72rem;color:#444;display:flex;align-items:center;gap:5px;}
    .cb-proof-item::before{content:'✓';color:#f97316;font-weight:700;}

    /* Mockup — verborgen op mobile */
    .cb-mockup-wrap{display:none;}

    /* Pijlers */
    .cb-pijlers{padding:50px 5vw;background:#141414;border-top:1px solid #2a2a2a;}
    .cb-pijlers-inner{max-width:1300px;margin:0 auto;}
    .cb-pijlers-lbl{font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                    color:#f97316;margin-bottom:24px;}
    .cb-pijlers-grid{display:grid;grid-template-columns:1fr;gap:2px;
                     border:1px solid #2a2a2a;border-radius:12px;overflow:hidden;}
    .cb-pijler{background:#1a1a1a;padding:28px 24px;position:relative;}
    .cb-pijler+.cb-pijler{border-top:2px solid #2a2a2a;}
    .cb-pijler-nr{font-family:'Bebas Neue',sans-serif;font-size:3.5rem;
                  color:rgba(249,115,22,0.07);position:absolute;top:12px;right:18px;line-height:1;}
    .cb-pijler-icon{font-size:1.6rem;margin-bottom:14px;}
    .cb-pijler-titel{font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#f5f3ef;
                     margin-bottom:10px;letter-spacing:1px;}
    .cb-pijler-tekst{font-size:0.84rem;color:#888;line-height:1.75;margin-bottom:16px;}
    .cb-tags{display:flex;gap:5px;flex-wrap:wrap;}
    .cb-tag{font-size:0.62rem;font-weight:600;color:#f97316;
            background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);
            padding:3px 8px;border-radius:100px;white-space:nowrap;}

    /* CTA */
    .cb-cta{background:#f97316;padding:70px 5vw;text-align:center;}
    .cb-cta h2{font-family:'Bebas Neue',sans-serif;font-size:clamp(2rem,8vw,4rem);
               color:#0c0c0c;margin:0 0 16px;letter-spacing:2px;line-height:1.05;}
    .cb-cta-sub{font-size:0.9rem;color:rgba(12,12,12,0.6);margin-bottom:32px;
                max-width:360px;margin-left:auto;margin-right:auto;line-height:1.7;}
    .cb-btn-dark{font-family:'Bebas Neue',sans-serif;font-size:0.95rem;font-weight:700;
                 color:#f97316;background:#0c0c0c;padding:14px 32px;border-radius:10px;
                 text-decoration:none;display:inline-block;letter-spacing:1px;}
    .cb-cta-proof{display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-top:20px;}
    .cb-cta-proof-item{font-size:0.7rem;color:rgba(12,12,12,0.5);}

    /* Footer */
    .cb-footer{background:#0c0c0c;border-top:1px solid #2a2a2a;padding:20px 5vw;
               display:flex;flex-direction:column;gap:8px;align-items:center;text-align:center;}
    .cb-footer-logo{font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#f5f3ef;letter-spacing:1px;}
    .cb-footer-copy{font-size:0.7rem;color:#444;}

    /* ── Tablet & Desktop ── */
    @media(min-width:768px){
        .cb-nav-tag{display:inline-block;}
        .cb-nav-login{font-size:0.82rem;}
        .cb-btn-primary{font-size:0.82rem;padding:9px 20px;}
        .cb-hero{padding:100px 6vw 80px;grid-template-columns:1fr 1fr;gap:60px;align-items:center;}
        .cb-mockup-wrap{display:block;}
        .cb-pijlers{padding:70px 6vw;}
        .cb-pijlers-grid{grid-template-columns:1fr 1fr 1fr;}
        .cb-pijler+.cb-pijler{border-top:none;border-left:2px solid #2a2a2a;}
        .cb-cta{padding:100px 6vw;}
        .cb-footer{flex-direction:row;justify-content:space-between;text-align:left;}
    }
    </style>

    <!-- NAV -->
    <div class="cb-nav">
      <div class="cb-nav-logo">Car<span style="color:#f97316;">b</span>oo</div>
      <div class="cb-nav-tag">Sports Nutrition Coach</div>
      <div class="cb-nav-right">
        <a href="?actie=login" class="cb-nav-login">Inloggen</a>
        <a href="?actie=register" class="cb-btn-primary">Gratis starten →</a>
      </div>
    </div>

    <!-- HERO -->
    <div class="cb-hero">
      <div>
        <div class="cb-hero-tag">Voeding × Prestatie</div>
        <h1>EET ZOALS<br>JE TRAINT.<br><em>MET EEN PLAN.</em></h1>
        <p class="cb-hero-sub">
          Periodiseer je voeding op basis van je trainingsbelasting.
          Stop met gissen. Begin met fuelen.
        </p>
        <div class="cb-hero-cta">
          <a href="?actie=register" class="cb-btn-big">GRATIS STARTEN →</a>
          <a href="?actie=login" class="cb-btn-ghost">Al een account? Inloggen ↗</a>
        </div>
        <div class="cb-hero-proof">
          <span class="cb-proof-item">7 dagen gratis</span>
          <span class="cb-proof-item">Geen creditcard</span>
          <span class="cb-proof-item">€9,99/maand</span>
        </div>
      </div>

      <!-- APP MOCKUP — enkel desktop -->
      <div class="cb-mockup-wrap">
        <div style="background:#111;border-radius:16px;overflow:hidden;
                    box-shadow:0 40px 100px rgba(0,0,0,0.6),0 0 0 1px rgba(255,255,255,0.06);
                    transform:perspective(1000px) rotateY(-3deg) rotateX(2deg);">
          <div style="background:#1a1a1a;padding:10px 14px;display:flex;align-items:center;gap:6px;
                      border-bottom:1px solid rgba(255,255,255,0.06);">
            <div style="width:9px;height:9px;border-radius:50%;background:#ff5f57;"></div>
            <div style="width:9px;height:9px;border-radius:50%;background:#febc2e;"></div>
            <div style="width:9px;height:9px;border-radius:50%;background:#28c840;"></div>
            <div style="flex:1;background:#222;border-radius:5px;padding:3px 10px;
                        font-size:0.6rem;color:#555;text-align:center;">carboo.app</div>
          </div>
          <div style="padding:18px;">
            <div style="font-size:.55rem;font-weight:700;color:#f97316;letter-spacing:2px;margin-bottom:8px;">DAGSCHEMA — WOENSDAG ⚡</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:14px;">
              <div style="background:#1e293b;border-radius:6px;padding:8px;">
                <div style="font-size:.5rem;color:#64748b;margin-bottom:2px;">KCAL</div>
                <div style="font-size:.9rem;font-weight:800;color:#f97316;">2840</div>
                <div style="height:3px;border-radius:2px;margin-top:4px;background:#f97316;width:82%;"></div>
              </div>
              <div style="background:#1e293b;border-radius:6px;padding:8px;">
                <div style="font-size:.5rem;color:#64748b;margin-bottom:2px;">KH</div>
                <div style="font-size:.9rem;font-weight:800;color:#22c55e;">348g</div>
                <div style="height:3px;border-radius:2px;margin-top:4px;background:#22c55e;width:88%;"></div>
              </div>
              <div style="background:#1e293b;border-radius:6px;padding:8px;">
                <div style="font-size:.5rem;color:#64748b;margin-bottom:2px;">EIWIT</div>
                <div style="font-size:.9rem;font-weight:800;color:#3b82f6;">162g</div>
                <div style="height:3px;border-radius:2px;margin-top:4px;background:#3b82f6;width:91%;"></div>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:4px;">
              <div style="display:flex;justify-content:space-between;align-items:center;font-size:.58rem;color:#94a3b8;background:#1e293b;border-radius:5px;padding:5px 8px;">
                🥗 Ontbijt op target <span style="color:#f97316;">✓</span></div>
              <div style="display:flex;justify-content:space-between;align-items:center;font-size:.58rem;color:#94a3b8;background:#1e293b;border-radius:5px;padding:5px 8px;">
                ⚡ Extra KH na training <span style="color:#f97316;">+40g</span></div>
              <div style="display:flex;justify-content:space-between;align-items:center;font-size:.58rem;color:#94a3b8;background:#1e293b;border-radius:5px;padding:5px 8px;">
                💪 Eiwit vandaag <span style="color:#f97316;">162g</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3 PIJLERS -->
    <div class="cb-pijlers">
      <div class="cb-pijlers-inner">
        <div class="cb-pijlers-lbl">De app</div>
        <div class="cb-pijlers-grid">
          <div class="cb-pijler">
            <div class="cb-pijler-nr">01</div>
            <div class="cb-pijler-icon">⚡</div>
            <div class="cb-pijler-titel">Fueling</div>
            <p class="cb-pijler-tekst">Dagschema op maat. Per training, per maaltijdmoment. 100+ NEVO-producten en een eigen prestatie-algoritme.</p>
            <div class="cb-tags">
              <span class="cb-tag">Dagschema</span>
              <span class="cb-tag">Micronutriënten</span>
              <span class="cb-tag">Prestatie-algoritme</span>
            </div>
          </div>
          <div class="cb-pijler">
            <div class="cb-pijler-nr">02</div>
            <div class="cb-pijler-icon">🏁</div>
            <div class="cb-pijler-titel">Race Nutrition Plan</div>
            <p class="cb-pijler-tekst">Stap-voor-stap voedingsstrategie voor je wedstrijddag. Van sprint tot Ironman.</p>
            <div class="cb-tags">
              <span class="cb-tag">Carboloading</span>
              <span class="cb-tag">Pre-racemeal</span>
              <span class="cb-tag">Raceplan</span>
            </div>
          </div>
          <div class="cb-pijler">
            <div class="cb-pijler-nr">03</div>
            <div class="cb-pijler-icon">🫀</div>
            <div class="cb-pijler-titel">Train the Gut</div>
            <p class="cb-pijler-tekst">Je darmen trainen voor maximale koolhydraatopname. Trapsgewijs protocol, wekelijkse tests.</p>
            <div class="cb-tags">
              <span class="cb-tag">KH Protocol</span>
              <span class="cb-tag">Intensiteitstests</span>
              <span class="cb-tag">Wedstrijdstrategie</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="cb-cta">
      <h2>KLAAR OM TE FUELEN<br>ZOALS EEN PROF?</h2>
      <p class="cb-cta-sub">Maak een gratis account aan en ontdek wat Carboo voor jouw prestaties kan doen.</p>
      <a href="?actie=register" class="cb-btn-dark">GRATIS STARTEN →</a>
      <div class="cb-cta-proof">
        <span class="cb-cta-proof-item">7 dagen gratis</span>
        <span class="cb-cta-proof-item">Geen creditcard</span>
        <span class="cb-cta-proof-item">Annuleer wanneer je wil</span>
      </div>
    </div>

    <!-- FOOTER -->
    <div class="cb-footer">
      <div class="cb-footer-logo">Car<span style="color:#f97316;">b</span>oo</div>
      <div class="cb-footer-copy">Sports Nutrition Coach · © 2026 · <a href="?actie=disclaimer" style="color:#555;text-decoration:none;">Gebruiksvoorwaarden</a></div>
    </div>
    """, unsafe_allow_html=True)




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

    from datetime import date as _date
    actieve_abos = [u for u in users if u.get("abonnement") and u.get("abo_verval") and u["rol"]=="user"
                    and str(u.get("abo_verval",""))[:10] >= str(_date.today())]
    trials  = [u for u in actieve_abos if u.get("abonnement") == "trial"]
    betaald = [u for u in actieve_abos if u.get("abonnement") != "trial"]
    col_a, col_b, col_c = st.columns(3)
    with col_a: st.metric("🔄 Actieve abos", len(betaald))
    with col_b: st.metric("⏱️ Trials actief", len(trials))
    with col_c: st.metric("💶 MRR", f"€{sum(9.99 if u.get('abonnement')=='alles' else 5.99 if u.get('abonnement')=='fueling' else 3.99 for u in betaald):.2f}")

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
            n_rol     = st.selectbox("Rol", ["user", "coach", "admin"], key="admin_rol")
        if st.button("Gebruiker aanmaken", key="admin_add", use_container_width=True):
            if not all([n_naam, n_email, n_ww]): st.error("Vul alle velden in.")
            elif _get_user(n_email): st.error("E-mail bestaat al.")
            else:
                try:
                    result = sb.table("carboo_users").insert({
                        "email": n_email.lower().strip(), "naam": n_naam.strip(),
                        "wachtwoord": _hash(n_ww), "rol": n_rol, "credits": n_credits,
                        "max_atleten": 700 if n_rol == "coach" else 0,
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
                if user.get("rol") == "coach":
                    max_a = st.number_input("Max. atleten", 0, 700, int(user.get("max_atleten") or 700), key=f"max_a_{user['id']}")
                    if st.button("💾 Opslaan", key=f"max_a_save_{user['id']}", use_container_width=True):
                        try:
                            _get_supabase().table("carboo_users").update({"max_atleten": max_a}).eq("id", user["id"]).execute()
                            st.success(f"✅ Max. atleten: {max_a}"); st.rerun()
                        except Exception as e: st.error(f"Fout: {e}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑 Verwijderen", key=f"del_{user['id']}", use_container_width=True):
                    try:
                        sb.table("carboo_transacties").delete().eq("user_id", user["id"]).execute()
                        sb.table("carboo_users").delete().eq("id", user["id"]).execute()
                        st.success("Gebruiker verwijderd."); st.rerun()
                    except Exception as e: st.error(f"Fout: {e}")

            # Abonnement beheer
            st.markdown('<div style="font-size:0.75rem;color:#64748b;margin-top:12px;margin-bottom:6px;">ABONNEMENT</div>', unsafe_allow_html=True)
            abo_huidig = user.get("abonnement") or "geen"
            verval_huidig = str(user.get("abo_verval","") or "—")[:10]
            abo_labels = {"trial":"Proefperiode","alles":"Alles-in-1","fueling":"Fueling","gut":"Train the Gut","geen":"Geen"}
            st.markdown(
                f'<div style="font-size:0.78rem;color:#f8fafc;margin-bottom:6px;">Huidig: '
                f'<b style="color:#f97316;">{abo_labels.get(abo_huidig, abo_huidig)}</b>'
                f' · Verval: <b>{verval_huidig}</b></div>', unsafe_allow_html=True)
            col_abo1, col_abo2 = st.columns([2,1])
            with col_abo1:
                nieuw_abo = st.selectbox("Abonnement instellen",
                    ["trial","alles","fueling","gut","geen"],
                    index=["trial","alles","fueling","gut","geen"].index(abo_huidig) if abo_huidig in ["trial","alles","fueling","gut","geen"] else 4,
                    key=f"abo_sel_{user['id']}")
                maanden = st.number_input("Maanden", 1, 12, 1, key=f"abo_mnd_{user['id']}")
            with col_abo2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✓ Activeren", key=f"abo_act_{user['id']}", use_container_width=True):
                    try:
                        from datetime import date, timedelta
                        verval_dt = (date.today() + timedelta(days=30*maanden)).isoformat()
                        abo_cred = 1 if nieuw_abo == "alles" else 0
                        _get_supabase().table("carboo_users").update({
                            "abonnement": nieuw_abo if nieuw_abo != "geen" else None,
                            "abo_verval": verval_dt if nieuw_abo != "geen" else None,
                            "abo_credits": abo_cred,
                        }).eq("id", user["id"]).execute()
                        st.success(f"✅ {abo_labels.get(nieuw_abo, nieuw_abo)} geactiveerd t/m {verval_dt}")
                        st.rerun()
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
