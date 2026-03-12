import streamlit as st
import json
import os
import hashlib
from datetime import datetime

USERS_FILE = "users.json"

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    if not os.path.exists(USERS_FILE):
        # Maak standaard admin gebruiker aan als het bestand niet bestaat
        default_users = [
            {
                "username": "admin",
                "password": hash_password("admin123"),
                "name": "Admin",
                "role": "admin",
                "created": datetime.now().isoformat()
            }
        ]
        save_users(default_users)
        return default_users
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def check_credentials(username, password):
    users = load_users()
    hashed = hash_password(password)
    for user in users:
        if user["username"] == username and user["password"] == hashed:
            return user
    return None


def register_user(username, password, name, role="user"):
    users = load_users()
    # Controleer of gebruiker al bestaat
    for u in users:
        if u["username"] == username:
            return False, "Gebruikersnaam bestaat al."
    new_user = {
        "username": username,
        "password": hash_password(password),
        "name": name,
        "role": role,
        "created": datetime.now().isoformat()
    }
    users.append(new_user)
    save_users(users)
    return True, "Registratie succesvol!"


# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────

def render_login_page():
    # Volledig scherm dark styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700;900&family=Rajdhani:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Exo 2', sans-serif;
        background-color: #030710 !important;
        color: #e2e8f0;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background: #030710 !important; }

    /* Verwijder lege ruimte bovenaan */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* Grid achtergrond */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(59,130,246,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59,130,246,0.06) 1px, transparent 1px);
        background-size: 60px 60px;
        pointer-events: none;
        z-index: 0;
    }

    /* Login card */
    .login-card {
        background: rgba(10, 20, 40, 0.90);
        border: 1px solid rgba(59,130,246,0.25);
        border-radius: 20px;
        padding: 2.5rem;
        backdrop-filter: blur(20px);
        box-shadow: 0 0 0 1px rgba(59,130,246,0.1),
                    0 20px 60px rgba(0,0,0,0.5),
                    inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
        margin-top: 1rem;
    }
    .login-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3b82f6, #f97316, transparent);
        animation: shimmer 3s linear infinite;
    }
    @keyframes shimmer {
        0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; }
    }

    /* Brand */
    .brand-name {
        font-family: 'Rajdhani', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        background: linear-gradient(135deg, #fff 30%, #fb923c 70%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        margin-bottom: 0;
    }
    .brand-subtitle {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.25em;
        color: #3b82f6;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        opacity: 0.85;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(59,130,246,0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'Exo 2', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        background: rgba(59,130,246,0.08) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    }
    .stTextInput label {
        color: #64748b !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
    }

    /* Login knop */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #2563eb 100%) !important;
        background-size: 200% 100% !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.18em !important;
        text-transform: uppercase !important;
        padding: 0.75rem !important;
        box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 30px rgba(37,99,235,0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Divider tekst */
    .divider-text {
        text-align: center;
        color: #64748b;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 1rem 0;
        position: relative;
    }
    .divider-text::before,
    .divider-text::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 40%;
        height: 1px;
        background: rgba(59,130,246,0.15);
    }
    .divider-text::before { left: 0; }
    .divider-text::after { right: 0; }

    /* Register link */
    .register-text {
        text-align: center;
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    .register-text a {
        color: #fb923c;
        font-weight: 600;
        text-decoration: none;
    }

    /* Error/success meldingen */
    .stAlert {
        border-radius: 8px !important;
    }

    /* Verberg het donkere blok bovenaan */
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        display: none !important;
    }
    .block-container { padding-top: 2rem !important; }

    /* Avatar float animatie */
    @keyframes hover-float {
        0%, 100% { transform: translateY(0px) rotate(-1deg); }
        50% { transform: translateY(-6px) rotate(1deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Haal avatar src op uit login.html
    import re
    avatar_src = ""
    if os.path.exists("login.html"):
        try:
            with open("login.html", "r") as f:
                content = f.read()
            match = re.search(r'<img[^>]+src="([^"]+)"[^>]*>', content)
            if match:
                avatar_src = match.group(1)
        except Exception:
            pass

    # Gecentreerde login card — geen linker kolom meer
    col_pad_l, col_login, col_pad_r = st.columns([1, 2, 1])

    with col_login:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # Avatar RECHTS van CARBOO titel, klein
        if avatar_src:
            st.markdown(f'''
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:4px;">
                <div>
                    <div class="brand-name">CARBOO</div>
                    <div class="brand-subtitle">Race Nutrition Platform</div>
                </div>
                <img src="{avatar_src}"
                     style="height:80px;width:auto;flex-shrink:0;
                            filter:drop-shadow(0 0 12px rgba(37,99,235,0.7)) drop-shadow(0 0 24px rgba(249,115,22,0.4));
                            animation:hover-float 4s ease-in-out infinite;">
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="brand-name">CARBOO</div>', unsafe_allow_html=True)
            st.markdown('<div class="brand-subtitle">Race Nutrition Platform</div>', unsafe_allow_html=True)

        # Toon registratie of login
        if st.session_state.get("show_register", False):
            _render_register_form()
        else:
            _render_login_form()

        st.markdown('</div>', unsafe_allow_html=True)


def _render_login_form():
    username = st.text_input("Gebruikersnaam", key="login_username", placeholder="Voer gebruikersnaam in")
    password = st.text_input("Wachtwoord", type="password", key="login_password", placeholder="Voer wachtwoord in")

    # Vergeten wachtwoord link
    st.markdown('<div style="text-align:right;margin-bottom:1rem;">'
                '<a href="#" style="font-size:0.72rem;color:#3b82f6;text-decoration:none;opacity:0.8;">'
                'Wachtwoord vergeten?</a></div>', unsafe_allow_html=True)

    if st.button("INLOGGEN", key="btn_login"):
        if not username or not password:
            st.error("Vul gebruikersnaam en wachtwoord in.")
        else:
            user = check_credentials(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.rerun()  # ← DE FIX: pagina herladen na inloggen
            else:
                st.error("Onjuiste gebruikersnaam of wachtwoord.")

    st.markdown('<div class="divider-text">of</div>', unsafe_allow_html=True)

    st.markdown('<div class="register-text">Nog geen account? '
                '</div>', unsafe_allow_html=True)

    if st.button("Registreer hier", key="btn_show_register"):
        st.session_state.show_register = True
        st.rerun()


def _render_register_form():
    st.markdown('<div style="color:#3b82f6;font-weight:700;font-size:0.85rem;'
                'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">'
                'Nieuw account aanmaken</div>', unsafe_allow_html=True)

    name = st.text_input("Volledige naam", key="reg_name", placeholder="Jouw naam")
    username = st.text_input("Gebruikersnaam", key="reg_username", placeholder="Kies een gebruikersnaam")
    password = st.text_input("Wachtwoord", type="password", key="reg_password", placeholder="Kies een wachtwoord")
    password2 = st.text_input("Bevestig wachtwoord", type="password", key="reg_password2", placeholder="Herhaal wachtwoord")

    if st.button("REGISTREREN", key="btn_register"):
        if not name or not username or not password or not password2:
            st.error("Vul alle velden in.")
        elif password != password2:
            st.error("Wachtwoorden komen niet overeen.")
        elif len(password) < 6:
            st.error("Wachtwoord moet minimaal 6 tekens zijn.")
        else:
            success, msg = register_user(username, password, name)
            if success:
                st.success(msg + " Je kunt nu inloggen.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error(msg)

    st.markdown('<div class="divider-text">of</div>', unsafe_allow_html=True)

    if st.button("← Terug naar inloggen", key="btn_back_login"):
        st.session_state.show_register = False
        st.rerun()


# ─── ADMIN PANEL ──────────────────────────────────────────────────────────────

def render_admin_panel():
    st.markdown("## 👥 Gebruikersbeheer")

    users = load_users()

    # Tabel van gebruikers
    if users:
        st.markdown("### Huidige gebruikers")
        for i, user in enumerate(users):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{user.get('name', '-')}**")
            with col2:
                st.write(user.get('username', '-'))
            with col3:
                role_color = "🔴" if user.get('role') == 'admin' else "🔵"
                st.write(f"{role_color} {user.get('role', 'user')}")
            with col4:
                if user.get('username') != st.session_state.current_user.get('username'):
                    if st.button("🗑️", key=f"del_user_{i}"):
                        users.pop(i)
                        save_users(users)
                        st.success(f"Gebruiker verwijderd.")
                        st.rerun()
    else:
        st.info("Geen gebruikers gevonden.")

    st.divider()

    # Nieuwe gebruiker toevoegen
    st.markdown("### Nieuwe gebruiker toevoegen")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Naam", key="admin_new_name")
        new_user = st.text_input("Gebruikersnaam", key="admin_new_user")
    with col2:
        new_pass = st.text_input("Wachtwoord", type="password", key="admin_new_pass")
        new_role = st.selectbox("Rol", ["user", "admin"], key="admin_new_role")

    if st.button("Gebruiker toevoegen", key="btn_add_user"):
        if not new_name or not new_user or not new_pass:
            st.error("Vul alle velden in.")
        else:
            success, msg = register_user(new_user, new_pass, new_name, new_role)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
