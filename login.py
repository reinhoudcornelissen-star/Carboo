import streamlit as st
import json
import os
import hashlib
from datetime import datetime
import streamlit.components.v1 as components

USERS_FILE = "users.json"

# ── helpers ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def verify_user(username: str, password: str) -> bool:
    users = load_users()
    return (
        username in users
        and users[username]["password"] == hash_password(password)
    )


def register_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    return True


# ── HTML login page ───────────────────────────────────────────────────────────

def load_login_html() -> str:
    """Load the login.html file from the same directory as this script."""
    html_path = os.path.join(os.path.dirname(__file__), "login.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ── main login flow ───────────────────────────────────────────────────────────

def show_login_page():
    """
    Renders the custom HTML login page inside an iframe.
    Returns True when the user is authenticated, False otherwise.
    """

    # Session state defaults
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    if st.session_state.authenticated:
        return True

    # ── Register form (plain Streamlit, shown on demand) ──────────────────
    if st.session_state.show_register:
        st.markdown("## Registreren")
        new_user = st.text_input("Gebruikersnaam", key="reg_user")
        new_pass = st.text_input("Wachtwoord", type="password", key="reg_pass")
        new_pass2 = st.text_input("Herhaal wachtwoord", type="password", key="reg_pass2")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aanmaken"):
                if new_pass != new_pass2:
                    st.error("Wachtwoorden komen niet overeen.")
                elif not new_user or not new_pass:
                    st.error("Vul alle velden in.")
                elif register_user(new_user, new_pass):
                    st.success("Account aangemaakt! Je kan nu inloggen.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Gebruikersnaam is al in gebruik.")
        with col2:
            if st.button("Terug naar login"):
                st.session_state.show_register = False
                st.rerun()
        return False

    # ── Custom HTML login form ─────────────────────────────────────────────
    st.markdown(
        "<style>header, footer, [data-testid='stToolbar'] {display:none}</style>",
        unsafe_allow_html=True,
    )

    try:
        html_content = load_login_html()
        components.html(html_content, height=650, scrolling=False)
    except FileNotFoundError:
        st.error("⚠️ login.html niet gevonden. Zorg dat login.html naast login.py staat.")
        return False

    # ── Fallback native form (below the HTML, hidden via CSS trick) ────────
    # Streamlit kan geen JS postMessage ontvangen, dus we gebruiken
    # een verborgen native form als brug.
    with st.expander("🔐 Inloggen (fallback)", expanded=False):
        username = st.text_input("Gebruikersnaam", key="login_user")
        password = st.text_input("Wachtwoord", type="password", key="login_pass")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Inloggen", type="primary"):
                if verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Ongeldige gebruikersnaam of wachtwoord.")
        with col2:
            if st.button("Registreren"):
                st.session_state.show_register = True
                st.rerun()

    return False


# ── Entry point (only when login.py is run directly) ─────────────────────────

if __name__ == "__main__":
    st.set_page_config(
        page_title="Carboo – Login",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if show_login_page():
        st.success(f"Welkom terug, {st.session_state.current_user}! 🏃")
        if st.button("Uitloggen"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
