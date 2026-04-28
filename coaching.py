import streamlit as st
from login import _get_supabase, _get_user, _get_user_by_id

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _laad_mijn_atleten(coach_id: str) -> list:
    """Haal alle atleten op voor deze coach."""
    try:
        r = _get_supabase().table("carboo_coaching")            .select("*,atleet:atleet_id(id,naam,email)")            .eq("coach_id", coach_id).execute()
        return r.data or []
    except: return []

def _laad_mijn_coaches(atleet_id: str) -> list:
    """Haal alle coaches op die deze atleet volgen."""
    try:
        r = _get_supabase().table("carboo_coaching")            .select("*,coach:coach_id(id,naam,email)")            .eq("atleet_id", atleet_id).execute()
        return r.data or []
    except: return []

def _stuur_uitnodiging(coach_id: str, atleet_email: str) -> str:
    """Stuur uitnodiging naar atleet. Geeft status terug."""
    atleet = _get_user(atleet_email)
    if not atleet:
        return "❌ Geen gebruiker gevonden met dit e-mailadres."
    if atleet["id"] == coach_id:
        return "❌ Je kan jezelf niet uitnodigen."
    # Check limiet
    bestaand = _laad_mijn_atleten(coach_id)
    if len([a for a in bestaand if a["status"] == "actief"]) >= 700:
        return "❌ Maximum van 700 atleten bereikt."
    # Check of al uitgenodigd
    al_uitgenodigd = [a for a in bestaand if a.get("atleet",{}).get("email") == atleet_email]
    if al_uitgenodigd:
        status = al_uitgenodigd[0]["status"]
        if status == "actief": return "⚠️ Deze atleet is al actief gekoppeld."
        if status == "uitgenodigd": return "⚠️ Uitnodiging al verstuurd."
    try:
        _get_supabase().table("carboo_coaching").insert({
            "coach_id":  coach_id,
            "atleet_id": atleet["id"],
            "status":    "uitgenodigd",
        }).execute()
        return f"✅ Uitnodiging verstuurd naar {atleet['naam']}."
    except Exception as e:
        return f"❌ Fout: {e}"

def _atleet_reageer(koppeling_id: str, accepteer: bool):
    """Atleet accepteert of weigert uitnodiging."""
    try:
        _get_supabase().table("carboo_coaching").update({
            "status": "actief" if accepteer else "geweigerd"
        }).eq("id", koppeling_id).execute()
        return True
    except: return False

def _verwijder_koppeling(koppeling_id: str):
    try:
        _get_supabase().table("carboo_coaching").delete().eq("id", koppeling_id).execute()
        return True
    except: return False

def _laad_atleet_scores(atleet_id: str, n_dagen: int = 14) -> list:
    """Haal performance scores op voor een atleet (enkel scores, geen details)."""
    try:
        from datetime import date, timedelta
        start = (date.today() - timedelta(days=n_dagen)).isoformat()
        # Performance scores uit welzijn tabel
        r = _get_supabase().table("fuelc_dagboek_welzijn")            .select("datum,energie_score,slaap_kwaliteit,spierpijn,stemming,stress")            .eq("user_id", atleet_id).gte("datum", start)            .order("datum").execute()
        return r.data or []
    except: return []

def _laad_atleet_dagboek_check(atleet_id: str, n_dagen: int = 7) -> dict:
    """Check enkel of atleet dagboek heeft ingevuld (ja/nee per dag)."""
    try:
        from datetime import date, timedelta
        start = (date.today() - timedelta(days=n_dagen)).isoformat()
        r = _get_supabase().table("fuelc_dagboek")            .select("datum")            .eq("user_id", atleet_id).gte("datum", start).execute()
        dagen_met_data = set(row["datum"][:10] for row in (r.data or []))
        return {str(date.today() - timedelta(days=i)): (str(date.today() - timedelta(days=i)) in dagen_met_data)
                for i in range(n_dagen)}
    except: return {}

# ─── UITNODIGINGEN voor atleet ────────────────────────────────────────────────
def render_coach_uitnodigingen(user_id: str):
    """Toon openstaande uitnodigingen voor atleet bovenaan de app."""
    uitnodigingen = [c for c in _laad_mijn_coaches(user_id) if c["status"] == "uitgenodigd"]
    if not uitnodigingen: return
    st.markdown(
        f'<div style="background:#1a1200;border-left:3px solid #f97316;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;">'
        f'<div style="font-size:0.78rem;color:#fbbf24;font-weight:700;margin-bottom:6px;">📬 {len(uitnodigingen)} openstaande uitnodiging(en)</div>',
        unsafe_allow_html=True)
    for uitn in uitnodigingen:
        coach_naam = uitn.get("coach",{}).get("naam","Coach")
        coach_email = uitn.get("coach",{}).get("email","")
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            st.markdown(f'<div style="font-size:0.82rem;color:#f1f5f9;padding:6px 0;">'
                f'<b>{coach_naam}</b> ({coach_email}) wil je volgen als atleet.</div>',
                unsafe_allow_html=True)
        with c2:
            if st.button("✓ Accepteer", key=f"acc_{uitn['id']}", use_container_width=True, type="primary"):
                _atleet_reageer(uitn["id"], True)
                st.rerun()
        with c3:
            if st.button("✗ Weiger", key=f"weig_{uitn['id']}", use_container_width=True):
                _atleet_reageer(uitn["id"], False)
                st.rerun()

# ─── COACH DASHBOARD ──────────────────────────────────────────────────────────
def render_coach_dashboard(user: dict):
    """Volledig coach dashboard."""
    coach_id = user.get("id","")
    user_db  = _get_user_by_id(coach_id) or {}
    max_atleten = int(user_db.get("max_atleten") or 700)

    st.markdown('<div style="font-size:1.3rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">👥 Coach Dashboard</div>', unsafe_allow_html=True)

    atleten = _laad_mijn_atleten(coach_id)
    actief  = [a for a in atleten if a["status"] == "actief"]
    uitgen  = [a for a in atleten if a["status"] == "uitgenodigd"]

    # Stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:14px;text-align:center;">'
            f'<div style="font-size:0.6rem;color:#64748b;">ACTIEVE ATLETEN</div>'
            f'<div style="font-size:1.8rem;font-weight:900;color:#22c55e;">{len(actief)}</div>'
            f'<div style="font-size:0.65rem;color:#475569;">/ {max_atleten} max</div></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:14px;text-align:center;">'
            f'<div style="font-size:0.6rem;color:#64748b;">UITNODIGINGEN</div>'
            f'<div style="font-size:1.8rem;font-weight:900;color:#fbbf24;">{len(uitgen)}</div>'
            f'<div style="font-size:0.65rem;color:#475569;">wachtend op respons</div></div>',
            unsafe_allow_html=True)
    with c3:
        # Hoeveel hebben vandaag dagboek ingevuld
        vandaag = str(__import__('datetime').date.today())
        actief_vandaag = 0
        # (Snelle check zonder alle data te laden)
        st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:14px;text-align:center;">'
            f'<div style="font-size:0.6rem;color:#64748b;">SLOTS BESCHIKBAAR</div>'
            f'<div style="font-size:1.8rem;font-weight:900;color:#3b82f6;">{max_atleten - len(actief)}</div>'
            f'<div style="font-size:0.65rem;color:#475569;">vrije plekken</div></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Atleet uitnodigen ──────────────────────────────────────────────────────
    with st.expander("➕ Atleet uitnodigen"):
        email_in = st.text_input("E-mailadres atleet", placeholder="atleet@email.com", key="coach_invite_email")
        if st.button("Uitnodiging sturen", key="coach_invite_btn", use_container_width=True):
            if email_in:
                result = _stuur_uitnodiging(coach_id, email_in.strip())
                if result.startswith("✅"):
                    st.success(result)
                elif result.startswith("⚠️"):
                    st.warning(result)
                else:
                    st.error(result)
            else:
                st.error("Vul een e-mailadres in.")

    # ── Openstaande uitnodigingen ──────────────────────────────────────────────
    if uitgen:
        st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#fbbf24;margin:16px 0 8px;">⏳ OPENSTAANDE UITNODIGINGEN</div>', unsafe_allow_html=True)
        for uitn in uitgen:
            naam  = uitn.get("atleet",{}).get("naam","?")
            email = uitn.get("atleet",{}).get("email","?")
            col_n, col_v = st.columns([4,1])
            with col_n:
                st.markdown(f'<div style="font-size:0.82rem;color:#94a3b8;padding:6px 0;">{naam} · {email}</div>',
                    unsafe_allow_html=True)
            with col_v:
                if st.button("🗑", key=f"del_uitn_{uitn['id']}", use_container_width=True):
                    _verwijder_koppeling(uitn["id"]); st.rerun()

    # ── Actieve atleten overview ───────────────────────────────────────────────
    if actief:
        st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#22c55e;margin:16px 0 8px;">✓ ACTIEVE ATLETEN</div>', unsafe_allow_html=True)
        for a in actief:
            atleet_id   = a.get("atleet",{}).get("id","")
            atleet_naam = a.get("atleet",{}).get("naam","?")
            with st.expander(f"👤 {atleet_naam}"):
                # Dagboek check
                dagboek = _laad_atleet_dagboek_check(atleet_id, 7)
                dagen_ingevuld = sum(1 for v in dagboek.values() if v)
                # Welzijn scores
                scores = _laad_atleet_scores(atleet_id, 14)

                col_a, col_b = st.columns([1,2])
                with col_a:
                    st.markdown('<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;">DAGBOEK LAATSTE 7 DAGEN</div>', unsafe_allow_html=True)
                    dag_html = ""
                    for dag_str, ingevuld in sorted(dagboek.items()):
                        kleur = "#22c55e" if ingevuld else "#1e293b"
                        dag_lbl = dag_str[8:]  # DD
                        dag_html += f'<div style="display:inline-block;width:28px;height:28px;border-radius:4px;background:{kleur};text-align:center;line-height:28px;font-size:0.65rem;color:#{"f8fafc" if ingevuld else "475569"};margin:2px;">{dag_lbl}</div>'
                    st.markdown(dag_html + f'<div style="font-size:0.72rem;color:#64748b;margin-top:4px;">{dagen_ingevuld}/7 dagen ingevuld</div>',
                        unsafe_allow_html=True)

                with col_b:
                    if scores:
                        st.markdown('<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;">WELZIJN (gem. 14 dagen)</div>', unsafe_allow_html=True)
                        WELZ = [
                            ("⚡ Energie",    "energie_score",   10),
                            ("😴 Slaap",      "slaap_kwaliteit", 10),
                            ("💪 Spierpijn",  "spierpijn",        5),
                            ("😊 Stemming",   "stemming",        10),
                        ]
                        for lbl, key, max_v in WELZ:
                            vals = [float(s.get(key,0) or 0) for s in scores if s.get(key)]
                            if not vals: continue
                            gem = round(sum(vals)/len(vals),1)
                            pct = round(gem/max_v*100)
                            kl  = "#22c55e" if pct>=60 else ("#fbbf24" if pct>=30 else "#ef4444")
                            st.markdown(
                                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
                                f'<div style="min-width:90px;font-size:0.72rem;color:#94a3b8;">{lbl}</div>'
                                f'<div style="flex:1;background:#0f172a;border-radius:3px;height:5px;">'
                                f'<div style="width:{pct}%;height:100%;background:{kl};border-radius:3px;"></div></div>'
                                f'<div style="min-width:40px;font-size:0.72rem;color:{kl};text-align:right;">{gem}/{max_v}</div></div>',
                                unsafe_allow_html=True)
                    else:
                        st.caption("Nog geen welzijnsdata beschikbaar.")

                if st.button("🔗 Koppeling verwijderen", key=f"del_act_{a['id']}", use_container_width=True):
                    _verwijder_koppeling(a["id"]); st.rerun()
    elif not uitgen:
        st.info("Nog geen atleten gekoppeld. Stuur een uitnodiging om te starten.")

    if st.button("← Terug naar menu", key="coach_terug"):
        st.session_state.module = "menu"; st.rerun()
