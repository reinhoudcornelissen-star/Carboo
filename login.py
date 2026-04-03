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
        afzender  = st.secrets.get("MAIL_FROM", "noreply@carboo.app")
        ww_mail   = st.secrets.get("MAIL_PASSWORD", "")
        smtp_host = st.secrets.get("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("MAIL_PORT", 587))

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
def _get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
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

        if st.button("Inloggen →", key="login_btn", use_container_width=True):
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
                    result = sb.table("carboo_users").insert({
                        "email":      r_email.lower().strip(),
                        "naam":       r_naam.strip(),
                        "wachtwoord": _hash(r_ww),
                        "rol":        "user",
                        "credits":    0,
                    }).execute()

                    if result.data:
                        new_user = result.data[0]
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gebruikers", totaal_users)
    with col2:
        st.metric("Totaal credits", totaal_credits)
    with col3:
        try:
            trans = sb.table("carboo_transacties").select("*").eq("type", "gebruik").execute().data
            st.metric("Rapporten gegenereerd", len(trans))
        except:
            st.metric("Rapporten", "—")

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
    if st.button("← Terug naar menu", key="admin_terug"):
        st.session_state.module = "menu"
        st.rerun()
