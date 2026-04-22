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

ZONE_LABELS = [
    "Z1 — Herstel",
    "Z2 — Duurzaam",
    "Z3 — Tempo",
    "Z4 — Drempel",
    "Z5 — VO2max",
]

ZONE_MET = {
    "Z1 — Herstel":    4.0,
    "Z2 — Duurzaam":   6.0,
    "Z3 — Tempo":      8.5,
    "Z4 — Drempel":   10.5,
    "Z5 — VO2max":    13.0,
}

def _bereken_kcal(gewicht_kg: float, minuten: float, zone: str) -> int:
    """MET-gebaseerde kcalberekening."""
    key = next((k for k in ZONE_MET if zone.startswith(k[:2])), None)
    met = ZONE_MET.get(key, 6.0) if key else 6.0
    return round((met * gewicht_kg * 3.5 / 200) * minuten)

def _dominante_zone(blokken: list) -> str:
    """Blokken = lijst van (zone_label, minuten)."""
    zones = {}
    for z, m in blokken:
        key = next((k for k in ZONE_MET if z.startswith(k[:2])), z)
        zones[key] = zones.get(key, 0) + m
    return max(zones, key=zones.get) if zones else "Z2 — Duurzaam"

def _laad_zones(user_id: str, sport: str) -> dict:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_zones").select("*").eq("user_id", user_id).eq("sport", sport).execute()
        return r.data[0] if r.data else {}
    except:
        return {}

def _sla_zones_op(user_id: str, sport: str, zones: dict) -> bool:
    try:
        sb = _get_supabase()
        bestaand = sb.table("fuelc_zones").select("id").eq("user_id", user_id).eq("sport", sport).execute()
        zones["user_id"] = user_id
        zones["sport"]   = sport
        if bestaand.data:
            sb.table("fuelc_zones").update(zones).eq("user_id", user_id).eq("sport", sport).execute()
        else:
            sb.table("fuelc_zones").insert(zones).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan zones: {e}")
        return False

def _laad_trainingen(user_id: str) -> list:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_trainingen").select("*").eq("user_id", user_id).order("datum", desc=True).limit(30).execute()
        return r.data or []
    except:
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

def _zone_info(zones: dict, zone_label: str, eenheid: str, sport: str) -> str:
    """Geef tempo/hs info voor een zone."""
    z_key = zone_label[:2].lower()
    if eenheid == "tempo" and sport == "Lopen":
        val = zones.get(f"{z_key}_tempo")
        if val:
            minuten = int(val)
            seconden = round((val - minuten) * 60)
            return f"{minuten}:{seconden:02d} min/km"
    elif eenheid == "watt":
        val = zones.get(f"{z_key}_tempo")
        if val: return f"{int(val)}W"
    elif eenheid in ("hartslag", None, ""):
        val = zones.get(f"{z_key}_hs")
        if val: return f"{int(val)} bpm"
    return ""

def _stap_trainingen(user: dict):
    user_id = user.get("id", "")
    profiel = st.session_state.get("fc_profiel", {})
    gewicht = float(profiel.get("gewicht_kg", 70) or 70)

    _sectie("TRAININGEN", "#22c55e")

    tab_add, tab_zones, tab_lijst = st.tabs([
        "➕  Training toevoegen",
        "⚙️  Zone kalibratie",
        "📋  Mijn trainingen",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — TRAINING TOEVOEGEN
    # ══════════════════════════════════════════════════════════════════════════
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
            omschrijving = st.text_input("Naam / omschrijving",
                placeholder="bijv. Lange duurloop", key="tr_naam")

        # Laad zones voor dit sport
        zones_data = _laad_zones(user_id, sport)
        eenheid    = zones_data.get("eenheid", "hartslag")

        # Invoermodus lopen: tijd of afstand
        if sport == "Lopen":
            invoer_modus = st.radio("Invoer op basis van",
                ["Tijd (minuten)", "Afstand (km)"],
                horizontal=True, key="tr_invoer_modus")
        else:
            invoer_modus = "Tijd (minuten)"

        def _zone_selectbox(label, key, default_idx=1):
            """Zone selectbox met kalibratie-info."""
            zone = st.selectbox(label, ZONE_LABELS, index=default_idx, key=key)
            info = _zone_info(zones_data, zone, eenheid, sport)
            if info:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#86efac;margin-top:-8px;'
                    f'margin-bottom:4px;">→ {info}</div>',
                    unsafe_allow_html=True)
            return zone

        def _invoer_blok(prefix, label_min, label_km, default_min, default_km, zone_idx):
            """Invoerblok met tijd of km keuze."""
            if invoer_modus == "Afstand (km)" and sport == "Lopen":
                km = st.number_input(label_km, 0.0, 200.0, default_km, 0.1,
                                     key=f"{prefix}_km")
                zone = _zone_selectbox("Intensiteitszone",
                                       f"{prefix}_zone", zone_idx)
                # Bereken minuten op basis van tempo uit zones
                tempo = zones_data.get(f"{zone[:2].lower()}_tempo")
                if tempo and tempo > 0 and km > 0:
                    minuten = round(km * tempo)
                    st.markdown(
                        f'<div style="font-size:0.7rem;color:#22c55e;margin-top:-8px;">'
                        f'≈ {int(minuten)}min op basis van gekalibreerd tempo</div>',
                        unsafe_allow_html=True)
                else:
                    minuten = round(km * 6) if km > 0 else 0
                return minuten, km, zone
            else:
                minuten = st.number_input(label_min, 0, 300, default_min,
                                          key=f"{prefix}_min")
                zone = _zone_selectbox("Intensiteitszone",
                                       f"{prefix}_zone", zone_idx)
                km_auto = 0.0
                if sport == "Lopen":
                    tempo = zones_data.get(f"{zone[:2].lower()}_tempo")
                    if tempo and tempo > 0 and minuten > 0:
                        km_auto = round(minuten / tempo, 2)
                        st.markdown(
                            f'<div style="font-size:0.7rem;color:#22c55e;margin-top:-8px;">'
                            f'≈ {km_auto} km op basis van gekalibreerd tempo</div>',
                            unsafe_allow_html=True)
                return minuten, km_auto, zone

        # ── Opwarming ─────────────────────────────────────────────────────────
        _sectie("OPWARMING", "#22c55e")
        ow1, ow2 = st.columns(2)
        with ow1:
            opw_min, opw_km, opw_zone = _invoer_blok(
                "tr_opw", "Duur (minuten)", "Afstand (km)", 10, 2.0, 0)
        with ow2:
            opw_kcal = _bereken_kcal(gewicht, opw_min, opw_zone) if opw_min > 0 else 0
            if opw_min > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                _metric_card("KCAL", str(opw_kcal), "kcal", "#22c55e")

        # ── Kern ──────────────────────────────────────────────────────────────
        _sectie("KERN", "#22c55e")

        kern_type = st.radio("Type kern",
            ["Doorlopend", "Intervalblokken", "Ramp up", "Ramp down"],
            horizontal=True, key="tr_kern_type")

        kern_min   = 0
        kern_km    = 0.0
        kern_zone  = ZONE_LABELS[1]
        kern_notitie = ""
        kern_zone2 = ZONE_LABELS[3]

        if kern_type == "Doorlopend":
            k1, k2 = st.columns(2)
            with k1:
                kern_min, kern_km, kern_zone = _invoer_blok(
                    "tr_kern", "Duur (minuten)", "Afstand (km)", 40, 8.0, 1)
            with k2:
                kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone) if kern_min > 0 else 0
                if kern_min > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    _metric_card("KCAL", str(kern_kcal), "kcal", "#22c55e")

        elif kern_type == "Intervalblokken":
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                int_herh   = st.number_input("Herhalingen", 1, 30, 5, key="tr_int_herh")
                int_werk   = st.number_input("Werkblok (min)", 1, 60, 4, key="tr_int_werk")
            with ic2:
                int_rust   = st.number_input("Rustblok (min)", 1, 30, 2, key="tr_int_rust")
                int_zone_w = _zone_selectbox("Zone werk", "tr_int_zone_w", 3)
            with ic3:
                int_zone_r = _zone_selectbox("Zone rust", "tr_int_zone_r", 0)
            kern_min  = int_herh * (int_werk + int_rust)
            kern_zone = int_zone_w
            kern_notitie = f"{int_herh}× {int_werk}min {int_zone_w[:2]} + {int_rust}min {int_zone_r[:2]}"
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#22c55e;">'
                f'📋 {kern_notitie} = {kern_min}min totaal</div>',
                unsafe_allow_html=True)

        elif kern_type == "Ramp up":
            ru1, ru2, ru3 = st.columns(3)
            with ru1:
                ramp_min  = st.number_input("Totale duur (min)", 5, 120, 20, key="tr_ramp_min")
            with ru2:
                ramp_van  = _zone_selectbox("Van zone", "tr_ramp_van", 1)
            with ru3:
                ramp_naar = _zone_selectbox("Naar zone", "tr_ramp_naar", 3)
            kern_min     = ramp_min
            kern_zone    = ramp_naar
            kern_notitie = f"Ramp up: {ramp_van[:2]} → {ramp_naar[:2]} over {ramp_min}min"
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#22c55e;">'
                f'📈 {kern_notitie}</div>', unsafe_allow_html=True)

        elif kern_type == "Ramp down":
            rd1, rd2, rd3 = st.columns(3)
            with rd1:
                ramp_min  = st.number_input("Totale duur (min)", 5, 120, 20, key="tr_rampd_min")
            with rd2:
                ramp_van  = _zone_selectbox("Van zone", "tr_rampd_van", 3)
            with rd3:
                ramp_naar = _zone_selectbox("Naar zone", "tr_rampd_naar", 1)
            kern_min     = ramp_min
            kern_zone    = ramp_van
            kern_notitie = f"Ramp down: {ramp_van[:2]} → {ramp_naar[:2]} over {ramp_min}min"
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#22c55e;">'
                f'📉 {kern_notitie}</div>', unsafe_allow_html=True)

        kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone) if kern_min > 0 else 0

        # ── Cooling down ──────────────────────────────────────────────────────
        _sectie("COOLING DOWN", "#22c55e")
        cd1, cd2 = st.columns(2)
        with cd1:
            cool_min, cool_km, cool_zone = _invoer_blok(
                "tr_cool", "Duur (minuten)", "Afstand (km)", 10, 2.0, 0)
        with cd2:
            cool_kcal = _bereken_kcal(gewicht, cool_min, cool_zone) if cool_min > 0 else 0
            if cool_min > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                _metric_card("KCAL", str(cool_kcal), "kcal", "#22c55e")

        # ── Optioneel ─────────────────────────────────────────────────────────
        _sectie("OPTIONEEL", "#86efac")
        o1, o2, o3 = st.columns(3)
        with o1:
            hartslag_gem = st.number_input("Hartslag gem (bpm)", 0, 220, 0, key="tr_hs_gem")
        with o2:
            if sport != "Lopen" or invoer_modus == "Tijd (minuten)":
                afstand_km = st.number_input("Afstand (km)", 0.0, 300.0, 0.0, 0.1, key="tr_afstand")
            else:
                afstand_km = round(opw_km + kern_km + cool_km, 2)
                st.markdown(
                    f'<div style="font-size:0.8rem;color:#22c55e;font-weight:700;'
                    f'padding-top:28px;">Totaal: {afstand_km} km</div>',
                    unsafe_allow_html=True)
        with o3:
            notitie_extra = st.text_input("Notitie", placeholder="bijv. Goed gevoel", key="tr_notitie")

        # ── Totalen ───────────────────────────────────────────────────────────
        totaal_min  = opw_min + kern_min + cool_min
        totaal_kcal = opw_kcal + kern_kcal + cool_kcal
        blokken     = [(opw_zone, opw_min), (kern_zone, kern_min), (cool_zone, cool_min)]
        dom_zone    = _dominante_zone(blokken) if totaal_min > 0 else "—"

        if totaal_min > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("SAMENVATTING", "#22c55e")
            m1, m2, m3 = st.columns(3)
            with m1:
                _metric_card("TOTALE DUUR",
                    f"{totaal_min // 60}u{totaal_min % 60:02d}", "min", "#22c55e")
            with m2:
                _metric_card("KCAL VERBRANDING", str(totaal_kcal), "kcal", "#4ade80")
            with m3:
                _metric_card("DOMINANTE ZONE", dom_zone[:2], dom_zone[4:], "#16a34a")

        # ── Opslaan ───────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if totaal_min > 0:
            if st.button("💾 Training opslaan", key="tr_opslaan", use_container_width=True):
                zone_verdeling = {}
                for z, m in blokken:
                    key = z[:2].lower()
                    zone_verdeling[key] = zone_verdeling.get(key, 0) + m

                notitie_vol = (
                    f"{omschrijving + ' | ' if omschrijving else ''}"
                    f"OPW: {opw_min}min {opw_zone[:2]} | "
                    f"KERN: {kern_min}min {kern_zone[:2]}"
                    f"{' | ' + kern_notitie if kern_notitie else ''} | "
                    f"COOL: {cool_min}min {cool_zone[:2]}"
                    f"{' | HS: ' + str(hartslag_gem) + 'bpm' if hartslag_gem > 0 else ''}"
                    f"{' | ' + str(round(afstand_km, 2)) + 'km' if afstand_km > 0 else ''}"
                    f"{' | ' + notitie_extra if notitie_extra else ''}"
                ).strip(" | ")

                training_data = {
                    "datum":             str(datum),
                    "sport":             sport,
                    "duur_min":          totaal_min,
                    "afstand_km":        round(afstand_km, 2) if afstand_km > 0 else None,
                    "hartslag_gem":      hartslag_gem if hartslag_gem > 0 else None,
                    "kcal_verbranding":  totaal_kcal,
                    "zone_verdeling":    zone_verdeling,
                    "notitie":           notitie_vol,
                }
                if _sla_training_op(user_id, training_data):
                    st.success("✅ Training opgeslagen!")
                    for k in ["tr_opw_min","tr_kern_min","tr_cool_min","tr_naam",
                              "tr_notitie","tr_afstand","tr_hs_gem","tr_interval_aan",
                              "tr_opw_km","tr_kern_km","tr_cool_km"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            st.button("💾 Training opslaan", key="tr_opslaan",
                      use_container_width=True, disabled=True)
            st.caption("Vul minstens één blok in om op te slaan.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ZONE KALIBRATIE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_zones:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZONE KALIBRATIE PER SPORT", "#22c55e")
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:16px;">'
            'Koppel je intensiteitszones aan tempo of hartslag. '
            'Dit wordt gebruikt voor automatische berekeningen bij het invoeren van trainingen.</div>',
            unsafe_allow_html=True)

        kal_sport = st.selectbox("Sport", SPORT_OPTIES, key="kal_sport")
        kal_zones = _laad_zones(user_id, kal_sport)

        if kal_sport == "Lopen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/km)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Fietsen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Watt", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        else:
            kal_eenheid = "Hartslag (bpm)"
            st.markdown(
                '<div style="font-size:0.8rem;color:#64748b;">Koppeling via hartslag.</div>',
                unsafe_allow_html=True)

        toon_tempo = kal_eenheid in ["Tempo (min/km)", "Watt", "Beide"]
        toon_hs    = kal_eenheid in ["Hartslag (bpm)", "Beide"]

        st.markdown("<br>", unsafe_allow_html=True)
        tempo_label = "Tempo (min/km)" if kal_sport == "Lopen" else "Watt"

        nieuwe_zones = {"eenheid": "tempo" if "Tempo" in kal_eenheid or "Watt" in kal_eenheid
                        else "hartslag"}

        for i, z in enumerate(ZONE_LABELS):
            z_key = z[:2].lower()
            st.markdown(
                f'<div style="font-size:0.75rem;font-weight:700;color:#22c55e;'
                f'margin:12px 0 4px;">{z}</div>',
                unsafe_allow_html=True)
            cols = st.columns(2 if (toon_tempo and toon_hs) else 1)
            if toon_tempo:
                with cols[0]:
                    if kal_sport == "Lopen":
                        # Tempo als min/km — invoer als decimaal (bijv. 5.30 = 5min30sec)
                        huidig = float(kal_zones.get(f"{z_key}_tempo") or 0)
                        val = st.number_input(
                            tempo_label, 0.0, 20.0, huidig, 0.05,
                            key=f"kal_{z_key}_tempo",
                            help="Voer in als min.sec (bijv. 5.30 = 5min30sec)")
                    else:
                        huidig = float(kal_zones.get(f"{z_key}_tempo") or 0)
                        val = st.number_input(
                            tempo_label, 0, 600, int(huidig), 5,
                            key=f"kal_{z_key}_tempo")
                    nieuwe_zones[f"{z_key}_tempo"] = val if val > 0 else None
            if toon_hs:
                with cols[-1]:
                    huidig_hs = int(kal_zones.get(f"{z_key}_hs") or 0)
                    hs_val = st.number_input(
                        "Hartslag (bpm)", 0, 220, huidig_hs, 1,
                        key=f"kal_{z_key}_hs")
                    nieuwe_zones[f"{z_key}_hs"] = hs_val if hs_val > 0 else None

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Zones opslaan", key="kal_opslaan", use_container_width=True):
            if _sla_zones_op(user_id, kal_sport, nieuwe_zones):
                st.success(f"✅ Zones opgeslagen voor {kal_sport}!")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — MIJN TRAININGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        trainingen = _laad_trainingen(user_id)

        if not trainingen:
            st.markdown(
                '<div style="text-align:center;color:#64748b;padding:30px;">'
                'Nog geen trainingen toegevoegd.</div>',
                unsafe_allow_html=True)
        else:
            from datetime import date, timedelta
            vandaag    = date.today()
            week_start = vandaag - timedelta(days=vandaag.weekday())
            week_kcal  = sum(
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

            SPORT_EMOJI = {"Lopen":"🏃","Fietsen":"🚴","Zwemmen":"🏊",
                           "Kracht":"💪","Andere":"⚡"}
            ZONE_KLEUR  = {"z1":"#64748b","z2":"#22c55e","z3":"#fbbf24",
                           "z4":"#f97316","z5":"#ef4444"}

            for t in trainingen:
                sport_em  = SPORT_EMOJI.get(t.get("sport",""), "⚡")
                datum_str = t.get("datum","")[:10]
                duur_min  = t.get("duur_min", 0) or 0
                duur_str  = f"{duur_min // 60}u{duur_min % 60:02d}"
                kcal      = t.get("kcal_verbranding", 0) or 0
                notitie   = t.get("notitie", "") or ""
                notitie_kort = notitie[:70] + "..." if len(notitie) > 70 else notitie

                zv = t.get("zone_verdeling") or {}
                if isinstance(zv, str):
                    import json
                    try: zv = json.loads(zv)
                    except: zv = {}
                totaal_zv = sum(zv.values()) if zv else max(duur_min, 1)
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
                        f'<div style="display:flex;gap:8px;margin-bottom:6px;">'
                        + "".join([
                            f'<span style="font-size:0.65rem;font-weight:700;padding:2px 6px;'
                            f'border-radius:4px;background:{kleur}22;color:{kleur};">'
                            f'{z.upper()}: {zv.get(z,0)}min</span>'
                            for z, kleur in ZONE_KLEUR.items() if zv.get(z, 0) > 0
                        ])
                        + f'</div>'
                        f'<div style="font-size:0.72rem;color:#64748b;">'
                        f'{str(t.get("afstand_km","")) + "km · " if t.get("afstand_km") else ""}'
                        f'{str(t.get("hartslag_gem","")) + " bpm" if t.get("hartslag_gem") else ""}'
                        f'</div>',
                        unsafe_allow_html=True)
                    if st.button("🗑 Verwijderen", key=f"tr_del_{t['id']}"):
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
