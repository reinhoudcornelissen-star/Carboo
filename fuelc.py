"""
FuelC — Carboo module voor energiebeheer sporters
Profiel & TDEE | Trainingszone | Bibliotheek | Dagschema | Dashboard
"""
import streamlit as st
from datetime import date, timedelta
from supabase import create_client


# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE CONNECTIE — zelfde aanpak als login.py
# ═══════════════════════════════════════════════════════════════════════════════

def _get_secrets(key: str, default: str = "") -> str:
    import os
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        return st.secrets[key]
    except:
        return default


def _get_supabase():
    url = _get_secrets("SUPABASE_URL")
    key = _get_secrets("SUPABASE_KEY")
    return create_client(url, key)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTEN
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVITEIT_FACTOR = {
    "Zittend (kantoorwerk, weinig beweging)":  1.2,
    "Licht actief (wandelen, staand werk)":    1.375,
    "Matig actief (lichamelijk werk)":         1.55,
}

DOELSTELLING_OPTIES = [
    "Gewicht houden",
    "Gewicht verliezen — 0.25 kg/week",
    "Gewicht verliezen — 0.5 kg/week",
    "Gewicht verliezen — 0.75 kg/week",
    "Gewicht aankomen — 0.25 kg/week",
    "Gewicht aankomen — 0.5 kg/week",
    "Prestatie (geen gewichtsdoel)",
]

DOELSTELLING_KCAL = {
    "Gewicht houden":                      0,
    "Gewicht verliezen — 0.25 kg/week": -275,
    "Gewicht verliezen — 0.5 kg/week":  -550,
    "Gewicht verliezen — 0.75 kg/week": -825,
    "Gewicht aankomen — 0.25 kg/week":  +275,
    "Gewicht aankomen — 0.5 kg/week":   +550,
    "Prestatie (geen gewichtsdoel)":        0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# BEREKENINGEN
# ═══════════════════════════════════════════════════════════════════════════════

def _bereken_bmr(geslacht: str, gewicht: float, lengte: int, leeftijd: int) -> int:
    """Mifflin-St Jeor formule."""
    if geslacht == "Man":
        bmr = 10 * gewicht + 6.25 * lengte - 5 * leeftijd + 5
    else:
        bmr = 10 * gewicht + 6.25 * lengte - 5 * leeftijd - 161
    return round(bmr)


def _bereken_tdee(bmr: int, activiteit: str) -> int:
    factor = ACTIVITEIT_FACTOR.get(activiteit, 1.2)
    return round(bmr * factor)


def _bereken_energie_doel(tdee: int, doelstelling: str) -> int:
    delta = DOELSTELLING_KCAL.get(doelstelling, 0)
    return tdee + delta


def _bereken_macros(energie_doel: int, kh_pct: int, eiwit_pct: int, vet_pct: int) -> dict:
    """Bereken macros in gram op basis van percentages."""
    return {
        "kh_g":    round(energie_doel * kh_pct    / 100 / 4),  # 4 kcal/g
        "eiwit_g": round(energie_doel * eiwit_pct / 100 / 4),  # 4 kcal/g
        "vet_g":   round(energie_doel * vet_pct   / 100 / 9),  # 9 kcal/g
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE — PROFIEL OPSLAAN / LADEN
# ═══════════════════════════════════════════════════════════════════════════════

def _laad_profiel(user_id: str) -> dict:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_profiel").select("*").eq("user_id", user_id).execute()
        return r.data[0] if r.data else {}
    except Exception as e:
        print(f"Fout bij laden profiel: {e}")
        return {}


def _sla_profiel_op(user_id: str, profiel: dict) -> bool:
    try:
        sb       = _get_supabase()
        bestaand = sb.table("fuelc_profiel").select("id").eq("user_id", user_id).execute()
        if bestaand.data:
            sb.table("fuelc_profiel").update(profiel).eq("user_id", user_id).execute()
        else:
            profiel["user_id"] = user_id
            sb.table("fuelc_profiel").insert(profiel).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan profiel: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# HULPFUNCTIES UI
# ═══════════════════════════════════════════════════════════════════════════════

def _sectie(titel: str, kleur: str = "#22c55e"):
    st.markdown(
        f'<div style="font-size:0.72rem;font-weight:700;color:{kleur};'
        f'letter-spacing:2px;margin:18px 0 8px;padding-bottom:4px;'
        f'border-bottom:1px solid #1e293b;">{titel}</div>',
        unsafe_allow_html=True)


def _metric_card(label: str, waarde: str, eenheid: str = "",
                 kleur: str = "#f97316", sub: str = ""):
    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;'
        f'padding:14px;text-align:center;">'
        f'<div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:6px;">'
        f'{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:800;color:{kleur};">{waarde}</div>'
        f'<div style="font-size:0.75rem;color:#64748b;">{eenheid}</div>'
        f'{"<div style=\'font-size:0.7rem;color:#475569;margin-top:4px;\'>" + sub + "</div>" if sub else ""}'
        f'</div>',
        unsafe_allow_html=True)


def _macro_balk(label: str, gram: int, pct: int, kleur: str):
    st.markdown(
        f'<div style="margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:0.78rem;margin-bottom:4px;">'
        f'<span style="color:#f8fafc;font-weight:600;">{label}</span>'
        f'<span style="color:{kleur};font-weight:700;">{gram}g &nbsp;·&nbsp; {pct}%</span>'
        f'</div>'
        f'<div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{kleur};border-radius:4px;"></div>'
        f'</div></div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STAP — PROFIEL & TDEE
# ═══════════════════════════════════════════════════════════════════════════════

def _stap_profiel(user: dict):
    user_id = user.get("id","")

    # Laad bestaand profiel uit Supabase of session state
    if "fc_profiel" not in st.session_state:
        st.session_state.fc_profiel = _laad_profiel(user_id)
    p = st.session_state.fc_profiel

    # ── BLOK 1: Basisgegevens ─────────────────────────────────────────────────
    _sectie("BASISGEGEVENS")
    c1, c2, c3 = st.columns(3)
    with c1:
        geslacht = st.radio("Geslacht", ["Man","Vrouw"],
                             index=["Man","Vrouw"].index(p.get("geslacht","Man")),
                             key="fc_geslacht", horizontal=True)
    with c2:
        leeftijd = st.number_input("Leeftijd", 16, 80,
                                    int(p.get("leeftijd", 30)), 1, key="fc_leeftijd")
    with c3:
        gewicht = st.number_input("Gewicht (kg)", 30.0, 200.0,
                                   float(p.get("gewicht_kg", 70.0)), 0.5,
                                   key="fc_gewicht")

    c4, c5 = st.columns(2)
    with c4:
        lengte = st.number_input("Lengte (cm)", 140, 220,
                                  int(p.get("lengte_cm", 175)), 1, key="fc_lengte")
    with c5:
        activiteit = st.selectbox(
            "Activiteitsniveau buiten sport",
            list(ACTIVITEIT_FACTOR.keys()),
            index=list(ACTIVITEIT_FACTOR.keys()).index(
                p.get("activiteit", list(ACTIVITEIT_FACTOR.keys())[0]))
            if p.get("activiteit") in ACTIVITEIT_FACTOR else 0,
            key="fc_activiteit")

    # ── BLOK 2: Doelstelling ──────────────────────────────────────────────────
    _sectie("DOELSTELLING")
    doelstelling = st.radio(
        "Wat is je voedingsdoel?",
        DOELSTELLING_OPTIES,
        index=DOELSTELLING_OPTIES.index(p.get("doelstelling", "Gewicht houden"))
        if p.get("doelstelling") in DOELSTELLING_OPTIES else 0,
        key="fc_doelstelling")

    # ── BLOK 3: Macro verdeling ───────────────────────────────────────────────
    _sectie("MACRO VERDELING")
    st.markdown(
        '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:10px;">'
        'Standaard verdeling voor sporters — pas aan naar voorkeur. '
        'Totaal moet 100% zijn.</div>',
        unsafe_allow_html=True)

    c6, c7, c8 = st.columns(3)
    with c6:
        kh_pct = st.number_input("Koolhydraten %", 20, 70,
                                   int(p.get("kh_doel_pct", 50)), 5, key="fc_kh_pct")
    with c7:
        eiwit_pct = st.number_input("Eiwit %", 10, 40,
                                     int(p.get("eiwit_doel_pct", 25)), 5, key="fc_eiwit_pct")
    with c8:
        vet_pct = st.number_input("Vet %", 10, 40,
                                   int(p.get("vet_doel_pct", 25)), 5, key="fc_vet_pct")

    totaal_pct = kh_pct + eiwit_pct + vet_pct
    if totaal_pct != 100:
        st.markdown(
            f'<div style="background:#1a0a0a;border-left:3px solid #ef4444;'
            f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#ef4444;">'
            f'⚠️ Totaal is {totaal_pct}% — moet 100% zijn.</div>',
            unsafe_allow_html=True)

    # ── Live berekening ───────────────────────────────────────────────────────
    bmr          = _bereken_bmr(geslacht, gewicht, lengte, leeftijd)
    tdee         = _bereken_tdee(bmr, activiteit)
    energie_doel = _bereken_energie_doel(tdee, doelstelling)
    macros       = _bereken_macros(energie_doel, kh_pct, eiwit_pct, vet_pct)

    _sectie("JOUW ENERGIEPROFIEL", "#22c55e")

    c9, c10, c11 = st.columns(3)
    with c9:
        _metric_card("BASISMETABOLISME", str(bmr), "kcal/dag",
                     "#4ade80", "BMR — Mifflin-St Jeor")
    with c10:
        _metric_card("TDEE BASIS", str(tdee), "kcal/dag",
                     "#22c55e", "Zonder sport")
    with c11:
        delta      = DOELSTELLING_KCAL.get(doelstelling, 0)
        delta_txt  = (f"+{delta}" if delta > 0 else str(delta)) if delta != 0 else "±0"
        doel_kleur = "#22c55e" if delta >= 0 else "#ef4444"
        _metric_card("ENERGIE DOEL", str(energie_doel), "kcal/dag",
                     doel_kleur, f"TDEE {delta_txt} kcal")

    # Macro balken
    st.markdown("<br>", unsafe_allow_html=True)
    _sectie("MACRO DOELEN PER DAG")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        _macro_balk("Koolhydraten", macros["kh_g"],    kh_pct,    "#22c55e")
        _macro_balk("Eiwit",        macros["eiwit_g"], eiwit_pct, "#16a34a")
    with col_m2:
        _macro_balk("Vet",          macros["vet_g"],   vet_pct,   "#86efac")
        st.markdown(
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;'
            f'padding:10px 14px;font-size:0.8rem;color:#94a3b8;margin-top:4px;">'
            f'💡 Sport verhoogt je dagelijkse behoefte. '
            f'FuelC past dit automatisch aan op basis van je trainingen.</div>',
            unsafe_allow_html=True)

    # ── Opslaan ───────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<style>[data-testid="stButton"] button[kind="primary"],'
        '.fc-groen button{background:#22c55e!important;color:#0a0f1e!important;'
        'font-weight:800!important;}</style>',
        unsafe_allow_html=True)
    if totaal_pct == 100:
        c_ops, c_vol = st.columns(2)
        with c_ops:
            opslaan_klik = st.button("💾 Opslaan", key="fc_prof_opslaan",
                         use_container_width=True)
        with c_vol:
            if st.session_state.fc_profiel.get("bmr"):
                if st.button("Volgende →", key="fc_prof_volgende",
                             use_container_width=True):
                    st.session_state.fc_stap = 2
                    st.rerun()
        if opslaan_klik:
            profiel_data = {
                "geslacht":       geslacht,
                "leeftijd":       leeftijd,
                "gewicht_kg":     gewicht,
                "lengte_cm":      lengte,
                "activiteit":     activiteit,
                "doelstelling":   doelstelling,
                "doel_tempo":     abs(DOELSTELLING_KCAL.get(doelstelling, 0)) / 1100,
                "bmr":            bmr,
                "tdee_basis":     tdee,
                "energie_doel":   energie_doel,
                "kh_doel_pct":    kh_pct,
                "eiwit_doel_pct": eiwit_pct,
                "vet_doel_pct":   vet_pct,
            }
            if _sla_profiel_op(user_id, profiel_data):
                st.session_state.fc_profiel = profiel_data
                st.success("✅ Profiel opgeslagen!")
                st.rerun()
    else:
        st.button("💾 Profiel opslaan →", key="fc_prof_opslaan",
                  use_container_width=True, disabled=True)
        st.caption("Corrigeer de macro verdeling naar 100% voor je kan opslaan.")


# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDERS ANDERE BLOKKEN
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 2 — TRAININGEN (MANUELE INVOER)
# ═══════════════════════════════════════════════════════════════════════════════

SPORT_OPTIES = ["Lopen", "Fietsen", "Zwemmen", "Kracht", "Andere"]

ZONE_OPTIES = ["Z1 — Herstel (zeer rustig)", "Z2 — Duurzaam (rustig)",
               "Z3 — Tempo (matig)", "Z4 — Drempel (zwaar)",
               "Z5 — VO2max (maximaal)"]

ZONE_MET = {
    "Z1 — Herstel (zeer rustig)":   4.0,
    "Z2 — Duurzaam (rustig)":       6.0,
    "Z3 — Tempo (matig)":           8.5,
    "Z4 — Drempel (zwaar)":        10.5,
    "Z5 — VO2max (maximaal)":      13.0,
}

ZONE_HERSTEL = {
    "Z1 — Herstel (zeer rustig)":   8,
    "Z2 — Duurzaam (rustig)":      16,
    "Z3 — Tempo (matig)":          24,
    "Z4 — Drempel (zwaar)":        36,
    "Z5 — VO2max (maximaal)":      48,
}

def _bereken_kcal(gewicht_kg: float, minuten: float, zone: str) -> int:
    """MET-gebaseerde kcalberekening."""
    met = ZONE_MET.get(zone, 6.0)
    return round((met * gewicht_kg * 3.5 / 200) * minuten)

def _dominante_zone(opwarming_zone, kern_zone, kern_min, opw_min, cool_min) -> str:
    """Bepaal dominante zone op basis van tijd in elke zone."""
    zones = {}
    zones[opwarming_zone] = zones.get(opwarming_zone, 0) + opw_min
    zones[kern_zone]      = zones.get(kern_zone, 0) + kern_min
    zones["Z1 — Herstel (zeer rustig)"] = zones.get("Z1 — Herstel (zeer rustig)", 0) + cool_min
    return max(zones, key=zones.get)

def _laad_trainingen(user_id: str) -> list:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_trainingen").select("*").eq("user_id", user_id).order("datum", desc=True).limit(30).execute()
        return r.data or []
    except Exception as e:
        print(f"Fout laden trainingen: {e}")
        return []

def _sla_training_op(user_id: str, training: dict) -> bool:
    try:
        sb = _get_supabase()
        training["user_id"] = user_id
        training["bron"]    = "manueel"
        sb.table("fuelc_trainingen").insert(training).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan training: {e}")
        return False

def _verwijder_training(training_id: str) -> bool:
    try:
        sb = _get_supabase()
        sb.table("fuelc_trainingen").delete().eq("id", training_id).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij verwijderen: {e}")
        return False

def _stap_trainingen(user: dict):
    user_id = user.get("id", "")

    # Laad profiel voor gewicht
    profiel = st.session_state.get("fc_profiel", {})
    gewicht = float(profiel.get("gewicht_kg", 70) or 70)

    _sectie("TRAININGEN TOEVOEGEN", "#22c55e")

    # ── Tabs: Toevoegen / Overzicht ───────────────────────────────────────────
    tab_add, tab_lijst = st.tabs(["➕  Training toevoegen", "📋  Mijn trainingen"])

    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Algemeen ─────────────────────────────────────────────────────────
        _sectie("ALGEMEEN", "#22c55e")
        c1, c2, c3 = st.columns(3)
        with c1:
            sport = st.selectbox("Sport", SPORT_OPTIES, key="tr_sport")
        with c2:
            datum = st.date_input("Datum", key="tr_datum")
        with c3:
            omschrijving = st.text_input("Naam / omschrijving (optioneel)",
                                          placeholder="bijv. Lange duurloop",
                                          key="tr_naam")

        # ── Opwarming ─────────────────────────────────────────────────────────
        _sectie("OPWARMING", "#22c55e")
        ow1, ow2 = st.columns(2)
        with ow1:
            opw_min = st.number_input("Duur (minuten)", 0, 60, 10,
                                       key="tr_opw_min")
        with ow2:
            opw_zone = st.selectbox("Intensiteitszone", ZONE_OPTIES,
                                     index=0, key="tr_opw_zone")
        opw_kcal = _bereken_kcal(gewicht, opw_min, opw_zone) if opw_min > 0 else 0
        if opw_min > 0:
            st.markdown(
                f'<div style="font-size:0.75rem;color:#22c55e;margin-top:-8px;margin-bottom:4px;">'
                f'≈ {opw_kcal} kcal</div>', unsafe_allow_html=True)

        # ── Kern ──────────────────────────────────────────────────────────────
        _sectie("KERN", "#22c55e")
        k1, k2 = st.columns(2)
        with k1:
            kern_min = st.number_input("Duur (minuten)", 0, 300, 40,
                                        key="tr_kern_min")
        with k2:
            kern_zone = st.selectbox("Intensiteitszone", ZONE_OPTIES,
                                      index=1, key="tr_kern_zone")

        # Intervalblokken
        gebruik_interval = st.checkbox("Intervalblokken toevoegen", key="tr_interval_aan")
        interval_tekst = ""
        if gebruik_interval:
            ic1, ic2, ic3, ic4 = st.columns(4)
            with ic1:
                int_herhalingen = st.number_input("Herhalingen", 1, 20, 5, key="tr_int_herh")
            with ic2:
                int_werk_min = st.number_input("Werkblok (min)", 1, 30, 4, key="tr_int_werk")
            with ic3:
                int_rust_min = st.number_input("Rustblok (min)", 1, 15, 2, key="tr_int_rust")
            with ic4:
                int_zone = st.selectbox("Zone werk", ZONE_OPTIES, index=3, key="tr_int_zone")
            interval_tekst = f"{int_herhalingen}× {int_werk_min}min {int_zone.split(' ')[0]} + {int_rust_min}min herstel"
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#22c55e;">'
                f'📋 {interval_tekst}</div>', unsafe_allow_html=True)

        kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone) if kern_min > 0 else 0
        if kern_min > 0:
            st.markdown(
                f'<div style="font-size:0.75rem;color:#22c55e;margin-top:-8px;margin-bottom:4px;">'
                f'≈ {kern_kcal} kcal</div>', unsafe_allow_html=True)

        # ── Cooling down ──────────────────────────────────────────────────────
        _sectie("COOLING DOWN", "#22c55e")
        cd1, cd2 = st.columns(2)
        with cd1:
            cool_min = st.number_input("Duur (minuten)", 0, 30, 10,
                                        key="tr_cool_min")
        with cd2:
            st.selectbox("Intensiteitszone", ["Z1 — Herstel (zeer rustig)"],
                         key="tr_cool_zone", disabled=True)
        cool_kcal = _bereken_kcal(gewicht, cool_min, "Z1 — Herstel (zeer rustig)") if cool_min > 0 else 0
        if cool_min > 0:
            st.markdown(
                f'<div style="font-size:0.75rem;color:#22c55e;margin-top:-8px;margin-bottom:4px;">'
                f'≈ {cool_kcal} kcal</div>', unsafe_allow_html=True)

        # ── Optioneel ─────────────────────────────────────────────────────────
        _sectie("OPTIONEEL", "#86efac")
        o1, o2, o3, o4 = st.columns(4)
        with o1:
            hartslag_gem = st.number_input("Hartslag gem (bpm)", 0, 220, 0, key="tr_hs_gem")
        with o2:
            afstand_km = st.number_input("Afstand (km)", 0.0, 300.0, 0.0, 0.1, key="tr_afstand")
        with o3:
            hoogtemeters = st.number_input("Hoogtemeters", 0, 5000, 0, key="tr_hoogte")
        with o4:
            notitie = st.text_input("Notitie", placeholder="bijv. Goed gevoel", key="tr_notitie")

        # ── Totalen ───────────────────────────────────────────────────────────
        totaal_min   = opw_min + kern_min + cool_min
        totaal_kcal  = opw_kcal + kern_kcal + cool_kcal
        dom_zone     = _dominante_zone(opw_zone, kern_zone, kern_min, opw_min, cool_min) if totaal_min > 0 else "—"
        herstel_uren = ZONE_HERSTEL.get(dom_zone, 16) if totaal_min > 0 else 0

        if totaal_min > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("SAMENVATTING", "#22c55e")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                _metric_card("TOTALE DUUR", f"{totaal_min // 60}u{totaal_min % 60:02d}",
                             "min", "#22c55e")
            with m2:
                _metric_card("KCAL VERBRANDING", str(totaal_kcal), "kcal", "#4ade80")
            with m3:
                dom_kort = dom_zone.split("—")[0].strip()
                _metric_card("DOMINANTE ZONE", dom_kort, "", "#16a34a")
            with m4:
                _metric_card("HERSTELTIJD", str(herstel_uren), "uur", "#86efac")

        # ── Opslaan ───────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if totaal_min > 0:
            if st.button("💾 Training opslaan", key="tr_opslaan",
                         use_container_width=True):
                zone_verdeling = {
                    "z1": opw_min + cool_min if "Z1" in opw_zone else cool_min,
                    "z2": kern_min if "Z2" in kern_zone else (opw_min if "Z2" in opw_zone else 0),
                    "z3": kern_min if "Z3" in kern_zone else (opw_min if "Z3" in opw_zone else 0),
                    "z4": kern_min if "Z4" in kern_zone else (opw_min if "Z4" in opw_zone else 0),
                    "z5": kern_min if "Z5" in kern_zone else (opw_min if "Z5" in opw_zone else 0),
                }
                training_data = {
                    "datum":          str(datum),
                    "sport":          sport,
                    "duur_min":       totaal_min,
                    "afstand_km":     afstand_km if afstand_km > 0 else None,
                    "hartslag_gem":   hartslag_gem if hartslag_gem > 0 else None,
                    "hoogte":         hoogtemeters if hoogtemeters > 0 else None,
                    "kcal_verbranding": totaal_kcal,
                    "hersteltijd_uur": herstel_uren,
                    "zone_verdeling": zone_verdeling,
                    "notitie":        f"{omschrijving} | OPW: {opw_min}min {opw_zone.split()[0]} | KERN: {kern_min}min {kern_zone.split()[0]}{' | ' + interval_tekst if interval_tekst else ''} | COOL: {cool_min}min Z1{' | HS: ' + str(hartslag_gem) + 'bpm' if hartslag_gem > 0 else ''}{' | ' + str(afstand_km) + 'km' if afstand_km > 0 else ''}{' | ' + notitie if notitie else ''}".strip(" | "),
                }
                if _sla_training_op(user_id, training_data):
                    st.success("✅ Training opgeslagen!")
                    # Reset formulier
                    for k in ["tr_opw_min","tr_kern_min","tr_cool_min","tr_naam",
                              "tr_notitie","tr_afstand","tr_hs_gem","tr_hoogte",
                              "tr_interval_aan"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
        else:
            st.button("💾 Training opslaan", key="tr_opslaan",
                      use_container_width=True, disabled=True)
            st.caption("Vul minstens één blok in om op te slaan.")

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        trainingen = _laad_trainingen(user_id)

        if not trainingen:
            st.markdown(
                '<div style="text-align:center;color:#64748b;padding:30px;">'
                'Nog geen trainingen toegevoegd.</div>',
                unsafe_allow_html=True)
        else:
            # Weekoverzicht totalen
            from datetime import date, timedelta
            vandaag = date.today()
            week_start = vandaag - timedelta(days=vandaag.weekday())
            week_kcal = sum(
                t.get("kcal_verbranding", 0) or 0
                for t in trainingen
                if t.get("datum", "") >= str(week_start)
            )
            week_min = sum(
                t.get("duur_min", 0) or 0
                for t in trainingen
                if t.get("datum", "") >= str(week_start)
            )
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #22c55e;border-radius:10px;'
                f'padding:12px 16px;margin-bottom:16px;display:flex;gap:24px;">'
                f'<div><div style="font-size:0.65rem;color:#64748b;font-weight:700;">DEZE WEEK</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">'
                f'{week_min // 60}u{week_min % 60:02d} · {week_kcal} kcal</div></div>'
                f'<div><div style="font-size:0.65rem;color:#64748b;font-weight:700;">TRAININGEN</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">'
                f'{len([t for t in trainingen if t.get("datum","") >= str(week_start)])}</div></div>'
                f'</div>',
                unsafe_allow_html=True)

            # Lijst van trainingen
            SPORT_EMOJI = {"Lopen":"🏃","Fietsen":"🚴","Zwemmen":"🏊",
                           "Kracht":"💪","Andere":"⚡"}
            ZONE_KLEUR  = {"z1":"#64748b","z2":"#22c55e","z3":"#fbbf24",
                           "z4":"#f97316","z5":"#ef4444"}

            for t in trainingen:
                sport_em = SPORT_EMOJI.get(t.get("sport",""), "⚡")
                datum_str = t.get("datum","")[:10]
                duur_min  = t.get("duur_min", 0) or 0
                duur_str  = f"{duur_min // 60}u{duur_min % 60:02d}"
                kcal      = t.get("kcal_verbranding", 0) or 0
                herstel   = t.get("hersteltijd_uur", 0) or 0
                notitie   = t.get("notitie", "") or ""
                notitie_kort = notitie[:60] + "..." if len(notitie) > 60 else notitie

                # Zone balken
                zv = t.get("zone_verdeling") or {}
                if isinstance(zv, str):
                    import json
                    try: zv = json.loads(zv)
                    except: zv = {}
                totaal_zv = sum(zv.values()) if zv else duur_min or 1
                zone_balken = ""
                for z, kleur in ZONE_KLEUR.items():
                    pct = round((zv.get(z, 0) / totaal_zv) * 100) if totaal_zv > 0 else 0
                    if pct > 0:
                        zone_balken += (
                            f'<div style="display:inline-block;width:{pct}%;height:6px;'
                            f'background:{kleur};"></div>'
                        )

                with st.expander(
                    f"{sport_em} {t.get('sport','')} — {datum_str} — {duur_str} — {kcal} kcal",
                    expanded=False):
                    st.markdown(
                        f'<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">'
                        f'{notitie_kort}</div>'
                        f'<div style="background:#1e293b;border-radius:4px;height:8px;'
                        f'overflow:hidden;margin-bottom:8px;">{zone_balken}</div>'
                        f'<div style="font-size:0.72rem;color:#64748b;">'
                        f'Hersteltijd: {herstel}u'
                        f'{" · " + str(t.get("afstand_km")) + "km" if t.get("afstand_km") else ""}'
                        f'{" · " + str(t.get("hartslag_gem")) + " bpm" if t.get("hartslag_gem") else ""}'
                        f'</div>',
                        unsafe_allow_html=True)
                    if st.button("🗑 Verwijderen", key=f"tr_del_{t['id']}",
                                 use_container_width=False):
                        if _verwijder_training(t["id"]):
                            st.success("Verwijderd.")
                            st.rerun()


def _stap_bibliotheek(user: dict):
    _sectie("VOEDSELBIBLIOTHEEK", "#22c55e")
    st.info("🚧 Blok 5 → 3 — Bibliotheek — wordt binnenkort gebouwd.")


def _stap_dagschema(user: dict):
    _sectie("DAGSCHEMA", "#22c55e")
    st.info("🚧 Blok 3 — Dagschema — wordt gebouwd na Bibliotheek.")


def _stap_dashboard(user: dict):
    _sectie("DASHBOARD", "#22c55e")
    st.info("🚧 Blok 4 — Dashboard — wordt binnenkort gebouwd.")


# ═══════════════════════════════════════════════════════════════════════════════
# HOOFDFUNCTIE
# ═══════════════════════════════════════════════════════════════════════════════

def render_fuelc(user: dict):
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">'
        '<div style="font-size:2rem;font-weight:900;letter-spacing:3px;color:#f8fafc;">'
        'FUEL<span style="color:#22c55e;">C</span></div>'
        '<div style="font-size:0.85rem;font-weight:700;color:#22c55e;letter-spacing:2px;'
        'border:1px solid #22c55e;border-radius:6px;padding:3px 10px;">'
        'ENERGIE COACH</div>'
        '</div>',
        unsafe_allow_html=True)

    st.markdown(
        '<style>.fc-terug button{background:#0f172a!important;border:1px solid #22c55e!important;'
        'color:#22c55e!important;font-size:0.8rem!important;padding:6px 14px!important;'
        'width:auto!important;border-radius:8px!important;}</style>',
        unsafe_allow_html=True)
    if st.button("← Terug naar modules", key="fc_terug_top"):
        st.session_state.module = "menu"
        st.rerun()

    # Navigatiebalk
    stap  = st.session_state.get("fc_stap", 1)
    namen = ["Profiel","Trainingen","Bibliotheek","Dagschema","Dashboard"]
    cols  = st.columns(len(namen))
    for i, (col, naam_stap) in enumerate(zip(cols, namen)):
        actief = (i+1) == stap
        gedaan = i+1 < stap
        kleur  = "#22c55e" if actief else ("#86efac" if gedaan else "#334155")
        col.markdown(
            f'<div style="text-align:center;font-size:10px;font-weight:700;'
            f'color:{kleur};border-bottom:2px solid {kleur};padding-bottom:4px;">'
            f'{"✓ " if gedaan else ""}{naam_stap}</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Profiel geladen check
    if "fc_profiel" not in st.session_state:
        st.session_state.fc_profiel = _laad_profiel(user.get("id",""))

    profiel_ingevuld = bool(st.session_state.fc_profiel.get("bmr"))

    # Routing
    if   stap == 1: _stap_profiel(user)
    elif stap == 2:
        if not profiel_ingevuld:
            st.warning("Vul eerst je profiel in.")
            if st.button("← Naar profiel", key="fc_naar_prof"):
                st.session_state.fc_stap = 1
                st.rerun()
        else:
            _stap_trainingen(user)
    elif stap == 3: _stap_bibliotheek(user)
    elif stap == 4: _stap_dagschema(user)
    elif stap == 5: _stap_dashboard(user)

    # Navigatieknoppen onderaan (enkel tonen als profiel ingevuld)
    if profiel_ingevuld and stap > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        c_terug, c_next = st.columns([1,2])
        with c_terug:
            if st.button("← Vorige", key="fc_vorige", use_container_width=True):
                st.session_state.fc_stap = max(1, stap - 1)
                st.rerun()
        with c_next:
            if stap < len(namen):
                if st.button("Volgende →", key="fc_volgende", use_container_width=True):
                    st.session_state.fc_stap = stap + 1
                    st.rerun()
