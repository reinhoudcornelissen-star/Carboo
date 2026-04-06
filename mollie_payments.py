import streamlit as st
import requests
import json

# ─── Pakketten ────────────────────────────────────────────────────────────────
PAKKETTEN = [
    {"id": "pack1",  "credits": 1,  "prijs": 4.99,  "label": "1 rapport",    "kleur": "#1e293b"},
    {"id": "pack3",  "credits": 3,  "prijs": 12.00, "label": "3 rapporten",  "kleur": "#1e3a5f"},
    {"id": "pack10", "credits": 10, "prijs": 45.00, "label": "10 rapporten", "kleur": "#1e4a2f"},
]

def _get_mollie_key():
    return st.secrets.get("MOLLIE_API_KEY", "")

def _get_app_url():
    return st.secrets.get("APP_URL", "https://carboo-z9tbmypf2zc56jzqjwc6bo.streamlit.app")

def maak_betaling(pakket_id: str, user_id: str, user_email: str) -> str | None:
    """Maak een Mollie betaling aan en geef de checkout URL terug."""
    pakket = next((p for p in PAKKETTEN if p["id"] == pakket_id), None)
    if not pakket:
        return None

    api_key = _get_mollie_key()
    if not api_key:
        st.error("Mollie API key niet geconfigureerd.")
        return None

    app_url = _get_app_url()

    payload = {
        "amount": {
            "currency": "EUR",
            "value": f"{pakket['prijs']:.2f}"
        },
        "description": f"Carboo — {pakket['label']}",
        "redirectUrl": f"{app_url}?betaling=ok&user_id={user_id}&credits={pakket['credits']}",
        "webhookUrl": f"{app_url}/webhook",  # optioneel
        "metadata": {
            "user_id":  user_id,
            "credits":  pakket["credits"],
            "pakket_id": pakket_id,
        },
        "locale": "nl_BE",
    }

    try:
        resp = requests.post(
            "https://api.mollie.com/v2/payments",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 201:
            return data["_links"]["checkout"]["href"]
        else:
            st.error(f"Mollie fout: {data.get('detail', 'Onbekende fout')}")
            return None
    except Exception as e:
        st.error(f"Verbindingsfout: {e}")
        return None


def controleer_betaling_url():
    """Controleer of gebruiker terugkomt van Mollie betaling via URL params."""
    params = st.query_params
    if params.get("betaling") != "ok":
        return

    user_id = params.get("user_id", "")
    credits = int(params.get("credits", 0))

    if not user_id or credits <= 0:
        st.query_params.clear()
        return

    try:
        from login import voeg_credits_toe, get_credits, _get_user_by_id, herstel_coach_data, wis_coach_data

        # Voorkom dubbele verwerking
        reeds_verwerkt_key = f"betaling_verwerkt_{user_id}_{credits}"
        if st.session_state.get(reeds_verwerkt_key):
            st.query_params.clear()
            return

        # Credits toevoegen
        voeg_credits_toe(user_id, credits, f"Mollie aankoop — {credits} rapport(en)")
        st.session_state[reeds_verwerkt_key] = True

        # Automatisch inloggen als sessie leeg is
        if "current_user" not in st.session_state or not st.session_state.get("logged_in"):
            user = _get_user_by_id(user_id)
            if user:
                st.session_state.logged_in    = True
                st.session_state.current_user = {
                    "id":      user["id"],
                    "name":    user["naam"],
                    "email":   user["email"],
                    "role":    user["rol"],
                    "credits": get_credits(user_id),
                }
                st.session_state.module = "coach"
        else:
            # Sessie actief — update credits
            st.session_state.current_user["credits"] = get_credits(user_id)

        # Herstel coach_data en ga naar stap 5
        coach_data = herstel_coach_data(user_id)
        if coach_data:
            st.session_state["coach_data"] = coach_data
            st.session_state["coach_stap"] = 5
            st.session_state["module"]     = "coach"
            wis_coach_data(user_id)

        # Wis URL params en toon melding
        st.query_params.clear()
        st.success(f"✅ Betaling geslaagd! {credits} credit(s) toegevoegd. Je plan staat klaar.")
        st.rerun()

    except Exception as e:
        st.error(f"Fout bij verwerken betaling: {e}")


def render_credits_kopen(user_id: str, user_email: str):
    """Toon het credits kopen scherm."""
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.1rem;font-weight:800;color:#f8fafc;margin-bottom:6px;">
            Koop credits om je rapport te genereren
        </div>
        <div style="font-size:0.82rem;color:#64748b;">
            Veilig betalen via Mollie — Bancontact, Visa, Mastercard
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, pakket in enumerate(PAKKETTEN):
        with cols[i]:
            prijs_pp = pakket["prijs"] / pakket["credits"]
            korting  = round((4.99 - prijs_pp) * pakket["credits"], 2) if pakket["credits"] > 1 else 0
            korting_html = f'<div style="font-size:0.72rem;color:#22c55e;margin-top:6px;min-height:18px;">✓ €{korting:.2f} korting</div>' if korting > 0 else '<div style="min-height:18px;"></div>'

            st.markdown(f"""
            <div style="background:{pakket['kleur']};border-radius:12px;padding:18px 16px 14px 16px;
                        text-align:center;border:1px solid #334155;margin-bottom:12px;
                        display:flex;flex-direction:column;align-items:center;min-height:160px;">
                <div style="font-size:1.1rem;font-weight:900;color:#f97316;min-height:28px;">
                    {pakket['label']}
                </div>
                <div style="font-size:2.2rem;font-weight:900;color:#f8fafc;margin:8px 0 2px 0;">
                    €{pakket['prijs']:.2f}
                </div>
                <div style="font-size:0.75rem;color:#64748b;min-height:18px;">
                    €{prijs_pp:.2f} / rapport
                </div>
                {korting_html}
            </div>
            """, unsafe_allow_html=True)

            if st.button("Kopen →", key=f"koop_{pakket['id']}", use_container_width=True):
                with st.spinner("Betaalpagina laden..."):
                    # Sla coach_data op in Supabase zodat plan bewaard blijft
                    coach_data = st.session_state.get("coach_data", {})
                    if coach_data and user_id:
                        try:
                            from login import sla_coach_data_op
                            sla_coach_data_op(user_id, coach_data)
                        except:
                            pass
                    url = maak_betaling(pakket["id"], user_id, user_email)
                    if url:
                        st.session_state[f"betaal_url_{pakket['id']}"] = url

            betaal_url = st.session_state.get(f"betaal_url_{pakket['id']}", "")
            if betaal_url:
                st.markdown(
                    f'<div style="text-align:center;margin-top:6px;">' +
                    f'<a href="{betaal_url}" target="_blank" style="' +
                    f'background:#f97316;color:white;padding:8px 16px;border-radius:8px;' +
                    f'font-weight:700;text-decoration:none;display:inline-block;' +
                    f'font-size:0.85rem;width:100%;box-sizing:border-box;">💳 Ga naar betaalpagina →</a></div>',
                    unsafe_allow_html=True
                )

    st.markdown("""
    <div style="text-align:center;margin-top:16px;font-size:0.72rem;color:#475569;">
        🔒 Veilige betaling via Mollie · Geen abonnement · Geen verborgen kosten
    </div>
    """, unsafe_allow_html=True)
