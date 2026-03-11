import streamlit as st
import json
import os
import hashlib
from datetime import datetime

USERS_FILE = "users.json"

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    # Default: enkel admin
    default = {
        "admin": {
            "password": _hash("carboo2024"),
            "name": "Admin",
            "role": "admin",
            "email": "admin@carboo.be",
            "created": str(datetime.now().date()),
            "active": True,
        }
    }
    _save_users(default)
    return default


def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────

def render_login_page():
    st.markdown("""
    <style>
    .login-wrap { max-width: 420px; margin: 60px auto 0 auto; }
    .login-logo { text-align:center; font-size:3rem; font-weight:900; letter-spacing:6px; color:#f8fafc; margin-bottom:4px; }
    .login-logo span { color:#f97316; }
    .login-sub { text-align:center; color:#64748b; font-size:0.85rem; letter-spacing:2px; margin-bottom:36px; }
    .login-card { background:#1e293b; border-radius:20px; padding:36px 32px; border:1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">CAR<span>BOO</span></div>
        <div class="login-sub">RACE NUTRITION PLATFORM</div>
        <div class="login-card">
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div style='color:#94a3b8; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:6px;'>GEBRUIKERSNAAM</div>", unsafe_allow_html=True)
        username = st.text_input("", placeholder="jouw gebruikersnaam", label_visibility="collapsed", key="login_user")

        st.markdown("<div style='color:#94a3b8; font-size:0.75rem; font-weight:700; letter-spacing:1px; margin-bottom:6px; margin-top:16px;'>WACHTWOORD</div>", unsafe_allow_html=True)
        password = st.text_input("", placeholder="••••••••", type="password", label_visibility="collapsed", key="login_pass")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀  INLOGGEN", key="login_btn", use_container_width=True):
            users = _load_users()
            u = users.get(username.lower().strip())
            if u and u.get("active", True) and u["password"] == _hash(password):
                st.session_state.logged_in = True
                st.session_state.current_user = {**u, "username": username.lower().strip()}
                st.rerun()
            else:
                st.markdown("""
                <div style="background:#fef2f2; border-left:4px solid #ef4444; padding:10px 14px; 
                     border-radius:8px; color:#991b1b; font-size:0.85rem; margin-top:12px;">
                    ❌ Ongeldige inloggegevens of account inactief.
                </div>
                """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; color:#475569; font-size:0.72rem; margin-top:24px;">
        © 2024 Carboo · Race Nutrition Platform
    </div>
    """, unsafe_allow_html=True)


# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

def render_admin_panel():
    st.markdown('<div class="section-title">⚙️ ADMIN — Gebruikersbeheer</div>', unsafe_allow_html=True)

    users = _load_users()

    tab_list, tab_new = st.tabs(["👥  GEBRUIKERSLIJST", "➕  NIEUW ACCOUNT"])

    # ─── GEBRUIKERSLIJST ─────────────────────────────────────────────────
    with tab_list:
        st.markdown(f"<div style='color:#64748b; font-size:0.8rem; margin-bottom:16px;'>{len(users)} account(s) aanwezig</div>", unsafe_allow_html=True)

        for uname, udata in users.items():
            role_color = "#8b5cf6" if udata["role"] == "admin" else "#22c55e"
            status_icon = "🟢" if udata.get("active", True) else "🔴"
            badge = f'<span style="background:{role_color}22; color:{role_color}; padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:700;">{udata["role"].upper()}</span>'

            with st.expander(f"{status_icon} **{udata['name']}** — `{uname}` {udata['role'].upper()}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**E-mail:** {udata.get('email','—')}")
                    st.markdown(f"**Aangemaakt:** {udata.get('created','—')}")
                with c2:
                    new_name = st.text_input("Naam", value=udata["name"], key=f"edit_name_{uname}")
                    new_email = st.text_input("E-mail", value=udata.get("email",""), key=f"edit_email_{uname}")
                with c3:
                    new_active = st.toggle("Account actief", value=udata.get("active", True), key=f"toggle_{uname}")
                    new_pw = st.text_input("Nieuw wachtwoord (optioneel)", type="password", key=f"pw_{uname}")

                col_save, col_del = st.columns(2)
                with col_save:
                    if st.button("💾 Opslaan", key=f"save_{uname}"):
                        users[uname]["name"] = new_name
                        users[uname]["email"] = new_email
                        users[uname]["active"] = new_active
                        if new_pw.strip():
                            users[uname]["password"] = _hash(new_pw.strip())
                        _save_users(users)
                        st.success("✅ Opgeslagen!")
                        st.rerun()
                with col_del:
                    if uname != "admin":
                        if st.button("🗑️ Verwijderen", key=f"del_{uname}"):
                            del users[uname]
                            _save_users(users)
                            st.warning(f"Gebruiker {uname} verwijderd.")
                            st.rerun()

    # ─── NIEUW ACCOUNT ────────────────────────────────────────────────────
    with tab_new:
        st.markdown("<div style='max-width:500px;'>", unsafe_allow_html=True)

        n_username = st.text_input("Gebruikersnaam *", placeholder="bijv. jan.peeters", key="new_uname")
        n_name     = st.text_input("Volledige naam *", placeholder="bijv. Jan Peeters", key="new_name")
        n_email    = st.text_input("E-mailadres", placeholder="jan@example.com", key="new_email")

        col1, col2 = st.columns(2)
        with col1:
            n_pw  = st.text_input("Wachtwoord *", type="password", key="new_pw")
        with col2:
            n_pw2 = st.text_input("Herhaal wachtwoord *", type="password", key="new_pw2")

        n_role = st.selectbox("Rol", ["atleet", "admin"], key="new_role")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕  ACCOUNT AANMAKEN", key="create_user_btn"):
            errors = []
            if not n_username.strip():
                errors.append("Gebruikersnaam is verplicht.")
            elif n_username.lower().strip() in users:
                errors.append("Gebruikersnaam bestaat al.")
            if not n_name.strip():
                errors.append("Naam is verplicht.")
            if not n_pw.strip():
                errors.append("Wachtwoord is verplicht.")
            elif n_pw != n_pw2:
                errors.append("Wachtwoorden komen niet overeen.")

            if errors:
                for e in errors:
                    st.markdown(f'<div class="alert-red">❌ {e}</div>', unsafe_allow_html=True)
            else:
                users[n_username.lower().strip()] = {
                    "password": _hash(n_pw),
                    "name": n_name.strip(),
                    "role": n_role,
                    "email": n_email.strip(),
                    "created": str(datetime.now().date()),
                    "active": True,
                }
                _save_users(users)
                st.markdown(f"""
                <div style="background:#f0fdf4; border-left:4px solid #22c55e; padding:14px; 
                     border-radius:8px; color:#14532d; font-size:0.9rem; margin-top:12px;">
                    ✅ Account <b>{n_username.lower().strip()}</b> aangemaakt voor <b>{n_name.strip()}</b>!<br>
                    <span style="font-size:0.8rem; color:#166534;">Tijdelijk wachtwoord: stuur dit veilig door aan de gebruiker.</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
