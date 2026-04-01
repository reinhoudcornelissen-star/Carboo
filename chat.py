import streamlit as st
import google.generativeai as genai

def show_chat():
    # 1. Stijlvolle titel
    st.markdown("### 🤖 Carboo AI Coach")
    st.info("Stel je vragen over training, voeding of herstel.")

    # 2. Configuratie van de Gemini API
    # Zorg dat 'GOOGLE_API_KEY' in je Streamlit Cloud Secrets staat!
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction="Je bent de Carboo AI Coach. Je helpt atleten met vragen over voeding, koolhydraten en herstel. Wees motiverend, deskundig en houd je antwoorden to-the-point."
        )
    except Exception as e:
        st.error("API Sleutel niet gevonden. Controleer je Streamlit Secrets.")
        return

    # 3. Chatgeschiedenis initialiseren in de sessie
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 4. Toon alle eerdere berichten
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 5. Gebruikersinput verwerken
    if prompt := st.chat_input("Hoe kan ik je vandaag helpen?"):
        # Voeg gebruikersbericht toe aan scherm en geschiedenis
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Genereer antwoord van de AI met een 'loading' spinner
        with st.chat_message("assistant"):
            with st.spinner("De coach denkt na..."):
                try:
                    response = model.generate_content(prompt)
                    answer = response.text
                    st.markdown(answer)
                    # Voeg AI-antwoord toe aan geschiedenis
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Er ging iets mis bij het ophalen van het antwoord: {e}")
