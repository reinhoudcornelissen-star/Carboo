import streamlit as st
import hashlib
from supabase import create_client


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _stuur_registratie_mail(naam: str, email: str):
    """Stuur notificatie mail naar admin bij nieuwe registratie."""
    try:
        ontvanger = "info@sportlab-achterbos.be"
        afzender  = _get_secrets("MAIL_FROM", "noreply@carboo.app")
        ww_mail   = _get_secrets("MAIL_PASSWORD", "")
        smtp_host = _get_secrets("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(_get_secrets("MAIL_PORT", 587))

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏃 Nieuwe Carboo registratie: {naam}"
        msg["From"]    = afzender
        msg["To"]      = ontvanger

        html_body = f"""
        <html><body style="font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px;">
        <div style="max-width:500px;margin:0 auto;background:#1e293b;border-radius:10px;padding:20px;">
            <div style="font-size:20px;font-weight:900;color:#f97316;margin-bottom:16px;">
                CAR<span style="color:#f1f5f9">BOO</span> — Nieuwe registratie
            </div>
            <p style="color:#94a3b8;margin-bottom:8px;">Er is een nieuw account aangemaakt:</p>
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:8px;color:#64748b;font-size:12px;font-weight:bold;">NAAM</td>
                    <td style="padding:8px;color:#f1f5f9;font-weight:bold;">{naam}</td>
                </tr>
                <tr style="background:rgba(255,255,255,0.03)">
                    <td style="padding:8px;color:#64748b;font-size:12px;font-weight:bold;">E-MAIL</td>
                    <td style="padding:8px;color:#f1f5f9;">{email}</td>
                </tr>
            </table>
            <div style="margin-top:16px;padding:12px;background:#0f172a;border-radius:8px;
                        font-size:13px;color:#94a3b8;">
                Log in op het admin panel om credits toe te voegen aan deze gebruiker.
            </div>
        </div>
        </body></html>
        """

        msg.attach(MIMEText(html_body, "html"))

        if ww_mail:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(afzender, ww_mail)
                server.sendmail(afzender, ontvanger, msg.as_string())
    except Exception as e:
        # Mail fout is niet kritiek — registratie gaat door
        print(f"Mail fout (niet kritiek): {e}")

# ─── Supabase connectie ───────────────────────────────────────────────────────
def _get_secrets(key: str, default: str = "") -> str:
    """Haal secret op via st.secrets of os.environ."""
    import os
    try:
        return st.secrets[key]
    except:
        return os.environ.get(key, default)


def _get_supabase():
    url = _get_secrets("SUPABASE_URL")
    key = _get_secrets("SUPABASE_KEY")
    return create_client(url, key)

def _hash(ww: str) -> str:
    return hashlib.sha256(ww.encode()).hexdigest()

# ─── User ophalen ─────────────────────────────────────────────────────────────
def _get_user(email: str):
    try:
        sb = _get_supabase()
        r  = sb.table("carboo_users").select("*").eq("email", email.lower().strip()).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        st.error(f"Database fout: {e}")
        return None

def _get_user_by_id(user_id: str):
    try:
        sb = _get_supabase()
        r  = sb.table("carboo_users").select("*").eq("id", user_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None

# ─── Credits ──────────────────────────────────────────────────────────────────
def get_credits(user_id: str) -> int:
    """Haal actuele credits op uit Supabase."""
    user = _get_user_by_id(user_id)
    return user["credits"] if user else 0

def gebruik_credit(user_id: str, beschrijving: str = "Rapport gegenereerd") -> bool:
    """Trek 1 credit af. Geeft True terug als gelukt."""
    try:
        sb = _get_supabase()
        user = _get_user_by_id(user_id)
        if not user or user["credits"] <= 0:
            return False
        # Credit aftrekken
        sb.table("carboo_users").update({"credits": user["credits"] - 1}).eq("id", user_id).execute()
        # Transactie loggen
        sb.table("carboo_transacties").insert({
            "user_id":     user_id,
            "type":        "gebruik",
            "credits":     -1,
            "beschrijving": beschrijving,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij credit aftrek: {e}")
        return False

def voeg_credits_toe(user_id: str, aantal: int, beschrijving: str = "Credits toegevoegd") -> bool:
    """Voeg credits toe aan een gebruiker."""
    try:
        sb = _get_supabase()
        user = _get_user_by_id(user_id)
        if not user:
            return False
        sb.table("carboo_users").update({"credits": user["credits"] + aantal}).eq("id", user_id).execute()
        sb.table("carboo_transacties").insert({
            "user_id":     user_id,
            "type":        "aankoop",
            "credits":     aantal,
            "beschrijving": beschrijving,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij credits toevoegen: {e}")
        return False

# ─── Login pagina ─────────────────────────────────────────────────────────────

def sla_coach_data_op(user_id: str, coach_data: dict) -> bool:
    """Sla coach_data op in Supabase zodat het na redirect herstelbaar is."""
    try:
        import json
        sb = _get_supabase()
        sb.table("carboo_users").update({
            "coach_data_json": json.dumps(coach_data)
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Fout bij opslaan coach_data: {e}")
        return False

def herstel_coach_data(user_id: str) -> dict | None:
    """Haal coach_data op uit Supabase."""
    try:
        import json
        sb = _get_supabase()
        r = sb.table("carboo_users").select("coach_data_json").eq("id", user_id).execute()
        if r.data and r.data[0].get("coach_data_json"):
            return json.loads(r.data[0]["coach_data_json"])
        return None
    except Exception as e:
        print(f"Fout bij herstellen coach_data: {e}")
        return None

def wis_coach_data(user_id: str):
    """Wis opgeslagen coach_data na gebruik."""
    try:
        sb = _get_supabase()
        sb.table("carboo_users").update({"coach_data_json": None}).eq("id", user_id).execute()
    except:
        pass


import secrets
from datetime import datetime, timedelta

def stuur_reset_mail(email: str) -> bool:
    """Genereer reset token en stuur mail."""
    try:
        sb    = _get_supabase()
        user  = _get_user(email)
        if not user:
            return False  # geen foutmelding tonen (security)

        token  = secrets.token_urlsafe(32)
        expiry = (datetime.utcnow() + timedelta(hours=2)).isoformat()

        sb.table("carboo_users").update({
            "reset_token":        token,
            "reset_token_expiry": expiry,
        }).eq("id", user["id"]).execute()

        app_url  = _get_secrets("APP_URL", "https://carboo-z9tbmypf2zc56jzqjwc6bo.streamlit.app")
        reset_url = f"{app_url}?reset_token={token}"

        afzender  = _get_secrets("MAIL_FROM", "")
        ww_mail   = _get_secrets("MAIL_PASSWORD", "")
        smtp_host = _get_secrets("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(_get_secrets("MAIL_PORT", 587))

        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Carboo — Wachtwoord opnieuw instellen"
        msg["From"]    = afzender
        msg["To"]      = email

        html_body = f"""
        <html><body style="font-family:Helvetica,Arial,sans-serif;background:#0f172a;color:#f1f5f9;padding:20px;">
        <div style="max-width:500px;margin:0 auto;background:#1e293b;border-radius:10px;padding:24px;">
            <div style="font-size:22px;font-weight:900;color:#f97316;margin-bottom:16px;">
                CAR<span style="color:#f1f5f9">BOO</span>
            </div>
            <p style="color:#94a3b8;">Hallo {user['naam']},</p>
            <p style="color:#f1f5f9;">Je hebt een wachtwoordreset aangevraagd. Klik op onderstaande knop om een nieuw wachtwoord in te stellen.</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{reset_url}" style="background:#f97316;color:white;padding:12px 28px;
                   border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">
                   🔑 Wachtwoord opnieuw instellen
                </a>
            </div>
            <p style="color:#64748b;font-size:0.8rem;">Deze link is 2 uur geldig. Als je geen reset hebt aangevraagd, kan je deze mail negeren.</p>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html"))

        if ww_mail:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(afzender, ww_mail)
                server.sendmail(afzender, email, msg.as_string())
        return True
    except Exception as e:
        print(f"Reset mail fout: {e}")
        return False


def verifieer_reset_token(token: str) -> dict | None:
    """Controleer of token geldig en niet verlopen is."""
    try:
        sb = _get_supabase()
        r  = sb.table("carboo_users").select("*").eq("reset_token", token).execute()
        if not r.data:
            return None
        user   = r.data[0]
        expiry = user.get("reset_token_expiry")
        if not expiry:
            return None
        if datetime.utcnow() > datetime.fromisoformat(expiry.replace("Z", "")):
            return None  # verlopen
        return user
    except:
        return None


def stel_nieuw_wachtwoord_in(token: str, nieuw_ww: str) -> bool:
    """Stel nieuw wachtwoord in en wis reset token."""
    try:
        sb   = _get_supabase()
        user = verifieer_reset_token(token)
        if not user:
            return False
        sb.table("carboo_users").update({
            "wachtwoord":         _hash(nieuw_ww),
            "reset_token":        None,
            "reset_token_expiry": None,
        }).eq("id", user["id"]).execute()
        return True
    except:
        return False


def render_wachtwoord_reset():
    """Toon wachtwoord reset formulier op basis van URL token."""
    token = st.query_params.get("reset_token", "")
    if not token:
        return False

    st.markdown("""
    <div style="max-width:420px;margin:40px auto 0 auto;text-align:center;">
        <div style="font-size:2rem;font-weight:900;letter-spacing:4px;color:#f8fafc;">
            CAR<span style="color:#f97316;">BOO</span>
        </div>
        <div style="font-size:0.8rem;color:#64748b;letter-spacing:2px;margin-top:4px;margin-bottom:24px;">
            WACHTWOORD OPNIEUW INSTELLEN
        </div>
    </div>
    """, unsafe_allow_html=True)

    user = verifieer_reset_token(token)
    if not user:
        st.error("❌ Deze link is ongeldig of verlopen. Vraag een nieuwe reset aan.")
        st.query_params.clear()
        return True

    st.success(f"Hallo {user['naam']}! Stel hieronder je nieuw wachtwoord in.")
    nw1 = st.text_input("Nieuw wachtwoord", type="password", key="reset_ww1")
    nw2 = st.text_input("Herhaal wachtwoord", type="password", key="reset_ww2")

    if st.button("✅ Wachtwoord opslaan", use_container_width=True):
        if len(nw1) < 6:
            st.error("Wachtwoord moet minstens 6 tekens zijn.")
        elif nw1 != nw2:
            st.error("Wachtwoorden komen niet overeen.")
        else:
            if stel_nieuw_wachtwoord_in(token, nw1):
                st.success("✅ Wachtwoord gewijzigd! Je kan nu inloggen.")
                st.query_params.clear()
            else:
                st.error("Fout bij opslaan. Probeer opnieuw.")
    return True


def controleer_promo_code(code: str) -> dict | None:
    """Controleer of een promo code geldig is. Geeft code data terug of None."""
    if not code:
        return None
    try:
        from datetime import date
        sb = _get_supabase()
        r  = sb.table("carboo_codes").select("*").eq("code", code.upper().strip()).execute()
        if not r.data:
            return None
        c = r.data[0]
        if not c.get("actief", False):
            return None
        if c.get("vervaldatum") and date.fromisoformat(c["vervaldatum"]) < date.today():
            return None
        if c.get("gebruik", 0) >= c.get("max_gebruik", 100):
            return None
        return c
    except Exception as e:
        print(f"Code check fout: {e}")
        return None


def gebruik_promo_code(code_id: str, user_id: str, credits: int):
    """Registreer gebruik van promo code en voeg credits toe."""
    try:
        sb = _get_supabase()
        # Gebruik teller ophogen
        huidig = sb.table("carboo_codes").select("gebruik").eq("id", code_id).execute()
        huidig_gebruik = huidig.data[0]["gebruik"] if huidig.data else 0
        sb.table("carboo_codes").update({
            "gebruik": huidig_gebruik + 1
        }).eq("id", code_id).execute()
        # Credits toevoegen aan gebruiker
        voeg_credits_toe(user_id, credits, f"Promo code — {credits} gratis rapport(en)")
        # Promo code opslaan op gebruiker
        code_data = sb.table("carboo_codes").select("code").eq("id", code_id).execute()
        code_str = code_data.data[0]["code"] if code_data.data else ""
        sb.table("carboo_users").update({"promo_code": code_str}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Promo gebruik fout: {e}")


def get_alle_codes() -> list:
    """Haal alle promo codes op voor admin."""
    try:
        sb = _get_supabase()
        return sb.table("carboo_codes").select("*").order("aangemaakt", desc=True).execute().data or []
    except:
        return []


def maak_code_aan(code: str, firma: str, credits: int, max_gebruik: int, vervaldatum: str) -> bool:
    """Maak een nieuwe promo code aan."""
    try:
        sb = _get_supabase()
        sb.table("carboo_codes").insert({
            "code":        code.upper().strip(),
            "firma":       firma,
            "credits":     credits,
            "max_gebruik": max_gebruik,
            "gebruik":     0,
            "actief":      True,
            "vervaldatum": vervaldatum if vervaldatum else None,
        }).execute()
        return True
    except Exception as e:
        print(f"Code aanmaken fout: {e}")
        return False


def toggle_code_actief(code_id: str, actief: bool):
    """Activeer of deactiveer een promo code."""
    try:
        sb = _get_supabase()
        sb.table("carboo_codes").update({"actief": actief}).eq("id", code_id).execute()
    except:
        pass

def render_login_page():
    st.markdown("""
    <div style="max-width:420px;margin:60px auto 0 auto;">
      <div style="text-align:center;margin-bottom:30px;">
        <div style="font-size:2.5rem;font-weight:900;letter-spacing:4px;color:#f8fafc;">
          CAR<span style="color:#f97316;">BOO</span>
        </div>
        <div style="font-size:0.8rem;color:#64748b;letter-spacing:2px;margin-top:4px;">
          RACE NUTRITION COACH
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["  Inloggen  ", "  Registreren  "])

    with tab_login:
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
                    # Ondersteun ook ongehashte wachtwoorden (tijdelijk voor admin)
                    st.error("Verkeerd wachtwoord.")
                else:
                    st.session_state.logged_in    = True
                    st.session_state.current_user = {
                        "id":     user["id"],
                        "name":   user["naam"],
                        "email":  user["email"],
                        "role":   user["rol"],
                        "credits": user["credits"],
                    }
                    st.rerun()

    with tab_register:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:12px;">Maak een account aan. De beheerder voegt credits toe na verificatie.</div>', unsafe_allow_html=True)

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
            elif _get_user(r_email):
                st.error("Dit e-mailadres is al geregistreerd.")
            else:
                try:
                    sb = _get_supabase()
                    # Controleer promo code voor registratie
                    promo_data = None
                    if r_code and r_code.strip():
                        promo_data = controleer_promo_code(r_code.strip())
                        if not promo_data:
                            st.warning("⚠️ Ongeldige of verlopen promotiecode. Registratie gaat door zonder code.")

                    result = sb.table("carboo_users").insert({
                        "email":      r_email.lower().strip(),
                        "naam":       r_naam.strip(),
                        "wachtwoord": _hash(r_ww),
                        "rol":        "user",
                        "credits":    0,
                    }).execute()

                    if result.data:
                        new_user = result.data[0]
                        # Verwerk promo code
                        if promo_data:
                            gebruik_promo_code(promo_data["id"], new_user["id"], promo_data["credits"])
                            st.success(f"🎉 Promotiecode geldig! Je ontvangt {promo_data['credits']} gratis rapport(en).")
                        # Stuur mail naar admin
                        _stuur_registratie_mail(r_naam.strip(), r_email.lower().strip())
                        st.success("✅ Account aangemaakt! Je kan nu inloggen.")
                        st.info("De beheerder wordt op de hoogte gebracht en voegt credits toe.")
                except Exception as e:
                    st.error(f"Fout bij registratie: {e}")


# ─── Admin panel ──────────────────────────────────────────────────────────────
def render_admin_panel():
    st.markdown('<div style="font-size:1.2rem;font-weight:900;color:#f97316;margin-bottom:20px;">⚙️ ADMIN PANEL</div>', unsafe_allow_html=True)

    try:
        sb = _get_supabase()
        users = sb.table("carboo_users").select("*").order("aangemaakt", desc=True).execute().data
    except Exception as e:
        st.error(f"Fout: {e}")
        return

    # ── Statistieken ──────────────────────────────────────────────────────────
    totaal_users   = len([u for u in users if u["rol"] == "user"])
    totaal_credits = sum(u["credits"] for u in users if u["rol"] == "user")
    try:
        alle_trans = sb.table("carboo_transacties").select("*").execute().data
    except:
        alle_trans = []

    trans_gebruik  = [t for t in alle_trans if t["type"] == "gebruik"]
    trans_aankoop  = [t for t in alle_trans if t["type"] == "aankoop"]
    omzet_credits  = sum(abs(t["credits"]) for t in trans_aankoop)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👤 Gebruikers", totaal_users)
    with col2:
        st.metric("📄 Rapporten", len(trans_gebruik))
    with col3:
        st.metric("🎟 Credits resterend", totaal_credits)
    with col4:
        st.metric("💰 Credits verkocht", omzet_credits)

    # ── Recente activiteit ────────────────────────────────────────────────────
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
                unsafe_allow_html=True
            )
    else:
        st.info("Nog geen transacties.")

    st.markdown("---")

    # ── Gebruiker toevoegen ───────────────────────────────────────────────────
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
            if not all([n_naam, n_email, n_ww]):
                st.error("Vul alle velden in.")
            elif _get_user(n_email):
                st.error("E-mail bestaat al.")
            else:
                try:
                    result = sb.table("carboo_users").insert({
                        "email":      n_email.lower().strip(),
                        "naam":       n_naam.strip(),
                        "wachtwoord": _hash(n_ww),
                        "rol":        n_rol,
                        "credits":    n_credits,
                    }).execute()
                    if result.data:
                        sb.table("carboo_transacties").insert({
                            "user_id":     result.data[0]["id"],
                            "type":        "admin",
                            "credits":     n_credits,
                            "beschrijving": "Credits toegevoegd door admin",
                        }).execute()
                        st.success(f"✅ {n_naam} aangemaakt met {n_credits} credits.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Fout: {e}")

    st.markdown("---")

    # ── Gebruikersoverzicht ────────────────────────────────────────────────────
    st.markdown('<div style="font-weight:800;color:#f8fafc;margin-bottom:10px;">GEBRUIKERS</div>', unsafe_allow_html=True)

    for user in users:
        if user["rol"] == "admin":
            continue
        with st.expander(f"👤 {user['naam']}  —  {user['email']}  —  {user['credits']} credits"):
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                st.markdown(f'<div style="font-size:0.8rem;color:#64748b;">Aangemaakt: {str(user["aangemaakt"])[:10]}</div>', unsafe_allow_html=True)
            with col_b:
                extra = st.number_input("Credits toevoegen", 0, 100, 5, key=f"add_c_{user['id']}")
                if st.button("➕ Toevoegen", key=f"add_btn_{user['id']}", use_container_width=True):
                    if voeg_credits_toe(user["id"], extra, "Credits toegevoegd door admin"):
                        st.success(f"✅ {extra} credits toegevoegd.")
                        st.rerun()
            with col_c:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑 Verwijderen", key=f"del_{user['id']}", use_container_width=True):
                    try:
                        sb.table("carboo_transacties").delete().eq("user_id", user["id"]).execute()
                        sb.table("carboo_users").delete().eq("id", user["id"]).execute()
                        st.success("Gebruiker verwijderd.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fout: {e}")

            # Transactie geschiedenis
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
                            unsafe_allow_html=True
                        )
            except:
                pass

    # ── Terug ─────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    # ── PROMO CODES TAB ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div style="font-weight:800;color:#f97316;margin-bottom:12px;font-size:1rem;">🎟 PROMO CODES</div>', unsafe_allow_html=True)

    codes = get_alle_codes()
    if codes:
        # Overzicht tabel
        for c in codes:
            gebruik_pct = round((c.get("gebruik",0) / max(c.get("max_gebruik",1),1)) * 100)
            kleur = "#22c55e" if c.get("actief") else "#ef4444"
            status = "✅ Actief" if c.get("actief") else "❌ Inactief"
            verval = c.get("vervaldatum","—") or "—"
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                        padding:10px 14px;margin-bottom:8px;display:flex;
                        justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <span style="font-family:monospace;font-weight:700;color:#f97316;font-size:1rem;">
                        {c['code']}</span>
                    <span style="color:#64748b;font-size:0.8rem;margin-left:10px;">{c.get('firma','—')}</span>
                </div>
                <div style="display:flex;gap:16px;align-items:center;font-size:0.8rem;">
                    <span style="color:#94a3b8;">🎟 {c.get('credits',1)} credit(s)</span>
                    <span style="color:#94a3b8;">👥 {c.get('gebruik',0)}/{c.get('max_gebruik',100)}</span>
                    <span style="color:#94a3b8;">📅 {verval}</span>
                    <span style="color:{kleur};">{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            ca, cb = st.columns([1,1])
            with ca:
                if c.get("actief"):
                    if st.button(f"⏸ Deactiveer", key=f"deact_{c['id']}", use_container_width=True):
                        toggle_code_actief(c["id"], False)
                        st.rerun()
                else:
                    if st.button(f"▶ Activeer", key=f"act_{c['id']}", use_container_width=True):
                        toggle_code_actief(c["id"], True)
                        st.rerun()
    else:
        st.info("Nog geen promo codes aangemaakt.")

    # Nieuwe code aanmaken
    st.markdown('<div style="font-weight:600;color:#f1f5f9;margin:16px 0 8px;">Nieuwe code aanmaken</div>', unsafe_allow_html=True)
    nc1, nc2 = st.columns(2)
    with nc1:
        n_code    = st.text_input("Code", placeholder="bijv. DECATHLON2026", key="new_code").upper()
        n_firma   = st.text_input("Firma / organisatie", placeholder="bijv. Decathlon", key="new_firma")
        n_credits = st.number_input("Gratis credits", 1, 10, 1, key="new_credits")
    with nc2:
        n_max     = st.number_input("Max. gebruik", 1, 10000, 100, key="new_max")
        n_verval  = st.date_input("Vervaldatum", key="new_verval")
    if st.button("✅ Code aanmaken", key="code_aanmaken", use_container_width=True):
        if not n_code or not n_firma:
            st.error("Vul code en firma in.")
        else:
            ok = maak_code_aan(n_code, n_firma, n_credits, n_max, str(n_verval))
            if ok:
                st.success(f"✅ Code '{n_code}' aangemaakt voor {n_firma}!")
                st.rerun()
            else:
                st.error("Code al in gebruik of fout opgetreden.")

    if st.button("← Terug naar menu", key="admin_terug"):
        st.session_state.module = "menu"
        st.rerun()
