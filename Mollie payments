import streamlit as st
import requests
import json

# ─── Pakketten ────────────────────────────────────────────────────────────────
PAKKETTEN = [
    {"id": "pack1", "credits": 1, "prijs": 4.99,  "label": "1 rapport",   "kleur": "#1e293b"},
    {"id": "pack3", "credits": 3, "prijs": 12.00, "label": "3 rapporten", "kleur": "#1e3a5f"},
    {"id": "pack5", "credits": 5, "prijs": 15.00, "label": "5 rapporten", "kleur": "#1e4a2f"},
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
    if params.get("betaling") == "ok":
        user_id = params.get("user_id", "")
        credits = int(params.get("credits", 0))
        if user_id and credits > 0:
            # Voeg credits toe via login module
            try:
                from login import voeg_credits_toe, get_credits
                voeg_credits_toe(user_id, credits, f"Mollie aankoop — {credits} rapport(en)")
                # Update session state
                if "current_user" in st.session_state:
                    st.session_state.current_user["credits"] = get_credits(user_id)
                # Wis URL params
                st.query_params.clear()
                st.success(f"✅ Betaling ontvangen! {credits} credit(s) toegevoegd.")
                st.rerun()
            except Exception as e:
                st.error(f"Fout bij credits toevoegen: {e}")


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
            # Bereken prijs per rapport
            prijs_pp = pakket["prijs"] / pakket["credits"]
            korting  = round((4.99 - prijs_pp) * pakket["credits"], 2) if pakket["credits"] > 1 else 0

            st.markdown(f"""
            <div style="background:{pakket['kleur']};border-radius:12px;padding:16px;
                        text-align:center;border:1px solid #334155;margin-bottom:8px;">
                <div style="font-size:1.4rem;font-weight:900;color:#f97316;">
                    {pakket['label']}
                </div>
                <div style="font-size:2rem;font-weight:900;color:#f8fafc;margin:8px 0;">
                    €{pakket['prijs']:.2f}
                </div>
                <div style="font-size:0.75rem;color:#64748b;">
                    €{prijs_pp:.2f} / rapport
                </div>
                {f'<div style="font-size:0.72rem;color:#22c55e;margin-top:4px;">✓ €{korting:.2f} korting</div>' if korting > 0 else ''}
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Kopen →", key=f"koop_{pakket['id']}", use_container_width=True):
                with st.spinner("Betaalpagina laden..."):
                    url = maak_betaling(pakket["id"], user_id, user_email)
                    if url:
                        # Open in nieuw tabblad via JavaScript
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0; url={url}">',
                            unsafe_allow_html=True
                        )
                        st.info(f"Je wordt doorgestuurd naar de betaalpagina...")
                        st.markdown(f"[Klik hier als je niet automatisch doorgestuurd wordt]({url})")

    st.markdown("""
    <div style="text-align:center;margin-top:16px;font-size:0.72rem;color:#475569;">
        🔒 Veilige betaling via Mollie · Geen abonnement · Geen verborgen kosten
    </div>
    """, unsafe_allow_html=True)
