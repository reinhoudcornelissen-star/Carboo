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
    """Mooie landing/login pagina in Streamlit."""
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
    elif actie == "disclaimer":
        st.query_params.clear()
        render_disclaimer()
        return

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Instrument+Sans:wght@400;500;600&display=swap');
    #MainMenu,header,footer,.stDeployButton{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    .stApp{background:#0c0c0c!important}
    </style>

    <!-- NAV -->
    <div style="position:sticky;top:0;z-index:100;width:100%;padding:18px 6vw;
                display:flex;align-items:center;justify-content:space-between;
                background:rgba(12,12,12,0.92);backdrop-filter:blur(16px);
                border-bottom:1px solid rgba(255,255,255,0.06);">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#f5f3ef;letter-spacing:2px;line-height:1;">
          Car<span style="color:#f97316;">b</span>oo
        </div>
        <div style="font-size:0.75rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;
                    color:#888;border:1px solid #2a2a2a;padding:5px 12px;border-radius:100px;">
          Sports Nutrition Coach
        </div>
      </div>
      <div style="display:flex;gap:10px;">
        <a href="?actie=login" style="font-size:0.82rem;color:#888;text-decoration:none;padding:8px 16px;">Inloggen</a>
        <a href="?actie=register" style="font-size:0.82rem;font-weight:600;color:#0c0c0c;
           background:#f97316;padding:9px 20px;border-radius:8px;text-decoration:none;">Gratis starten →</a>
      </div>
    </div>

    <!-- HERO -->
    <div style="min-height:100vh;padding:120px 6vw 80px;max-width:1300px;margin:0 auto;
                display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center;">
      <div>
        <div style="font-size:0.7rem;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;
                    color:#f97316;margin-bottom:28px;display:flex;align-items:center;gap:8px;">
          <span style="display:inline-block;width:24px;height:1px;background:#f97316;"></span>
          Voeding × Prestatie
        </div>
        <h1 style="font-family:'Bebas Neue',sans-serif;font-size:clamp(3.5rem,6vw,6rem);
                   line-height:0.95;letter-spacing:2px;color:#f5f3ef;margin-bottom:28px;">
          EET ZOALS<br>JE TRAINT.<br><span style="color:#f97316;">MET EEN PLAN.</span>
        </h1>
        <p style="font-size:1.05rem;color:#888;line-height:1.75;max-width:420px;margin-bottom:44px;">
          Periodiseer je voeding op basis van je trainingsbelasting. Stop met gissen. Begin met fuelen.
        </p>
        <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:32px;">
          <a href="?actie=register" style="font-family:'Bebas Neue',sans-serif;font-size:1rem;
             color:#0c0c0c;background:#f97316;padding:14px 28px;border-radius:10px;
             text-decoration:none;letter-spacing:1px;">GRATIS STARTEN →</a>
          <a href="?actie=login" style="font-size:0.9rem;color:#666;text-decoration:none;padding:14px 0;
             border-bottom:1px solid transparent;">Al een account? Inloggen ↗</a>
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
          <span style="font-size:0.78rem;color:#444;display:flex;align-items:center;gap:6px;">
            <span style="color:#f97316;font-weight:700;">✓</span> 7 dagen gratis</span>
          <span style="font-size:0.78rem;color:#444;display:flex;align-items:center;gap:6px;">
            <span style="color:#f97316;font-weight:700;">✓</span> Geen creditcard</span>
          <span style="font-size:0.78rem;color:#444;display:flex;align-items:center;gap:6px;">
            <span style="color:#f97316;font-weight:700;">✓</span> €9,99/maand</span>
        </div>
      </div>

      <!-- APP MOCKUP -->
      <div style="background:#111;border-radius:16px;overflow:hidden;
                  box-shadow:0 40px 100px rgba(0,0,0,0.6),0 0 0 1px rgba(255,255,255,0.06);
                  transform:perspective(1000px) rotateY(-3deg) rotateX(2deg);">
        <div style="background:#1a1a1a;padding:12px 16px;display:flex;align-items:center;gap:8px;
                    border-bottom:1px solid rgba(255,255,255,0.06);">
          <div style="width:10px;height:10px;border-radius:50%;background:#ff5f57;"></div>
          <div style="width:10px;height:10px;border-radius:50%;background:#febc2e;"></div>
          <div style="width:10px;height:10px;border-radius:50%;background:#28c840;"></div>
          <div style="flex:1;background:#222;border-radius:6px;padding:4px 12px;
                      font-size:0.65rem;color:#555;text-align:center;">carboo.app/dagschema</div>
        </div>
        <div style="padding:20px;">
          <div style="font-size:.6rem;font-weight:700;color:#f97316;letter-spacing:2px;margin-bottom:10px;">DAGSCHEMA — WOENSDAG</div>
          <div style="font-size:1rem;font-weight:700;color:#f5f3ef;margin-bottom:16px;">Zware trainingsdag ⚡</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px;">
            <div style="background:#1e293b;border-radius:8px;padding:10px;">
              <div style="font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Kcal</div>
              <div style="font-size:1rem;font-weight:800;color:#f97316;line-height:1;">2840</div>
              <div style="height:3px;border-radius:2px;margin-top:6px;background:#f97316;width:82%;"></div>
            </div>
            <div style="background:#1e293b;border-radius:8px;padding:10px;">
              <div style="font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">KH</div>
              <div style="font-size:1rem;font-weight:800;color:#22c55e;line-height:1;">348g</div>
              <div style="height:3px;border-radius:2px;margin-top:6px;background:#22c55e;width:88%;"></div>
            </div>
            <div style="background:#1e293b;border-radius:8px;padding:10px;">
              <div style="font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Eiwit</div>
              <div style="font-size:1rem;font-weight:800;color:#3b82f6;line-height:1;">162g</div>
              <div style="height:3px;border-radius:2px;margin-top:6px;background:#3b82f6;width:91%;"></div>
            </div>
          </div>
          <div style="font-size:.62rem;color:#64748b;margin-bottom:8px;">Energietiming vs trainingsbelasting</div>
          <div style="display:flex;align-items:flex-end;gap:4px;height:50px;margin-bottom:14px;">
            <div style="flex:1;height:25%;border-radius:3px 3px 0 0;background:#1e293b;"></div>
            <div style="flex:1;height:20%;border-radius:3px 3px 0 0;background:#1e293b;"></div>
            <div style="flex:1;height:90%;border-radius:3px 3px 0 0;background:#f97316;"></div>
            <div style="flex:1;height:50%;border-radius:3px 3px 0 0;background:#1e293b;"></div>
            <div style="flex:1;height:72%;border-radius:3px 3px 0 0;background:#f97316;"></div>
            <div style="flex:1;height:30%;border-radius:3px 3px 0 0;background:#1e293b;"></div>
            <div style="flex:1;height:20%;border-radius:3px 3px 0 0;background:#1e293b;"></div>
          </div>
          <div style="display:flex;flex-direction:column;gap:5px;">
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:.62rem;color:#94a3b8;background:#1e293b;border-radius:6px;padding:6px 10px;">
              🥗 Ontbijt op target <span style="color:#f97316;font-weight:700;">✓</span></div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:.62rem;color:#94a3b8;background:#1e293b;border-radius:6px;padding:6px 10px;">
              ⚡ Extra KH na training <span style="color:#f97316;font-weight:700;">+40g</span></div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:.62rem;color:#94a3b8;background:#1e293b;border-radius:6px;padding:6px 10px;">
              💪 Eiwit vandaag <span style="color:#f97316;font-weight:700;">162g</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3 PIJLERS -->
    <div style="padding:80px 6vw;background:#141414;border-top:1px solid #2a2a2a;">
      <div style="max-width:1300px;margin:0 auto;">
        <div style="font-size:0.68rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                    color:#f97316;margin-bottom:20px;display:flex;align-items:center;gap:10px;">
          De app <span style="flex:1;height:1px;background:#2a2a2a;display:inline-block;"></span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:2px;
                    border:1px solid #2a2a2a;border-radius:16px;overflow:hidden;margin-top:32px;">
          <div style="background:#1a1a1a;padding:44px 36px;position:relative;display:flex;flex-direction:column;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:5rem;color:rgba(249,115,22,0.07);
                        position:absolute;top:16px;right:24px;line-height:1;">01</div>
            <div style="font-size:2rem;margin-bottom:20px;">⚡</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#f5f3ef;
                        margin-bottom:14px;letter-spacing:1px;">FUELING</div>
            <p style="font-size:0.88rem;color:#888;line-height:1.75;margin-bottom:20px;">
              Dagschema op maat. Per training, per maaltijdmoment. 100+ NEVO-producten,
              AI-etiketscan, community recepten en een eigen prestatie-algoritme.</p>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:auto;">
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Dagschema</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Micronutriënten</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Prestatie-algoritme</span>
            </div>
          </div>
          <div style="background:#1a1a1a;padding:44px 36px;position:relative;border-left:2px solid #2a2a2a;display:flex;flex-direction:column;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:5rem;color:rgba(249,115,22,0.07);
                        position:absolute;top:16px;right:24px;line-height:1;">02</div>
            <div style="font-size:2rem;margin-bottom:20px;">🏁</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#f5f3ef;
                        margin-bottom:14px;letter-spacing:1px;">RACE NUTRITION PLAN</div>
            <p style="font-size:0.88rem;color:#888;line-height:1.75;margin-bottom:20px;">
              Stap-voor-stap voedingsstrategie voor je wedstrijddag. Van sprint tot Ironman.
              Gels, bars, dranken en vast voedsel per checkpoint.</p>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:auto;">
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Carboloading</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Pre-racemeal</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Raceplan</span>
            </div>
          </div>
          <div style="background:#1a1a1a;padding:44px 36px;position:relative;border-left:2px solid #2a2a2a;display:flex;flex-direction:column;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:5rem;color:rgba(249,115,22,0.07);
                        position:absolute;top:16px;right:24px;line-height:1;">03</div>
            <div style="font-size:2rem;margin-bottom:20px;">🫀</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#f5f3ef;
                        margin-bottom:14px;letter-spacing:1px;">TRAIN THE GUT</div>
            <p style="font-size:0.88rem;color:#888;line-height:1.75;margin-bottom:20px;">
              Je darmen trainen voor maximale koolhydraatopname. Trapsgewijs protocol,
              wekelijkse tests, perfecte wedstrijdstrategie.</p>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:auto;">
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Darmprotocol</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Intensiteitstests</span>
              <span style="font-size:0.68rem;font-weight:600;color:#f97316;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);padding:3px 10px;border-radius:100px;">Wedstrijdstrategie</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div style="background:#f97316;padding:100px 6vw;text-align:center;">
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:clamp(2.5rem,5vw,4.5rem);
                 color:#0c0c0c;margin-bottom:20px;letter-spacing:2px;line-height:1;">
        KLAAR OM TE FUELEN<br>ZOALS EEN PROF?</h2>
      <p style="font-size:1rem;color:rgba(12,12,12,0.6);margin-bottom:40px;max-width:400px;
                margin-left:auto;margin-right:auto;line-height:1.7;">
        Maak een gratis account aan en ontdek wat Carboo voor jouw prestaties kan doen.</p>
      <a href="?actie=register" style="font-family:'Bebas Neue',sans-serif;font-size:1rem;
         font-weight:700;color:#f97316;background:#0c0c0c;padding:16px 36px;border-radius:10px;
         text-decoration:none;display:inline-block;letter-spacing:1px;">GRATIS STARTEN →</a>
    </div>

    <!-- FOOTER -->
    <div style="background:#0c0c0c;border-top:1px solid #2a2a2a;padding:28px 6vw;
                display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#f5f3ef;letter-spacing:1px;">
        Car<span style="color:#f97316;">b</span>oo</div>
      <div style="font-size:.75rem;color:#444;">
        Sports Nutrition Coach · Eet zoals je traint. Met een plan. · © 2026</div>
    </div>
    """, unsafe_allow_html=True)



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
        st.markdown(
            '<div style="font-size:0.8rem;color:#64748b;margin:8px 0;">'
            '<a href="?actie=disclaimer" target="_blank" style="color:#f97316;">Lees onze gebruiksvoorwaarden & disclaimer</a>'
            '</div>', unsafe_allow_html=True)
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
