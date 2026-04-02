import streamlit as st
import requests
import json

# ── Carboo chatbot via Gemini API ─────────────────────────────────────────────

SYSTEM_PROMPT = """Je bent Carboo Coach, een sportvoedingsassistent gespecialiseerd in race nutrition voor duursporters (fietsen, lopen, triatlon, duatlon).

Je helpt atleten met:
- Koolhydraatbeheer en carboloading
- Voeding tijdens wedstrijden (gels, sportdrank, vast voedsel)
- Timing van maaltijden voor de race
- Vochtbeheer en elektrolyten
- Specifieke vragen over producten (Maurten, SIS, Precision Hydration, ...)

Je antwoorden zijn:
- Praktisch en concreet (geen vage algemeenheden)
- Gebaseerd op sportwetenschap
- In het Nederlands
- Kort en bondig (max 3-4 zinnen tenzij gevraagd)
- Vriendelijk maar professioneel

Als iemand vraagt buiten het domein van sportvoeding, verwijs je beleefd terug naar je specialiteit."""

def _gemini_call(messages: list) -> str:
    """Roep Gemini API aan met conversatiegeschiedenis."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            return "❌ Gemini API sleutel niet gevonden in Streamlit secrets. Voeg GEMINI_API_KEY toe."

        # Bouw Gemini contents op (systeem als eerste user message)
        contents = []
        
        # Voeg systeemprompt toe als eerste bericht
        contents.append({
            "role": "user",
            "parts": [{"text": f"[SYSTEEM INSTRUCTIE - volg dit altijd op]\n{SYSTEM_PROMPT}"}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Begrepen! Ik ben Carboo Coach en help je met alle vragen over race nutrition. Stel gerust je vraag."}]
        })
        
        # Voeg gespreksgeschiedenis toe
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500,
            }
        }
        
        resp = requests.post(url, json=payload, timeout=15)
        
        if resp.status_code != 200:
            return f"❌ API fout {resp.status_code}: {resp.text[:200]}"
        
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    
    except requests.exceptions.Timeout:
        return "⏱️ Timeout — probeer opnieuw."
    except Exception as e:
        return f"❌ Fout: {str(e)[:100]}"


def render_chatbot():
    """Render de Carboo chatbot — roep aan vanuit app.py of wizard."""
    
    # Session state initialiseren
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # ── Drijvende knop (rechtsboven) ──────────────────────────────────────────
    st.markdown("""
    <style>
    .chat-fab {
        position: fixed;
        bottom: 28px;
        right: 28px;
        width: 52px;
        height: 52px;
        background: #f97316;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(249,115,22,0.5);
        z-index: 9999;
        border: none;
        color: white;
        transition: transform .2s;
    }
    .chat-fab:hover { transform: scale(1.08); }
    .chat-window {
        position: fixed;
        bottom: 90px;
        right: 24px;
        width: 340px;
        max-height: 500px;
        background: #1e293b;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        z-index: 9998;
        display: flex;
        flex-direction: column;
        border: 1px solid #334155;
    }
    .chat-header {
        background: #0f172a;
        border-radius: 14px 14px 0 0;
        padding: 12px 16px;
        font-weight: 800;
        font-size: 13px;
        color: #f97316;
        display: flex;
        justify-content: space-between;
        align-items: center;
        letter-spacing: 1px;
    }
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 340px;
    }
    .msg-user {
        background: #f97316;
        color: white;
        border-radius: 10px 10px 2px 10px;
        padding: 7px 11px;
        font-size: 12px;
        align-self: flex-end;
        max-width: 85%;
        line-height: 1.4;
    }
    .msg-bot {
        background: #0f172a;
        color: #cbd5e1;
        border-radius: 10px 10px 10px 2px;
        padding: 7px 11px;
        font-size: 12px;
        align-self: flex-start;
        max-width: 90%;
        line-height: 1.4;
        border: 1px solid #334155;
    }
    .msg-bot b { color: #f97316; }
    </style>
    """, unsafe_allow_html=True)

    # ── Toggle knop ───────────────────────────────────────────────────────────
    col_space, col_btn = st.columns([10, 1])
    with col_btn:
        lbl = "✕" if st.session_state.chat_open else "💬"
        if st.button(lbl, key="chat_fab_btn", help="Carboo Coach — sportvoeding assistent"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    # ── Chatvenster ───────────────────────────────────────────────────────────
    if st.session_state.chat_open:
        
        # Header
        st.markdown("""
        <div style='background:#0f172a;border-radius:10px 10px 0 0;padding:10px 14px;
                    border:1px solid #334155;border-bottom:none;margin-top:8px'>
          <span style='font-weight:800;color:#f97316;font-size:13px;letter-spacing:1px'>
            💬 CARBOO COACH
          </span>
          <span style='color:#64748b;font-size:10px;margin-left:8px'>Race nutrition assistent</span>
        </div>
        """, unsafe_allow_html=True)

        # Berichten tonen
        msgs_html = ""
        if not st.session_state.chat_messages:
            msgs_html = '<div class="msg-bot">👋 Hallo! Ik ben Carboo Coach. Vraag me alles over race nutrition, carboloading, gels, timing, ...</div>'
        else:
            for msg in st.session_state.chat_messages:
                cls = "msg-user" if msg["role"] == "user" else "msg-bot"
                tekst = msg["content"].replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
                msgs_html += f'<div class="{cls}">{tekst}</div>'

        st.markdown(f"""
        <div style='background:#1e293b;border:1px solid #334155;border-top:none;border-bottom:none;
                    padding:10px 12px;max-height:300px;overflow-y:auto;display:flex;
                    flex-direction:column;gap:6px'>
          {msgs_html}
        </div>
        """, unsafe_allow_html=True)

        # Input
        st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-top:none;border-radius:0 0 10px 10px;padding:8px 12px">', unsafe_allow_html=True)
        
        with st.form(key="chat_form", clear_on_submit=True):
            col_input, col_send = st.columns([5, 1])
            with col_input:
                vraag = st.text_input(
                    "", 
                    placeholder="Stel je vraag...",
                    label_visibility="collapsed",
                    key="chat_input"
                )
            with col_send:
                verzend = st.form_submit_button("➤", use_container_width=True)
            
            if verzend and vraag.strip():
                # Voeg gebruikersbericht toe
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": vraag.strip()
                })
                
                # Roep Gemini aan
                with st.spinner("..."):
                    antwoord = _gemini_call(st.session_state.chat_messages)
                
                # Voeg antwoord toe
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": antwoord
                })
                
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Reset knop
        if st.session_state.chat_messages:
            if st.button("🗑 Gesprek wissen", key="chat_reset", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()


def render_chatbot_inline(context: str = ""):
    """
    Compacte inline chatbot voor in de wizard.
    context: extra context meegeven (bv. huidige stap, sport, duur)
    """
    if "wizard_chat_msgs" not in st.session_state:
        st.session_state.wizard_chat_msgs = []
    if "wizard_chat_open" not in st.session_state:
        st.session_state.wizard_chat_open = False

    # Toggle
    label = "✕ Sluit coach" if st.session_state.wizard_chat_open else "💬 Vraag de coach"
    if st.button(label, key="wizard_chat_toggle", use_container_width=False):
        st.session_state.wizard_chat_open = not st.session_state.wizard_chat_open
        st.rerun()

    if not st.session_state.wizard_chat_open:
        return

    st.markdown("""
    <div style='background:#0f172a;border:1px solid #334155;border-radius:10px;
                padding:10px 14px;margin:8px 0 4px 0'>
      <span style='font-weight:800;color:#f97316;font-size:12px'>💬 CARBOO COACH</span>
      <span style='color:#64748b;font-size:10px;margin-left:8px'>Race nutrition assistent</span>
    </div>
    """, unsafe_allow_html=True)

    # Berichten
    if st.session_state.wizard_chat_msgs:
        for msg in st.session_state.wizard_chat_msgs[-6:]:  # toon max 6 laatste
            if msg["role"] == "user":
                st.markdown(f'<div style="background:#f97316;color:white;border-radius:8px;padding:6px 10px;font-size:11px;margin:3px 0;text-align:right">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#1e293b;color:#cbd5e1;border-radius:8px;padding:6px 10px;font-size:11px;margin:3px 0;border:1px solid #334155">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#1e293b;color:#94a3b8;border-radius:8px;padding:6px 10px;font-size:11px;border:1px solid #334155">👋 Stel een vraag over voeding, producten, timing, ...</div>', unsafe_allow_html=True)

    with st.form(key="wizard_chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            vraag = st.text_input("", placeholder="Stel je vraag...", label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("➤", use_container_width=True)

        if send and vraag.strip():
            # Voeg context toe aan eerste bericht
            vraag_met_context = vraag.strip()
            if context and not st.session_state.wizard_chat_msgs:
                vraag_met_context = f"[Context: {context}]\n{vraag.strip()}"
            
            st.session_state.wizard_chat_msgs.append({"role": "user", "content": vraag_met_context})
            antwoord = _gemini_call(st.session_state.wizard_chat_msgs)
            st.session_state.wizard_chat_msgs.append({"role": "assistant", "content": antwoord})
            st.rerun()

    if st.session_state.wizard_chat_msgs:
        if st.button("🗑 Wis", key="wizard_chat_reset"):
            st.session_state.wizard_chat_msgs = []
            st.rerun()
