import streamlit as st
import requests

# ─── Credit pakketten (losse rapporten) ──────────────────────────────────────
PAKKETTEN = [
    {"id": "pack1",  "credits": 1,  "prijs": 4.99,  "label": "1 rapport",    "kleur": "#1e293b"},
    {"id": "pack3",  "credits": 3,  "prijs": 12.00, "label": "3 rapporten",  "kleur": "#1e3a5f"},
    {"id": "pack10", "credits": 10, "prijs": 45.00, "label": "10 rapporten", "kleur": "#1e4a2f"},
]

# ─── Abonnement pakketten ─────────────────────────────────────────────────────
ABONNEMENTEN = [
    {"id": "abo_alles",   "pakket": "alles",   "prijs": 9.99,  "label": "Alles-in-1",   "kleur": "#1e293b", "populair": True},
    {"id": "abo_fueling", "pakket": "fueling", "prijs": 5.99,  "label": "Fueling",      "kleur": "#1e293b", "populair": False},
    {"id": "abo_gut",     "pakket": "gut",      "prijs": 3.99,  "label": "Train the Gut","kleur": "#1e293b", "populair": False},
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _get_mollie_key():
    import os
    try: return st.secrets.get("MOLLIE_API_KEY", "") or os.environ.get("MOLLIE_API_KEY", "")
    except: return os.environ.get("MOLLIE_API_KEY", "")

def _get_app_url():
    import os
    try: return st.secrets.get("APP_URL", "") or os.environ.get("APP_URL", "https://carboo.onrender.com")
    except: return os.environ.get("APP_URL", "https://carboo.onrender.com")

def _get_webhook_url():
    import os
    try: return st.secrets.get("WEBHOOK_URL", "") or os.environ.get("WEBHOOK_URL", "https://carboo-webhook.railway.app/webhook")
    except: return os.environ.get("WEBHOOK_URL", "https://carboo-webhook.railway.app/webhook")

# ─── Mollie API ───────────────────────────────────────────────────────────────
def verifieer_mollie_betaling(payment_id: str) -> dict | None:
    api_key = _get_mollie_key()
    if not api_key or not payment_id: return None
    try:
        resp = requests.get(
            f"https://api.mollie.com/v2/payments/{payment_id}",
            headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except: return None

def maak_betaling(pakket_id: str, user_id: str, user_email: str) -> str | None:
    """Maak Mollie betaling voor losse credits."""
    pakket = next((p for p in PAKKETTEN if p["id"] == pakket_id), None)
    if not pakket: return None
    api_key = _get_mollie_key()
    if not api_key: st.error("Mollie API key niet geconfigureerd."); return None
    app_url = _get_app_url()
    payload = {
        "amount":      {"currency": "EUR", "value": f"{pakket['prijs']:.2f}"},
        "description": f"Carboo — {pakket['label']}",
        "redirectUrl": f"{app_url}?betaling=ok&user_id={user_id}&credits={pakket['credits']}",
        "webhookUrl":  _get_webhook_url(),
        "metadata":    {"user_id": user_id, "credits": pakket["credits"], "type": "credits"},
        "locale":      "nl_BE",
    }
    try:
        resp = requests.post(
            "https://api.mollie.com/v2/payments",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload, timeout=10)
        data = resp.json()
        if resp.status_code == 201: return data["_links"]["checkout"]["href"]
        st.error(f"Mollie fout: {data.get('detail', 'Onbekende fout')}"); return None
    except Exception as e:
        st.error(f"Verbindingsfout: {e}"); return None

def maak_abonnement_betaling(abo_id: str, user_id: str, user_email: str) -> str | None:
    """Maak Mollie betaling voor een abonnement (éénmalig, manueel verlengen)."""
    abo = next((a for a in ABONNEMENTEN if a["id"] == abo_id), None)
    if not abo: return None
    api_key = _get_mollie_key()
    if not api_key: st.error("Mollie API key niet geconfigureerd."); return None
    app_url = _get_app_url()
    payload = {
        "amount":      {"currency": "EUR", "value": f"{abo['prijs']:.2f}"},
        "description": f"Carboo — {abo['label']} (1 maand)",
        "redirectUrl": f"{app_url}?betaling=abo&user_id={user_id}&pakket={abo['pakket']}",
        "webhookUrl":  _get_webhook_url(),
        "metadata":    {"user_id": user_id, "pakket": abo["pakket"], "type": "abonnement"},
        "locale":      "nl_BE",
    }
    try:
        resp = requests.post(
            "https://api.mollie.com/v2/payments",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload, timeout=10)
        data = resp.json()
        if resp.status_code == 201: return data["_links"]["checkout"]["href"]
        st.error(f"Mollie fout: {data.get('detail', 'Onbekende fout')}"); return None
    except Exception as e:
        st.error(f"Verbindingsfout: {e}"); return None

# ─── Webhook verwerking ───────────────────────────────────────────────────────
def verwerk_mollie_webhook(payment_id: str) -> bool:
    betaling = verifieer_mollie_betaling(payment_id)
    if not betaling or betaling.get("status") != "paid": return False
    metadata = betaling.get("metadata", {})
    user_id  = metadata.get("user_id", "")
    betaling_type = metadata.get("type", "credits")
    if not user_id: return False
    try:
        if betaling_type == "abonnement":
            from login import activeer_abonnement
            pakket = metadata.get("pakket", "alles")
            activeer_abonnement(user_id, pakket)
        else:
            from login import voeg_credits_toe
            credits = int(metadata.get("credits", 0))
            if credits > 0:
                voeg_credits_toe(user_id, credits, f"Mollie webhook — {credits} rapport(en)")
        return True
    except: return False

# ─── URL check na betaling ────────────────────────────────────────────────────
def controleer_betaling_url():
    """Controleer of gebruiker terugkomt van Mollie betaling via URL params."""
    params = st.query_params
    betaling_type = params.get("betaling", "")
    if betaling_type not in ("ok", "abo"): return

    user_id = params.get("user_id", "")
    if not user_id: st.query_params.clear(); return

    reeds_key = f"betaling_verwerkt_{user_id}_{betaling_type}"
    if st.session_state.get(reeds_key): st.query_params.clear(); return

    try:
        from login import voeg_credits_toe, get_credits, _get_user_by_id, activeer_abonnement, herstel_coach_data, wis_coach_data

        if betaling_type == "abo":
            # Abonnement activeren
            pakket = params.get("pakket", "alles")
            activeer_abonnement(user_id, pakket)
            st.session_state[reeds_key] = True
            # Herstel sessie
            if not st.session_state.get("logged_in"):
                user = _get_user_by_id(user_id)
                if user:
                    st.session_state.logged_in    = True
                    st.session_state.current_user = {
                        "id": user["id"], "name": user["naam"],
                        "email": user["email"], "role": user["rol"],
                        "credits": get_credits(user_id),
                    }
            st.session_state.module = "menu"
            st.query_params.clear()
            abo_labels = {"alles": "Alles-in-1", "fueling": "Fueling", "gut": "Train the Gut"}
            st.success(f"✅ Abonnement '{abo_labels.get(pakket, pakket)}' geactiveerd! Veel trainingsplezier.")
            st.rerun()

        else:
            # Credits toevoegen
            credits = int(params.get("credits", 0))
            if credits <= 0: st.query_params.clear(); return
            voeg_credits_toe(user_id, credits, f"Mollie aankoop — {credits} rapport(en)")
            st.session_state[reeds_key] = True
            if not st.session_state.get("logged_in"):
                user = _get_user_by_id(user_id)
                if user:
                    st.session_state.logged_in    = True
                    st.session_state.current_user = {
                        "id": user["id"], "name": user["naam"],
                        "email": user["email"], "role": user["rol"],
                        "credits": get_credits(user_id),
                    }
                    st.session_state.module = "coach"
            else:
                st.session_state.current_user["credits"] = get_credits(user_id)

            # Herstel rapport
            coach_data = herstel_coach_data(user_id)
            if coach_data:
                st.session_state["coach_data"] = coach_data
                try:
                    pending_html = st.session_state.pop("rapport_html_pending", "")
                    if pending_html:
                        html_str = pending_html
                    else:
                        from carboo_coach import _genereer_html
                        html_str = _genereer_html(coach_data, st.session_state.get("current_user",{}).get("name","Atleet"))
                    st.session_state["rapport_html"] = html_str
                    st.session_state.pop("rapport_pdf", None)
                    st.session_state.pop("rapport_credit_afgetrokken", None)
                    st.session_state["module"] = "rapport"
                except:
                    st.session_state["module"] = "coach"
                wis_coach_data(user_id)

            st.query_params.clear()
            st.success(f"✅ Betaling geslaagd! {credits} credit(s) toegevoegd.")
            st.rerun()

    except Exception as e:
        st.error(f"Fout bij verwerken betaling: {e}")

# ─── Credits kopen UI ─────────────────────────────────────────────────────────
def render_credits_kopen(user_id: str, user_email: str):
    """Toon het volledige betaalscherm: abonnementen + losse credits."""

    # Check of we hier komen vanuit abonnement keuze
    abo_keuze = st.session_state.pop("_abo_keuze", None)

    st.markdown("""
    <div style="text-align:center;margin-bottom:28px;">
      <div style="font-size:1.2rem;font-weight:800;color:#f8fafc;margin-bottom:6px;">Kies je pakket</div>
      <div style="font-size:0.82rem;color:#64748b;">Veilig betalen via Mollie — Bancontact · Visa · Mastercard</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Abonnementen ──────────────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;font-weight:700;margin-bottom:10px;">MAANDABONNEMENT</div>', unsafe_allow_html=True)
    abo_cols = st.columns(3)
    abo_info = {
        "alles":   ["⚡ Fueling", "🧪 Train the Gut", "🏁 1 wedstrijdrapport/maand"],
        "fueling": ["⚡ Dagschema op maat", "📊 Voedingsanalyses", "🍽️ Voedselbibliotheek"],
        "gut":     ["🧪 Darmprotocol", "📈 Intensiteitstests", "🏆 Wedstrijdstrategie"],
    }
    for i, abo in enumerate(ABONNEMENTEN):
        with abo_cols[i]:
            rand_kleur = "#f97316" if abo["populair"] else "#334155"
            populair_badge = '<div style="font-size:0.6rem;color:#f97316;font-weight:700;letter-spacing:2px;margin-bottom:6px;">POPULAIRSTE</div>' if abo["populair"] else '<div style="min-height:18px;"></div>'
            features = "".join([f'<div style="font-size:0.72rem;color:#94a3b8;">{f}</div>' for f in abo_info[abo["pakket"]]])
            st.markdown(f"""
            <div style="background:#1e293b;border:2px solid {rand_kleur};border-radius:12px;padding:18px;
                        text-align:center;min-height:220px;box-sizing:border-box;">
              {populair_badge}
              <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">{abo['label']}</div>
              <div style="font-size:2rem;font-weight:900;color:#f97316;margin:6px 0;">€{abo['prijs']:.2f}</div>
              <div style="font-size:0.65rem;color:#64748b;margin-bottom:12px;">/maand</div>
              <div style="line-height:1.9;">{features}</div>
            </div>
            """, unsafe_allow_html=True)

            btn_label = f"{'✓ ' if abo_keuze == abo['pakket'] else ''}Kies {abo['label']}"
            if st.button(btn_label, key=f"abo_koop_{abo['id']}", use_container_width=True,
                         type="primary" if abo["populair"] else "secondary"):
                with st.spinner("Betaalpagina laden..."):
                    url = maak_abonnement_betaling(abo["id"], user_id, user_email)
                    if url: st.session_state[f"abo_url_{abo['id']}"] = url

            betaal_url = st.session_state.get(f"abo_url_{abo['id']}", "")
            if betaal_url:
                st.markdown(
                    f'<div style="text-align:center;margin-top:6px;">'
                    f'<a href="{betaal_url}" target="_blank" style="background:#f97316;color:white;'
                    f'padding:8px 16px;border-radius:8px;font-weight:700;text-decoration:none;'
                    f'display:inline-block;font-size:0.85rem;width:100%;box-sizing:border-box;">'
                    f'💳 Ga naar betaalpagina →</a></div>',
                    unsafe_allow_html=True)

    # ── Losse credits ─────────────────────────────────────────────────────────
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;font-weight:700;margin-bottom:10px;">LOSSE WEDSTRIJDRAPPORTEN</div>', unsafe_allow_html=True)
    credit_cols = st.columns(3)
    for i, pakket in enumerate(PAKKETTEN):
        with credit_cols[i]:
            prijs_pp = pakket["prijs"] / pakket["credits"]
            korting  = round((4.99 - prijs_pp) * pakket["credits"], 2) if pakket["credits"] > 1 else 0
            korting_html = f'<div style="font-size:0.72rem;color:#22c55e;">✓ €{korting:.2f} korting</div>' if korting > 0 else '<div style="min-height:18px;"></div>'
            st.markdown(f"""
            <div style="background:{pakket['kleur']};border-radius:12px;padding:16px;
                        text-align:center;border:1px solid #334155;min-height:140px;box-sizing:border-box;">
              <div style="font-size:1rem;font-weight:900;color:#f97316;">{pakket['label']}</div>
              <div style="font-size:1.8rem;font-weight:900;color:#f8fafc;margin:6px 0;">€{pakket['prijs']:.2f}</div>
              <div style="font-size:0.72rem;color:#64748b;">€{prijs_pp:.2f} / rapport</div>
              {korting_html}
            </div>
            """, unsafe_allow_html=True)
            if st.button("Kopen →", key=f"koop_{pakket['id']}", use_container_width=True):
                with st.spinner("Betaalpagina laden..."):
                    coach_data = st.session_state.get("coach_data", {})
                    if coach_data and user_id:
                        try:
                            from login import sla_coach_data_op
                            sla_coach_data_op(user_id, coach_data)
                        except: pass
                    url = maak_betaling(pakket["id"], user_id, user_email)
                    if url: st.session_state[f"betaal_url_{pakket['id']}"] = url

            betaal_url = st.session_state.get(f"betaal_url_{pakket['id']}", "")
            if betaal_url:
                st.markdown(
                    f'<div style="text-align:center;margin-top:6px;">'
                    f'<a href="{betaal_url}" target="_blank" style="background:#f97316;color:white;'
                    f'padding:8px 16px;border-radius:8px;font-weight:700;text-decoration:none;'
                    f'display:inline-block;font-size:0.85rem;width:100%;box-sizing:border-box;">'
                    f'💳 Ga naar betaalpagina →</a></div>',
                    unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-top:20px;font-size:0.72rem;color:#475569;">
        🔒 Veilige betaling via Mollie · Geen verborgen kosten · Annuleer maandelijks
    </div>
    """, unsafe_allow_html=True)
