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

def _format_tempo(val: float) -> str:
    """Zet decimaal tempo om naar min:sec formaat."""
    if not val: return ""
    minuten = int(val)
    seconden = round((val - minuten) * 60)
    return f"{minuten}:{seconden:02d}"

def _zone_info(zones: dict, zone_label: str, eenheid: str, sport: str) -> str:
    """Geef tempo/hs bereik info voor een zone."""
    z_key = zone_label[:2].lower()
    if eenheid == "tempo" and sport == "Lopen":
        van = zones.get(f"{z_key}_tempo_van")
        tot = zones.get(f"{z_key}_tempo_tot")
        if van and tot:
            return f"{_format_tempo(van)} — {_format_tempo(tot)} min/km"
        elif van:
            return f"vanaf {_format_tempo(van)} min/km"
    elif eenheid == "watt":
        van = zones.get(f"{z_key}_tempo_van")
        tot = zones.get(f"{z_key}_tempo_tot")
        if van and tot: return f"{int(van)}—{int(tot)}W"
        elif van: return f"vanaf {int(van)}W"
    if eenheid in ("hartslag", None, ""):
        van = zones.get(f"{z_key}_hs_van")
        tot = zones.get(f"{z_key}_hs_tot")
        if van and tot: return f"{int(van)}—{int(tot)} bpm"
        elif van: return f"vanaf {int(van)} bpm"
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

        def _km_of_min_invoer(prefix, label_min, label_km, default_min, default_km, zone_idx, help_min="", help_km=""):
            """Invoer in km of minuten afhankelijk van modus, geeft (minuten, km, zone) terug."""
            if invoer_modus == "Afstand (km)" and sport == "Lopen":
                km = st.number_input(label_km, 0.0, 200.0, default_km, 0.1,
                                     key=f"{prefix}_km", help=help_km)
                zone = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                tempo = zones_data.get(f"{zone[:2].lower()}_tempo_van") or zones_data.get(f"{zone[:2].lower()}_tempo_tot")
                if tempo and tempo > 0 and km > 0:
                    minuten = round(km * tempo)
                    st.markdown(
                        f'<div style="font-size:0.7rem;color:#22c55e;margin-top:-8px;">'
                        f'≈ {minuten}min op basis van gekalibreerd tempo</div>',
                        unsafe_allow_html=True)
                else:
                    minuten = round(km * 6) if km > 0 else 0
                return minuten, km, zone
            else:
                minuten = st.number_input(label_min, 0, 300, default_min,
                                          key=f"{prefix}_min", help=help_min)
                zone = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                km_auto = 0.0
                if sport == "Lopen":
                    tempo = zones_data.get(f"{zone[:2].lower()}_tempo_van") or zones_data.get(f"{zone[:2].lower()}_tempo_tot")
                    if tempo and tempo > 0 and minuten > 0:
                        km_auto = round(minuten / tempo, 2)
                        st.markdown(
                            f'<div style="font-size:0.7rem;color:#22c55e;margin-top:-8px;">'
                            f'≈ {km_auto} km op basis van gekalibreerd tempo</div>',
                            unsafe_allow_html=True)
                return minuten, km_auto, zone

        if kern_type == "Doorlopend":
            k1, k2 = st.columns(2)
            with k1:
                kern_min, kern_km, kern_zone = _km_of_min_invoer(
                    "tr_kern", "Duur (minuten)", "Afstand (km)", 40, 8.0, 1)
            with k2:
                kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone) if kern_min > 0 else 0
                if kern_min > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    _metric_card("KCAL", str(kern_kcal), "kcal", "#22c55e")

        elif kern_type == "Intervalblokken":
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                int_herh = st.number_input("Herhalingen", 1, 30, 5, key="tr_int_herh")
                int_zone_w = _zone_selectbox("Zone werk", "tr_int_zone_w", 3)
            with ic2:
                int_zone_r = _zone_selectbox("Zone rust", "tr_int_zone_r", 0)
                if invoer_modus == "Afstand (km)" and sport == "Lopen":
                    int_werk_km = st.number_input("Werkblok (km)", 0.1, 20.0, 1.0, 0.1, key="tr_int_werk_km")
                    int_rust_km = st.number_input("Rustblok (km)", 0.1, 10.0, 0.4, 0.1, key="tr_int_rust_km")
                    tempo_w = zones_data.get(f"{int_zone_w[:2].lower()}_tempo_van") or zones_data.get(f"{int_zone_w[:2].lower()}_tempo_tot") or 5.0
                    tempo_r = zones_data.get(f"{int_zone_r[:2].lower()}_tempo_van") or zones_data.get(f"{int_zone_r[:2].lower()}_tempo_tot") or 6.5
                    int_werk = round(int_werk_km * tempo_w)
                    int_rust  = round(int_rust_km * tempo_r)
                    kern_km   = int_herh * (int_werk_km + int_rust_km)
                else:
                    int_werk_km = 0.0
                    int_rust_km = 0.0
                    kern_km     = 0.0
            with ic3:
                if invoer_modus == "Tijd (minuten)" or sport != "Lopen":
                    int_werk = st.number_input("Werkblok (min)", 1, 60, 4, key="tr_int_werk")
                    int_rust = st.number_input("Rustblok (min)", 1, 30, 2, key="tr_int_rust")

            kern_min  = int_herh * (int_werk + int_rust)
            kern_zone = int_zone_w
            if invoer_modus == "Afstand (km)" and sport == "Lopen":
                kern_notitie = f"{int_herh}× {int_werk_km}km {int_zone_w[:2]} + {int_rust_km}km {int_zone_r[:2]}"
            else:
                kern_notitie = f"{int_herh}× {int_werk}min {int_zone_w[:2]} + {int_rust}min {int_zone_r[:2]}"
            st.markdown(
                f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                f'border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#22c55e;">'
                f'📋 {kern_notitie} = {kern_min}min totaal</div>',
                unsafe_allow_html=True)

        elif kern_type == "Ramp up":
            ru1, ru2, ru3 = st.columns(3)
            with ru1:
                if invoer_modus == "Afstand (km)" and sport == "Lopen":
                    ramp_km  = st.number_input("Afstand (km)", 0.1, 50.0, 5.0, 0.1, key="tr_ramp_km")
                    ramp_min = round(ramp_km * 5.5)
                    kern_km  = ramp_km
                else:
                    ramp_min = st.number_input("Totale duur (min)", 5, 120, 20, key="tr_ramp_min")
                    kern_km  = 0.0
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
                if invoer_modus == "Afstand (km)" and sport == "Lopen":
                    ramp_km  = st.number_input("Afstand (km)", 0.1, 50.0, 5.0, 0.1, key="tr_rampd_km")
                    ramp_min = round(ramp_km * 5.5)
                    kern_km  = ramp_km
                else:
                    ramp_min = st.number_input("Totale duur (min)", 5, 120, 20, key="tr_rampd_min")
                    kern_km  = 0.0
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

        st.markdown(
            '<div style="font-size:0.75rem;color:#64748b;margin-bottom:12px;">' +
            ('Tempo: voer in als min.sec — bijv. 5.30 = 5min30sec/km' if toon_tempo and kal_sport == "Lopen" else '') +
            '</div>', unsafe_allow_html=True)

        for i, z in enumerate(ZONE_LABELS):
            z_key = z[:2].lower()
            st.markdown(
                f'<div style="font-size:0.75rem;font-weight:700;color:#22c55e;'
                f'margin:14px 0 4px;padding:4px 8px;background:#0f172a;border-left:3px solid #22c55e;border-radius:0 4px 4px 0;">{z}</div>',
                unsafe_allow_html=True)

            if toon_tempo:
                t1, t2 = st.columns(2)
                with t1:
                    if kal_sport == "Lopen":
                        huidig_van = float(kal_zones.get(f"{z_key}_tempo_van") or 0)
                        val_van = st.number_input(
                            f"{tempo_label} — van (langzamer)",
                            0.0, 20.0, huidig_van, 0.05,
                            key=f"kal_{z_key}_tempo_van",
                            help="bijv. 5.30 = 5min30sec/km")
                    else:
                        huidig_van = float(kal_zones.get(f"{z_key}_tempo_van") or 0)
                        val_van = st.number_input(
                            f"{tempo_label} — van", 0, 600, int(huidig_van), 5,
                            key=f"kal_{z_key}_tempo_van")
                    nieuwe_zones[f"{z_key}_tempo_van"] = val_van if val_van > 0 else None
                with t2:
                    if kal_sport == "Lopen":
                        huidig_tot = float(kal_zones.get(f"{z_key}_tempo_tot") or 0)
                        val_tot = st.number_input(
                            f"{tempo_label} — tot (sneller)",
                            0.0, 20.0, huidig_tot, 0.05,
                            key=f"kal_{z_key}_tempo_tot",
                            help="bijv. 5.00 = 5min00sec/km")
                    else:
                        huidig_tot = float(kal_zones.get(f"{z_key}_tempo_tot") or 0)
                        val_tot = st.number_input(
                            f"{tempo_label} — tot", 0, 600, int(huidig_tot), 5,
                            key=f"kal_{z_key}_tempo_tot")
                    nieuwe_zones[f"{z_key}_tempo_tot"] = val_tot if val_tot > 0 else None

                # Preview
                if val_van and val_tot:
                    if kal_sport == "Lopen":
                        preview = f"{_format_tempo(val_van)} — {_format_tempo(val_tot)} min/km"
                    else:
                        preview = f"{int(val_van)}—{int(val_tot)}W"
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {preview}</div>', unsafe_allow_html=True)

            if toon_hs:
                h1, h2 = st.columns(2)
                with h1:
                    huidig_hs_van = int(kal_zones.get(f"{z_key}_hs_van") or 0)
                    hs_van = st.number_input(
                        "Hartslag — van (bpm)", 0, 220, huidig_hs_van, 1,
                        key=f"kal_{z_key}_hs_van")
                    nieuwe_zones[f"{z_key}_hs_van"] = hs_van if hs_van > 0 else None
                with h2:
                    huidig_hs_tot = int(kal_zones.get(f"{z_key}_hs_tot") or 0)
                    hs_tot = st.number_input(
                        "Hartslag — tot (bpm)", 0, 220, huidig_hs_tot, 1,
                        key=f"kal_{z_key}_hs_tot")
                    nieuwe_zones[f"{z_key}_hs_tot"] = hs_tot if hs_tot > 0 else None

                if hs_van and hs_tot:
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {int(hs_van)}—{int(hs_tot)} bpm</div>', unsafe_allow_html=True)

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


# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 3 — VOEDSELBIBLIOTHEEK (MANUEEL)
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORIE_OPTIES = [
    "Granen & brood", "Zuivel", "Vlees & vis", "Groenten", "Fruit",
    "Sportvoeding", "Dranken", "Sauzen & spreads", "Snacks", "Overige"
]

VOEDSEL_DB = [
    {"naam":'Wit brood',"cat":'Granen & brood',"kcal":265,"kh":49,"suikers":4,"eiwit":8,"vet":3,"verz":0.6,"vezels":2,"natrium":500,"portie":35},
    {"naam":'Bruin brood',"cat":'Granen & brood',"kcal":245,"kh":44,"suikers":4,"eiwit":9,"vet":3,"verz":0.5,"vezels":5,"natrium":480,"portie":35},
    {"naam":'Volkorenbrood',"cat":'Granen & brood',"kcal":240,"kh":41,"suikers":3,"eiwit":9,"vet":3,"verz":0.5,"vezels":7,"natrium":400,"portie":35},
    {"naam":'Stokbrood',"cat":'Granen & brood',"kcal":270,"kh":55,"suikers":2,"eiwit":9,"vet":1,"verz":0.2,"vezels":2,"natrium":550,"portie":50},
    {"naam":'Havermout',"cat":'Granen & brood',"kcal":370,"kh":60,"suikers":1,"eiwit":13,"vet":7,"verz":1.2,"vezels":10,"natrium":5,"portie":45},
    {"naam":'Cornflakes',"cat":'Granen & brood',"kcal":375,"kh":84,"suikers":7,"eiwit":7,"vet":1,"verz":0.1,"vezels":3,"natrium":660,"portie":30},
    {"naam":'Muesli',"cat":'Granen & brood',"kcal":360,"kh":65,"suikers":20,"eiwit":9,"vet":7,"verz":1.0,"vezels":8,"natrium":30,"portie":50},
    {"naam":'Granola',"cat":'Granen & brood',"kcal":440,"kh":64,"suikers":22,"eiwit":9,"vet":17,"verz":2.0,"vezels":6,"natrium":80,"portie":45},
    {"naam":'Rijst wit gekookt',"cat":'Granen & brood',"kcal":130,"kh":28,"suikers":0,"eiwit":3,"vet":0,"verz":0.0,"vezels":0,"natrium":0,"portie":180},
    {"naam":'Rijst volkoren gekookt',"cat":'Granen & brood',"kcal":110,"kh":23,"suikers":0,"eiwit":3,"vet":1,"verz":0.1,"vezels":2,"natrium":0,"portie":180},
    {"naam":'Pasta wit gekookt',"cat":'Granen & brood',"kcal":158,"kh":31,"suikers":1,"eiwit":6,"vet":1,"verz":0.1,"vezels":2,"natrium":0,"portie":180},
    {"naam":'Pasta volkoren gekookt',"cat":'Granen & brood',"kcal":150,"kh":28,"suikers":1,"eiwit":6,"vet":1,"verz":0.1,"vezels":4,"natrium":0,"portie":180},
    {"naam":'Quinoa gekookt',"cat":'Granen & brood',"kcal":120,"kh":21,"suikers":1,"eiwit":4,"vet":2,"verz":0.2,"vezels":3,"natrium":5,"portie":185},
    {"naam":'Couscous gekookt',"cat":'Granen & brood',"kcal":112,"kh":23,"suikers":0,"eiwit":4,"vet":0,"verz":0.0,"vezels":1,"natrium":5,"portie":180},
    {"naam":'Aardappel gekookt',"cat":'Granen & brood',"kcal":87,"kh":20,"suikers":1,"eiwit":2,"vet":0,"verz":0.0,"vezels":2,"natrium":5,"portie":175},
    {"naam":'Zoete aardappel gekookt',"cat":'Granen & brood',"kcal":90,"kh":21,"suikers":4,"eiwit":2,"vet":0,"verz":0.0,"vezels":3,"natrium":36,"portie":175},
    {"naam":'Rijstwafel naturel',"cat":'Granen & brood',"kcal":385,"kh":81,"suikers":1,"eiwit":8,"vet":3,"verz":0.5,"vezels":2,"natrium":10,"portie":9},
    {"naam":'Cracker volkoren',"cat":'Granen & brood',"kcal":410,"kh":70,"suikers":2,"eiwit":10,"vet":10,"verz":2.0,"vezels":8,"natrium":600,"portie":10},
    {"naam":'Roggebrood',"cat":'Granen & brood',"kcal":259,"kh":49,"suikers":2,"eiwit":9,"vet":2,"verz":0.2,"vezels":6,"natrium":450,"portie":40},
    {"naam":'Wrap',"cat":'Granen & brood',"kcal":290,"kh":50,"suikers":3,"eiwit":8,"vet":6,"verz":2.0,"vezels":3,"natrium":600,"portie":60},
    {"naam":'Pannenkoek',"cat":'Granen & brood',"kcal":230,"kh":35,"suikers":8,"eiwit":6,"vet":8,"verz":2.0,"vezels":1,"natrium":220,"portie":80},
    {"naam":'Croissant',"cat":'Granen & brood',"kcal":406,"kh":46,"suikers":10,"eiwit":8,"vet":21,"verz":12.0,"vezels":2,"natrium":400,"portie":60},
    {"naam":'Maïstortilla',"cat":'Granen & brood',"kcal":218,"kh":46,"suikers":1,"eiwit":5,"vet":3,"verz":0.3,"vezels":4,"natrium":400,"portie":45},
    {"naam":'Bulgur gekookt',"cat":'Granen & brood',"kcal":83,"kh":19,"suikers":0,"eiwit":3,"vet":0,"verz":0.0,"vezels":5,"natrium":5,"portie":180},
    {"naam":'Polenta',"cat":'Granen & brood',"kcal":372,"kh":78,"suikers":1,"eiwit":9,"vet":4,"verz":0.5,"vezels":7,"natrium":10,"portie":50},
    {"naam":'Volle melk',"cat":'Zuivel',"kcal":64,"kh":5,"suikers":5,"eiwit":3,"vet":4,"verz":2.4,"vezels":0,"natrium":43,"portie":200},
    {"naam":'Halfvolle melk',"cat":'Zuivel',"kcal":46,"kh":5,"suikers":5,"eiwit":3,"vet":2,"verz":1.1,"vezels":0,"natrium":43,"portie":200},
    {"naam":'Magere melk',"cat":'Zuivel',"kcal":34,"kh":5,"suikers":5,"eiwit":3,"vet":0,"verz":0.0,"vezels":0,"natrium":43,"portie":200},
    {"naam":'Sojadrank',"cat":'Zuivel',"kcal":40,"kh":3,"suikers":2,"eiwit":3,"vet":2,"verz":0.3,"vezels":0,"natrium":50,"portie":200},
    {"naam":'Haverdrank',"cat":'Zuivel',"kcal":45,"kh":7,"suikers":4,"eiwit":1,"vet":1,"verz":0.2,"vezels":1,"natrium":60,"portie":200},
    {"naam":'Amandelmelk',"cat":'Zuivel',"kcal":24,"kh":3,"suikers":2,"eiwit":1,"vet":1,"verz":0.1,"vezels":0,"natrium":70,"portie":200},
    {"naam":'Griekse yoghurt vol',"cat":'Zuivel',"kcal":130,"kh":4,"suikers":4,"eiwit":9,"vet":8,"verz":5.0,"vezels":0,"natrium":40,"portie":150},
    {"naam":'Yoghurt natuur mager',"cat":'Zuivel',"kcal":55,"kh":7,"suikers":7,"eiwit":5,"vet":1,"verz":0.5,"vezels":0,"natrium":65,"portie":125},
    {"naam":'Kwark mager',"cat":'Zuivel',"kcal":57,"kh":4,"suikers":4,"eiwit":9,"vet":0,"verz":0.0,"vezels":0,"natrium":40,"portie":100},
    {"naam":'Plattekaas',"cat":'Zuivel',"kcal":72,"kh":3,"suikers":3,"eiwit":8,"vet":3,"verz":2.0,"vezels":0,"natrium":55,"portie":100},
    {"naam":'Edammer 30+',"cat":'Zuivel',"kcal":270,"kh":0,"suikers":0,"eiwit":27,"vet":18,"verz":11.0,"vezels":0,"natrium":800,"portie":30},
    {"naam":'Gouda 48+',"cat":'Zuivel',"kcal":356,"kh":0,"suikers":0,"eiwit":25,"vet":28,"verz":18.0,"vezels":0,"natrium":820,"portie":30},
    {"naam":'Mozzarella',"cat":'Zuivel',"kcal":280,"kh":2,"suikers":1,"eiwit":19,"vet":22,"verz":13.0,"vezels":0,"natrium":600,"portie":50},
    {"naam":'Feta',"cat":'Zuivel',"kcal":264,"kh":4,"suikers":0,"eiwit":14,"vet":21,"verz":15.0,"vezels":0,"natrium":1120,"portie":30},
    {"naam":'Skyr',"cat":'Zuivel',"kcal":63,"kh":4,"suikers":4,"eiwit":11,"vet":0,"verz":0.0,"vezels":0,"natrium":50,"portie":150},
    {"naam":'Boter',"cat":'Zuivel',"kcal":717,"kh":1,"suikers":0,"eiwit":1,"vet":81,"verz":51.0,"vezels":0,"natrium":700,"portie":10},
    {"naam":'Margarine',"cat":'Zuivel',"kcal":520,"kh":1,"suikers":0,"eiwit":0,"vet":58,"verz":15.0,"vezels":0,"natrium":600,"portie":10},
    {"naam":'Kipfilet',"cat":'Vlees & vis',"kcal":165,"kh":0,"suikers":0,"eiwit":31,"vet":4,"verz":1.0,"vezels":0,"natrium":74,"portie":120},
    {"naam":'Kalkoenfilet',"cat":'Vlees & vis',"kcal":157,"kh":0,"suikers":0,"eiwit":30,"vet":3,"verz":0.9,"vezels":0,"natrium":70,"portie":120},
    {"naam":'Rundergehakt mager',"cat":'Vlees & vis',"kcal":200,"kh":0,"suikers":0,"eiwit":20,"vet":13,"verz":5.0,"vezels":0,"natrium":75,"portie":120},
    {"naam":'Biefstuk',"cat":'Vlees & vis',"kcal":217,"kh":0,"suikers":0,"eiwit":26,"vet":12,"verz":4.0,"vezels":0,"natrium":66,"portie":150},
    {"naam":'Varkenshaas',"cat":'Vlees & vis',"kcal":143,"kh":0,"suikers":0,"eiwit":22,"vet":6,"verz":2.0,"vezels":0,"natrium":63,"portie":120},
    {"naam":'Zalm',"cat":'Vlees & vis',"kcal":208,"kh":0,"suikers":0,"eiwit":20,"vet":13,"verz":3.0,"vezels":0,"natrium":59,"portie":150},
    {"naam":'Tonijn in water',"cat":'Vlees & vis',"kcal":108,"kh":0,"suikers":0,"eiwit":25,"vet":1,"verz":0.2,"vezels":0,"natrium":320,"portie":100},
    {"naam":'Kabeljauw',"cat":'Vlees & vis',"kcal":82,"kh":0,"suikers":0,"eiwit":18,"vet":1,"verz":0.1,"vezels":0,"natrium":54,"portie":150},
    {"naam":'Garnalen',"cat":'Vlees & vis',"kcal":99,"kh":0,"suikers":0,"eiwit":21,"vet":1,"verz":0.3,"vezels":0,"natrium":111,"portie":100},
    {"naam":'Makreel',"cat":'Vlees & vis',"kcal":205,"kh":0,"suikers":0,"eiwit":19,"vet":14,"verz":3.0,"vezels":0,"natrium":90,"portie":120},
    {"naam":'Haring',"cat":'Vlees & vis',"kcal":217,"kh":0,"suikers":0,"eiwit":18,"vet":15,"verz":3.0,"vezels":0,"natrium":100,"portie":100},
    {"naam":'Ei groot',"cat":'Vlees & vis',"kcal":155,"kh":1,"suikers":1,"eiwit":13,"vet":11,"verz":3.0,"vezels":0,"natrium":124,"portie":60},
    {"naam":'Kippenham',"cat":'Vlees & vis',"kcal":105,"kh":2,"suikers":1,"eiwit":18,"vet":3,"verz":1.0,"vezels":0,"natrium":900,"portie":30},
    {"naam":'Spek',"cat":'Vlees & vis',"kcal":541,"kh":0,"suikers":0,"eiwit":37,"vet":42,"verz":14.0,"vezels":0,"natrium":1717,"portie":30},
    {"naam":'Sardines in olie',"cat":'Vlees & vis',"kcal":208,"kh":0,"suikers":0,"eiwit":25,"vet":11,"verz":1.5,"vezels":0,"natrium":505,"portie":100},
    {"naam":'Broccoli',"cat":'Groenten',"kcal":34,"kh":7,"suikers":2,"eiwit":3,"vet":0,"verz":0.0,"vezels":3,"natrium":33,"portie":150},
    {"naam":'Spinazie',"cat":'Groenten',"kcal":23,"kh":4,"suikers":0,"eiwit":3,"vet":0,"verz":0.0,"vezels":2,"natrium":79,"portie":100},
    {"naam":'Wortel',"cat":'Groenten',"kcal":41,"kh":10,"suikers":5,"eiwit":1,"vet":0,"verz":0.0,"vezels":3,"natrium":69,"portie":100},
    {"naam":'Tomaat',"cat":'Groenten',"kcal":18,"kh":4,"suikers":3,"eiwit":1,"vet":0,"verz":0.0,"vezels":1,"natrium":5,"portie":100},
    {"naam":'Komkommer',"cat":'Groenten',"kcal":15,"kh":3,"suikers":2,"eiwit":1,"vet":0,"verz":0.0,"vezels":1,"natrium":2,"portie":100},
    {"naam":'Paprika rood',"cat":'Groenten',"kcal":31,"kh":7,"suikers":5,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":4,"portie":100},
    {"naam":'Courgette',"cat":'Groenten',"kcal":17,"kh":3,"suikers":2,"eiwit":1,"vet":0,"verz":0.0,"vezels":1,"natrium":8,"portie":150},
    {"naam":'Aubergine',"cat":'Groenten',"kcal":25,"kh":6,"suikers":4,"eiwit":1,"vet":0,"verz":0.0,"vezels":3,"natrium":2,"portie":150},
    {"naam":'Bloemkool',"cat":'Groenten',"kcal":25,"kh":5,"suikers":2,"eiwit":2,"vet":0,"verz":0.0,"vezels":2,"natrium":30,"portie":150},
    {"naam":'Sla gemengd',"cat":'Groenten',"kcal":15,"kh":3,"suikers":2,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":10,"portie":80},
    {"naam":'Ui',"cat":'Groenten',"kcal":40,"kh":9,"suikers":4,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":4,"portie":80},
    {"naam":'Champignon',"cat":'Groenten',"kcal":22,"kh":3,"suikers":2,"eiwit":3,"vet":0,"verz":0.0,"vezels":1,"natrium":5,"portie":100},
    {"naam":'Erwten',"cat":'Groenten',"kcal":81,"kh":14,"suikers":6,"eiwit":5,"vet":0,"verz":0.0,"vezels":5,"natrium":5,"portie":100},
    {"naam":'Witte bonen',"cat":'Groenten',"kcal":127,"kh":23,"suikers":1,"eiwit":8,"vet":1,"verz":0.0,"vezels":7,"natrium":290,"portie":120},
    {"naam":'Linzen gekookt',"cat":'Groenten',"kcal":116,"kh":20,"suikers":2,"eiwit":9,"vet":0,"verz":0.0,"vezels":8,"natrium":238,"portie":150},
    {"naam":'Kikkererwten',"cat":'Groenten',"kcal":164,"kh":27,"suikers":5,"eiwit":9,"vet":3,"verz":0.3,"vezels":8,"natrium":24,"portie":120},
    {"naam":'Zoete mais',"cat":'Groenten',"kcal":86,"kh":19,"suikers":3,"eiwit":3,"vet":1,"verz":0.2,"vezels":2,"natrium":15,"portie":100},
    {"naam":'Avocado',"cat":'Groenten',"kcal":160,"kh":9,"suikers":1,"eiwit":2,"vet":15,"verz":2.0,"vezels":7,"natrium":7,"portie":100},
    {"naam":'Edamame',"cat":'Groenten',"kcal":121,"kh":9,"suikers":3,"eiwit":11,"vet":5,"verz":0.7,"vezels":5,"natrium":2,"portie":100},
    {"naam":'Knoflook',"cat":'Groenten',"kcal":149,"kh":33,"suikers":1,"eiwit":6,"vet":1,"verz":0.0,"vezels":2,"natrium":17,"portie":5},
    {"naam":'Banaan',"cat":'Fruit',"kcal":89,"kh":23,"suikers":12,"eiwit":1,"vet":0,"verz":0.0,"vezels":3,"natrium":1,"portie":120},
    {"naam":'Appel',"cat":'Fruit',"kcal":52,"kh":14,"suikers":10,"eiwit":0,"vet":0,"verz":0.0,"vezels":2,"natrium":1,"portie":150},
    {"naam":'Peer',"cat":'Fruit',"kcal":57,"kh":15,"suikers":10,"eiwit":0,"vet":0,"verz":0.0,"vezels":3,"natrium":1,"portie":150},
    {"naam":'Sinaasappel',"cat":'Fruit',"kcal":47,"kh":12,"suikers":9,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":0,"portie":150},
    {"naam":'Mandarijn',"cat":'Fruit',"kcal":53,"kh":13,"suikers":11,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":2,"portie":100},
    {"naam":'Aardbei',"cat":'Fruit',"kcal":32,"kh":8,"suikers":5,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":1,"portie":150},
    {"naam":'Bosbes',"cat":'Fruit',"kcal":57,"kh":14,"suikers":10,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":1,"portie":100},
    {"naam":'Druiven',"cat":'Fruit',"kcal":67,"kh":17,"suikers":16,"eiwit":1,"vet":0,"verz":0.0,"vezels":1,"natrium":1,"portie":150},
    {"naam":'Kiwi',"cat":'Fruit',"kcal":61,"kh":15,"suikers":9,"eiwit":1,"vet":1,"verz":0.0,"vezels":3,"natrium":3,"portie":100},
    {"naam":'Mango',"cat":'Fruit',"kcal":60,"kh":15,"suikers":14,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":1,"portie":150},
    {"naam":'Ananas',"cat":'Fruit',"kcal":50,"kh":13,"suikers":10,"eiwit":1,"vet":0,"verz":0.0,"vezels":1,"natrium":1,"portie":150},
    {"naam":'Watermeloen',"cat":'Fruit',"kcal":30,"kh":8,"suikers":6,"eiwit":1,"vet":0,"verz":0.0,"vezels":0,"natrium":1,"portie":200},
    {"naam":'Dadel gedroogd',"cat":'Fruit',"kcal":277,"kh":75,"suikers":66,"eiwit":2,"vet":0,"verz":0.0,"vezels":7,"natrium":1,"portie":30},
    {"naam":'Rozijnen',"cat":'Fruit',"kcal":299,"kh":79,"suikers":59,"eiwit":3,"vet":0,"verz":0.0,"vezels":4,"natrium":11,"portie":30},
    {"naam":'Abrikoos gedroogd',"cat":'Fruit',"kcal":241,"kh":63,"suikers":53,"eiwit":3,"vet":0,"verz":0.0,"vezels":7,"natrium":10,"portie":30},
    {"naam":'Appelmoes',"cat":'Fruit',"kcal":68,"kh":18,"suikers":16,"eiwit":0,"vet":0,"verz":0.0,"vezels":1,"natrium":2,"portie":120},
    {"naam":'Framboos',"cat":'Fruit',"kcal":52,"kh":12,"suikers":4,"eiwit":1,"vet":1,"verz":0.0,"vezels":7,"natrium":1,"portie":100},
    {"naam":'Grapefruit',"cat":'Fruit',"kcal":42,"kh":11,"suikers":7,"eiwit":1,"vet":0,"verz":0.0,"vezels":2,"natrium":0,"portie":150},
    {"naam":'Energiegel standaard',"cat":'Sportvoeding',"kcal":100,"kh":25,"suikers":17,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":55,"portie":40},
    {"naam":'Energiegel cafeïne',"cat":'Sportvoeding',"kcal":100,"kh":25,"suikers":17,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":55,"portie":40},
    {"naam":'Sportdrank poeder',"cat":'Sportvoeding',"kcal":390,"kh":96,"suikers":80,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":800,"portie":35},
    {"naam":'Isotone sportdrank',"cat":'Sportvoeding',"kcal":28,"kh":7,"suikers":6,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":46,"portie":500},
    {"naam":'Energiereep',"cat":'Sportvoeding',"kcal":380,"kh":60,"suikers":30,"eiwit":10,"vet":10,"verz":3.0,"vezels":3,"natrium":200,"portie":65},
    {"naam":'Proteïnereep',"cat":'Sportvoeding',"kcal":350,"kh":30,"suikers":5,"eiwit":30,"vet":12,"verz":4.0,"vezels":5,"natrium":300,"portie":60},
    {"naam":'Whey proteïne',"cat":'Sportvoeding',"kcal":380,"kh":6,"suikers":4,"eiwit":80,"vet":4,"verz":1.0,"vezels":0,"natrium":200,"portie":30},
    {"naam":'Caseïne proteïne',"cat":'Sportvoeding',"kcal":360,"kh":5,"suikers":2,"eiwit":78,"vet":2,"verz":1.0,"vezels":0,"natrium":350,"portie":30},
    {"naam":'Recovery shake',"cat":'Sportvoeding',"kcal":350,"kh":50,"suikers":20,"eiwit":25,"vet":5,"verz":1.0,"vezels":2,"natrium":300,"portie":80},
    {"naam":'Elektrolyten tablet',"cat":'Sportvoeding',"kcal":5,"kh":1,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":250,"portie":5},
    {"naam":'Maltodextrine',"cat":'Sportvoeding',"kcal":383,"kh":95,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":5,"portie":40},
    {"naam":'Dextrose',"cat":'Sportvoeding',"kcal":393,"kh":99,"suikers":99,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":0,"portie":40},
    {"naam":'ORS oplossing',"cat":'Sportvoeding',"kcal":18,"kh":5,"suikers":4,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":460,"portie":500},
    {"naam":'Rijstwafel chocolate',"cat":'Sportvoeding',"kcal":410,"kh":75,"suikers":25,"eiwit":6,"vet":10,"verz":5.0,"vezels":2,"natrium":50,"portie":20},
    {"naam":'Water',"cat":'Dranken',"kcal":0,"kh":0,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":0,"portie":500},
    {"naam":'Koffie zwart',"cat":'Dranken',"kcal":2,"kh":0,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":2,"portie":150},
    {"naam":'Thee zwart',"cat":'Dranken',"kcal":1,"kh":0,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":3,"portie":200},
    {"naam":'Sinaasappelsap',"cat":'Dranken',"kcal":45,"kh":10,"suikers":9,"eiwit":1,"vet":0,"verz":0.0,"vezels":0,"natrium":1,"portie":200},
    {"naam":'Appelsap',"cat":'Dranken',"kcal":46,"kh":11,"suikers":10,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":3,"portie":200},
    {"naam":'Cola',"cat":'Dranken',"kcal":42,"kh":11,"suikers":11,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":4,"portie":330},
    {"naam":'Cola Zero',"cat":'Dranken',"kcal":1,"kh":0,"suikers":0,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":14,"portie":330},
    {"naam":'Energiedrank',"cat":'Dranken',"kcal":45,"kh":11,"suikers":11,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":50,"portie":250},
    {"naam":'Kokoswater',"cat":'Dranken',"kcal":19,"kh":4,"suikers":4,"eiwit":1,"vet":0,"verz":0.0,"vezels":0,"natrium":105,"portie":250},
    {"naam":'Sojamelk',"cat":'Dranken',"kcal":42,"kh":3,"suikers":2,"eiwit":3,"vet":2,"verz":0.3,"vezels":0,"natrium":40,"portie":200},
    {"naam":'Olijfolie',"cat":'Sauzen & spreads',"kcal":884,"kh":0,"suikers":0,"eiwit":0,"vet":100,"verz":14.0,"vezels":0,"natrium":0,"portie":10},
    {"naam":'Zonnebloemolie',"cat":'Sauzen & spreads',"kcal":884,"kh":0,"suikers":0,"eiwit":0,"vet":100,"verz":10.0,"vezels":0,"natrium":0,"portie":10},
    {"naam":'Kokosolie',"cat":'Sauzen & spreads',"kcal":862,"kh":0,"suikers":0,"eiwit":0,"vet":100,"verz":87.0,"vezels":0,"natrium":0,"portie":10},
    {"naam":'Tomatensaus',"cat":'Sauzen & spreads',"kcal":72,"kh":12,"suikers":9,"eiwit":2,"vet":2,"verz":0.3,"vezels":2,"natrium":590,"portie":100},
    {"naam":'Pesto groen',"cat":'Sauzen & spreads',"kcal":490,"kh":5,"suikers":2,"eiwit":8,"vet":49,"verz":9.0,"vezels":2,"natrium":700,"portie":20},
    {"naam":'Honing',"cat":'Sauzen & spreads',"kcal":304,"kh":82,"suikers":82,"eiwit":0,"vet":0,"verz":0.0,"vezels":0,"natrium":4,"portie":15},
    {"naam":'Confituur',"cat":'Sauzen & spreads',"kcal":250,"kh":62,"suikers":60,"eiwit":0,"vet":0,"verz":0.0,"vezels":1,"natrium":10,"portie":20},
    {"naam":'Pindakaas',"cat":'Sauzen & spreads',"kcal":594,"kh":20,"suikers":9,"eiwit":25,"vet":50,"verz":10.0,"vezels":6,"natrium":410,"portie":20},
    {"naam":'Amandelboter',"cat":'Sauzen & spreads',"kcal":614,"kh":19,"suikers":5,"eiwit":21,"vet":56,"verz":4.0,"vezels":10,"natrium":5,"portie":20},
    {"naam":'Tahini',"cat":'Sauzen & spreads',"kcal":595,"kh":21,"suikers":0,"eiwit":17,"vet":54,"verz":8.0,"vezels":9,"natrium":115,"portie":15},
    {"naam":'Mayonaise',"cat":'Sauzen & spreads',"kcal":680,"kh":2,"suikers":2,"eiwit":1,"vet":75,"verz":11.0,"vezels":0,"natrium":640,"portie":15},
    {"naam":'Mosterd',"cat":'Sauzen & spreads',"kcal":66,"kh":6,"suikers":4,"eiwit":4,"vet":4,"verz":0.3,"vezels":3,"natrium":1100,"portie":10},
    {"naam":'Sojasaus',"cat":'Sauzen & spreads',"kcal":53,"kh":8,"suikers":2,"eiwit":8,"vet":0,"verz":0.0,"vezels":1,"natrium":5720,"portie":15},
    {"naam":'Chocopasta',"cat":'Sauzen & spreads',"kcal":539,"kh":58,"suikers":56,"eiwit":6,"vet":31,"verz":11.0,"vezels":4,"natrium":41,"portie":20},
    {"naam":'Hummus',"cat":'Sauzen & spreads',"kcal":177,"kh":14,"suikers":1,"eiwit":8,"vet":10,"verz":1.0,"vezels":6,"natrium":421,"portie":50},
    {"naam":'Ketjap manis',"cat":'Sauzen & spreads',"kcal":220,"kh":55,"suikers":50,"eiwit":6,"vet":0,"verz":0.0,"vezels":0,"natrium":3600,"portie":15},
    {"naam":'Walnoten',"cat":'Snacks',"kcal":654,"kh":14,"suikers":3,"eiwit":15,"vet":65,"verz":6.0,"vezels":7,"natrium":2,"portie":30},
    {"naam":'Amandelen',"cat":'Snacks',"kcal":579,"kh":22,"suikers":4,"eiwit":21,"vet":50,"verz":4.0,"vezels":13,"natrium":1,"portie":30},
    {"naam":'Cashewnoten',"cat":'Snacks',"kcal":553,"kh":33,"suikers":6,"eiwit":18,"vet":44,"verz":9.0,"vezels":3,"natrium":12,"portie":30},
    {"naam":'Pindanoten',"cat":'Snacks',"kcal":567,"kh":16,"suikers":4,"eiwit":26,"vet":49,"verz":7.0,"vezels":9,"natrium":18,"portie":30},
    {"naam":'Pistachenoten',"cat":'Snacks',"kcal":560,"kh":28,"suikers":8,"eiwit":20,"vet":45,"verz":6.0,"vezels":10,"natrium":1,"portie":30},
    {"naam":'Pure chocolade 70%',"cat":'Snacks',"kcal":598,"kh":46,"suikers":28,"eiwit":8,"vet":43,"verz":25.0,"vezels":11,"natrium":8,"portie":20},
    {"naam":'Melkchocolade',"cat":'Snacks',"kcal":535,"kh":60,"suikers":57,"eiwit":8,"vet":30,"verz":18.0,"vezels":2,"natrium":75,"portie":20},
    {"naam":'Chips',"cat":'Snacks',"kcal":536,"kh":53,"suikers":0,"eiwit":7,"vet":33,"verz":10.0,"vezels":4,"natrium":600,"portie":30},
    {"naam":'Popcorn naturel',"cat":'Snacks',"kcal":375,"kh":74,"suikers":1,"eiwit":11,"vet":5,"verz":1.0,"vezels":15,"natrium":8,"portie":30},
    {"naam":'Speculoos',"cat":'Snacks',"kcal":479,"kh":71,"suikers":33,"eiwit":6,"vet":18,"verz":9.0,"vezels":2,"natrium":350,"portie":16},
    {"naam":'Havermoutkoek',"cat":'Snacks',"kcal":430,"kh":66,"suikers":32,"eiwit":7,"vet":15,"verz":5.0,"vezels":4,"natrium":200,"portie":40},
    {"naam":'Winegums',"cat":'Snacks',"kcal":320,"kh":77,"suikers":45,"eiwit":6,"vet":0,"verz":0.0,"vezels":0,"natrium":30,"portie":40},
    {"naam":'Energiebal dadel-noot',"cat":'Snacks',"kcal":380,"kh":55,"suikers":45,"eiwit":7,"vet":15,"verz":2.0,"vezels":6,"natrium":20,"portie":30},
    {"naam":'Rijstwafels mais',"cat":'Snacks',"kcal":380,"kh":82,"suikers":3,"eiwit":7,"vet":3,"verz":0.5,"vezels":2,"natrium":200,"portie":9},
]


def _laad_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    try:
        sb = _get_supabase()
        q  = sb.table("fuelc_bibliotheek").select("*").eq("user_id", user_id)
        if categorie and categorie != "Alle":
            q = q.eq("categorie", categorie)
        r = q.order("naam").execute()
        data = r.data or []
        if zoek:
            zoek_l = zoek.lower()
            data = [p for p in data if zoek_l in (p.get("naam") or "").lower()]
        return data
    except Exception as e:
        print(f"Fout laden bibliotheek: {e}")
        return []

def _sla_product_op(user_id: str, product: dict) -> bool:
    try:
        sb = _get_supabase()
        product["user_id"] = user_id
        product["bron"]    = "manueel"
        sb.table("fuelc_bibliotheek").insert(product).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan: {e}")
        return False

def _update_product(product_id: str, data: dict) -> bool:
    try:
        sb = _get_supabase()
        sb.table("fuelc_bibliotheek").update(data).eq("id", product_id).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij updaten: {e}")
        return False

def _verwijder_product(product_id: str) -> bool:
    try:
        sb = _get_supabase()
        sb.table("fuelc_bibliotheek").delete().eq("id", product_id).execute()
        return True
    except Exception as e:
        st.error(f"Fout bij verwijderen: {e}")
        return False

def _macro_preview(kcal, kh, suikers, eiwit, vet, verzadigd, vezels, portie):
    """Toon macro balken per 100g en per portie."""
    totaal_macro = (kh or 0) + (eiwit or 0) + (vet or 0)
    if totaal_macro == 0:
        return
    kh_pct    = round((kh or 0) / totaal_macro * 100) if totaal_macro > 0 else 0
    eiwit_pct = round((eiwit or 0) / totaal_macro * 100) if totaal_macro > 0 else 0
    vet_pct   = round((vet or 0) / totaal_macro * 100) if totaal_macro > 0 else 0

    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-top:8px;">'
        f'<div style="font-size:0.65rem;color:#64748b;font-weight:700;margin-bottom:8px;">MACRO PREVIEW — per 100g</div>'
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
        f'<span style="font-size:0.7rem;color:#f97316;width:60px;">KH</span>'
        f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px;">'
        f'<div style="width:{kh_pct}%;height:100%;background:#f97316;border-radius:3px;"></div></div>'
        f'<span style="font-size:0.7rem;color:#f97316;width:40px;text-align:right;">{kh}g</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
        f'<span style="font-size:0.7rem;color:#3b82f6;width:60px;">Eiwit</span>'
        f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px;">'
        f'<div style="width:{eiwit_pct}%;height:100%;background:#3b82f6;border-radius:3px;"></div></div>'
        f'<span style="font-size:0.7rem;color:#3b82f6;width:40px;text-align:right;">{eiwit}g</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<span style="font-size:0.7rem;color:#8b5cf6;width:60px;">Vet</span>'
        f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px;">'
        f'<div style="width:{vet_pct}%;height:100%;background:#8b5cf6;border-radius:3px;"></div></div>'
        f'<span style="font-size:0.7rem;color:#8b5cf6;width:40px;text-align:right;">{vet}g</span></div>'
        + (f'<div style="font-size:0.65rem;color:#64748b;margin-top:8px;">'
           f'Per portie ({portie}g): {round((kcal or 0)*portie/100)}kcal · '
           f'{round((kh or 0)*portie/100)}g KH · '
           f'{round((eiwit or 0)*portie/100)}g eiwit · '
           f'{round((vet or 0)*portie/100)}g vet</div>' if portie > 0 else '')
        + '</div>',
        unsafe_allow_html=True)

def _stap_bibliotheek(user: dict):
    user_id = user.get("id", "")

    _sectie("VOEDSELBIBLIOTHEEK", "#22c55e")

    tab_add, tab_db, tab_scan, tab_lijst = st.tabs([
        "➕  Manueel toevoegen",
        "🔍  Voedselbank zoeken",
        "📷  Etiketscan",
        "📋  Mijn bibliotheek",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — PRODUCT TOEVOEGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Algemeen ─────────────────────────────────────────────────────────
        _sectie("PRODUCTINFO", "#22c55e")
        a1, a2 = st.columns(2)
        with a1:
            naam = st.text_input("Productnaam *",
                placeholder="bijv. Havermout Quaker", key="bib_naam")
        with a2:
            categorie = st.selectbox("Categorie *", CATEGORIE_OPTIES, key="bib_cat")

        p1, p2 = st.columns(2)
        with p1:
            portie_g = st.number_input("Standaard portiegrootte (g of ml)",
                0.0, 2000.0, 100.0, 5.0, key="bib_portie",
                help="Bijv. 45g voor een portie havermout, 200ml voor een glas melk")
        with p2:
            notitie = st.text_input("Notitie (optioneel)",
                placeholder="bijv. biologisch, glutenvrij...", key="bib_notitie")

        # ── Macros per 100g ───────────────────────────────────────────────────
        _sectie("VOEDINGSWAARDEN PER 100g", "#22c55e")
        st.markdown(
            '<div style="font-size:0.75rem;color:#94a3b8;margin-bottom:12px;">'
            'Voer de waarden in zoals vermeld op de verpakking (per 100g of per 100ml).</div>',
            unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        with m1:
            kcal_100g = st.number_input("Energie (kcal)", 0.0, 900.0, 0.0, 1.0, key="bib_kcal")
        with m2:
            kh_100g = st.number_input("Koolhydraten (g)", 0.0, 100.0, 0.0, 0.1, key="bib_kh")
        with m3:
            suikers_100g = st.number_input("waarvan suikers (g)", 0.0, 100.0, 0.0, 0.1, key="bib_suikers")

        m4, m5, m6 = st.columns(3)
        with m4:
            eiwit_100g = st.number_input("Eiwit (g)", 0.0, 100.0, 0.0, 0.1, key="bib_eiwit")
        with m5:
            vet_100g = st.number_input("Vetten (g)", 0.0, 100.0, 0.0, 0.1, key="bib_vet")
        with m6:
            verzadigd_100g = st.number_input("waarvan verzadigd (g)", 0.0, 100.0, 0.0, 0.1, key="bib_verz")

        m7, m8 = st.columns(2)
        with m7:
            vezels_100g = st.number_input("Vezels (g)", 0.0, 100.0, 0.0, 0.1, key="bib_vezels")
        with m8:
            natrium_100g = st.number_input("Natrium (mg)", 0.0, 5000.0, 0.0, 1.0, key="bib_natrium")

        # Live macro preview
        if kcal_100g > 0 or kh_100g > 0 or eiwit_100g > 0 or vet_100g > 0:
            _macro_preview(kcal_100g, kh_100g, suikers_100g,
                           eiwit_100g, vet_100g, verzadigd_100g,
                           vezels_100g, portie_g)

        favoriet = st.checkbox("⭐ Toevoegen aan favorieten", key="bib_fav")

        # ── Opslaan ───────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if naam and categorie:
            if st.button("💾 Product opslaan", key="bib_opslaan",
                         use_container_width=True):
                product = {
                    "naam":           naam.strip(),
                    "categorie":      categorie,
                    "portie_g":       portie_g if portie_g > 0 else None,
                    "kcal_100g":      kcal_100g if kcal_100g > 0 else None,
                    "kh_100g":        kh_100g if kh_100g > 0 else None,
                    "suikers_100g":   suikers_100g if suikers_100g > 0 else None,
                    "eiwit_100g":     eiwit_100g if eiwit_100g > 0 else None,
                    "vet_100g":       vet_100g if vet_100g > 0 else None,
                    "verzadigd_100g": verzadigd_100g if verzadigd_100g > 0 else None,
                    "vezels_100g":    vezels_100g if vezels_100g > 0 else None,
                    "natrium_100g":   natrium_100g if natrium_100g > 0 else None,
                    "favoriet":       favoriet,
                    "notitie":        notitie.strip() if notitie else None,
                }
                if _sla_product_op(user_id, product):
                    st.success(f"✅ '{naam}' opgeslagen in je bibliotheek!")
                    for k in ["bib_naam","bib_cat","bib_portie","bib_notitie",
                              "bib_kcal","bib_kh","bib_suikers","bib_eiwit",
                              "bib_vet","bib_verz","bib_vezels","bib_natrium","bib_fav"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            st.button("💾 Product opslaan", key="bib_opslaan",
                      use_container_width=True, disabled=True)
            st.caption("Vul minstens naam en categorie in.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — INGEBOUWDE VOEDSELBANK
    # ══════════════════════════════════════════════════════════════════════════
    with tab_db:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZOEKEN IN VOEDSELBANK", "#22c55e")
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:12px;">' +
            'Zoek in onze ingebouwde databank en importeer producten naar je bibliotheek.</div>',
            unsafe_allow_html=True)

        db_zoek = st.text_input("Zoeken op naam",
            placeholder="bijv. havermout, banaan, kipfilet...",
            key="db_zoek", label_visibility="collapsed")

        db_cat_filter = st.selectbox("Categorie",
            ["Alle"] + CATEGORIE_OPTIES, key="db_cat_filter",
            label_visibility="collapsed")

        # Filter de databank
        zoek_l = db_zoek.lower().strip() if db_zoek else ""
        db_results = [
            p for p in VOEDSEL_DB
            if (not zoek_l or zoek_l in p["naam"].lower())
            and (db_cat_filter == "Alle" or p["cat"] == db_cat_filter)
        ]

        st.markdown(
            f'<div style="font-size:0.72rem;color:#64748b;margin:8px 0;">' +
            f'{len(db_results)} product(en) gevonden</div>',
            unsafe_allow_html=True)

        for i, p in enumerate(db_results[:50]):
            with st.expander(f"{p['naam']} — {p['cat']}", expanded=False):
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;">' +
                    f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">KCAL</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#f97316;">{p["kcal"]}</div></div>' +
                    f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">KH</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#f97316;">{p["kh"]}g</div></div>' +
                    f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">EIWIT</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#3b82f6;">{p["eiwit"]}g</div></div>' +
                    f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">VET</div>' +
                    f'<div style="font-size:0.9rem;font-weight:700;color:#8b5cf6;">{p["vet"]}g</div></div>' +
                    f'</div>' +
                    f'<div style="font-size:0.7rem;color:#64748b;margin-bottom:8px;">' +
                    f'Standaard portie: {p["portie"]}g/ml · ' +
                    f'Vezels: {p["vezels"]}g · Natrium: {p["natrium"]}mg</div>',
                    unsafe_allow_html=True)

                import_cat = st.selectbox("Categorie",
                    CATEGORIE_OPTIES,
                    index=CATEGORIE_OPTIES.index(p["cat"]) if p["cat"] in CATEGORIE_OPTIES else 0,
                    key=f"db_cat_{i}")
                import_portie = st.number_input("Portiegrootte (g/ml)",
                    0.0, 2000.0, float(p["portie"]), 5.0,
                    key=f"db_portie_{i}")

                if st.button("📥 Toevoegen aan bibliotheek",
                             key=f"db_import_{i}", use_container_width=True):
                    product = {
                        "naam":           p["naam"],
                        "categorie":      import_cat,
                        "bron":           "databank",
                        "portie_g":       import_portie,
                        "kcal_100g":      p["kcal"],
                        "kh_100g":        p["kh"],
                        "suikers_100g":   p["suikers"],
                        "eiwit_100g":     p["eiwit"],
                        "vet_100g":       p["vet"],
                        "verzadigd_100g": p["verz"],
                        "vezels_100g":    p["vezels"],
                        "natrium_100g":   p["natrium"],
                        "favoriet":       False,
                        "user_id":        user_id,
                    }
                    if _sla_product_op(user_id, product):
                        st.success(f"✅ '{p['naam']}' toegevoegd!")
                        st.rerun()


    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — ETIKETSCAN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_scan:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ETIKETSCAN VIA AI", "#22c55e")
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:12px;">' +
            'Upload een foto van het voedingsetiket. De AI leest de macros automatisch uit ' +
            'en vult het formulier in. Controleer altijd de waarden voor het opslaan.</div>',
            unsafe_allow_html=True)

        scan_foto = st.file_uploader(
            "Foto van etiket uploaden (JPG of PNG)",
            type=["jpg","jpeg","png"],
            key="scan_foto")

        if scan_foto:
            import base64
            foto_bytes = scan_foto.read()
            foto_b64   = base64.b64encode(foto_bytes).decode()
            foto_mime  = "image/jpeg" if scan_foto.name.lower().endswith((".jpg",".jpeg")) else "image/png"

            st.image(scan_foto, caption="Geüpload etiket", width=300)

            if st.button("🤖 Scan etiket", key="scan_btn", use_container_width=True):
                with st.spinner("AI leest het etiket uit..."):
                    try:
                        import requests as _req2, json as _json
                        payload = {
                            "model": "claude-sonnet-4-5",
                            "max_tokens": 1000,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": foto_mime,
                                            "data": foto_b64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": (
                                            "Dit is een foto van een voedingsetiket. "
                                            "Lees de voedingswaarden per 100g of per 100ml uit. "
                                            "Geef ENKEL een JSON terug (gebruik 0 als niet gevonden): "
                                            "{naam, kcal_100g, kh_100g, suikers_100g, "
                                            "eiwit_100g, vet_100g, verzadigd_100g, "
                                            "vezels_100g, natrium_100g, portie_g}. "
                                            "Geen uitleg, enkel JSON met deze veldnamen."
                                        )
                                    }
                                ]
                            }]
                        }
                        import os as _os
                        _api_key = _os.environ.get("ANTHROPIC_API_KEY","")
                        resp_raw = _req2.post(
                            "https://api.anthropic.com/v1/messages",
                            json=payload,
                            headers={
                                "x-api-key": _api_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json",
                            },
                            timeout=30
                        )
                        resp = resp_raw.json()

                        if "content" not in resp:
                            raise Exception(resp.get("error", {}).get("message", str(resp)))
                        tekst = resp["content"][0]["text"].strip()
                        # Strip markdown fences indien aanwezig
                        if tekst.startswith("```"):
                            tekst = tekst.split("```")[1]
                            if tekst.startswith("json"):
                                tekst = tekst[4:]
                        scan_data = _json.loads(tekst.strip())
                        st.session_state["scan_result"] = scan_data
                        st.success("✅ Etiket uitgelezen!")
                    except Exception as e:
                        st.error(f"Scan mislukt: {e}")

        scan_result = st.session_state.get("scan_result", {})
        if scan_result:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("GESCANDE WAARDEN — controleer en pas aan", "#86efac")

            s1, s2 = st.columns(2)
            with s1:
                scan_naam    = st.text_input("Productnaam", value=scan_result.get("naam",""), key="scan_naam")
                scan_kcal    = st.number_input("Energie (kcal/100g)", 0.0, 900.0, float(scan_result.get("kcal_100g") or 0), 1.0, key="scan_kcal")
                scan_kh      = st.number_input("Koolhydraten (g/100g)", 0.0, 100.0, float(scan_result.get("kh_100g") or 0), 0.1, key="scan_kh")
                scan_suikers = st.number_input("Suikers (g/100g)", 0.0, 100.0, float(scan_result.get("suikers_100g") or 0), 0.1, key="scan_suikers")
            with s2:
                scan_eiwit   = st.number_input("Eiwit (g/100g)", 0.0, 100.0, float(scan_result.get("eiwit_100g") or 0), 0.1, key="scan_eiwit")
                scan_vet     = st.number_input("Vet (g/100g)", 0.0, 100.0, float(scan_result.get("vet_100g") or 0), 0.1, key="scan_vet")
                scan_verz    = st.number_input("Verzadigd vet (g/100g)", 0.0, 100.0, float(scan_result.get("verzadigd_100g") or 0), 0.1, key="scan_verz")
                scan_vezels  = st.number_input("Vezels (g/100g)", 0.0, 100.0, float(scan_result.get("vezels_100g") or 0), 0.1, key="scan_vezels")

            s3, s4 = st.columns(2)
            with s3:
                scan_natrium = st.number_input("Natrium (mg/100g)", 0.0, 5000.0, float(scan_result.get("natrium_100g") or 0), 1.0, key="scan_natrium")
            with s4:
                scan_portie  = st.number_input("Portiegrootte (g/ml)", 0.0, 2000.0, float(scan_result.get("portie_g") or 100), 5.0, key="scan_portie")

            scan_cat = st.selectbox("Categorie", CATEGORIE_OPTIES, key="scan_cat")

            st.markdown("<br>", unsafe_allow_html=True)
            if scan_naam:
                if st.button("💾 Opslaan in bibliotheek", key="scan_opslaan", use_container_width=True):
                    product = {
                        "naam":           scan_naam.strip(),
                        "categorie":      scan_cat,
                        "bron":           "etiketscan",
                        "portie_g":       scan_portie if scan_portie > 0 else None,
                        "kcal_100g":      scan_kcal,
                        "kh_100g":        scan_kh,
                        "suikers_100g":   scan_suikers,
                        "eiwit_100g":     scan_eiwit,
                        "vet_100g":       scan_vet,
                        "verzadigd_100g": scan_verz,
                        "vezels_100g":    scan_vezels,
                        "natrium_100g":   scan_natrium,
                        "favoriet":       False,
                        "user_id":        user_id,
                    }
                    if _sla_product_op(user_id, product):
                        st.success(f"✅ '{scan_naam}' opgeslagen!")
                        st.session_state.pop("scan_result", None)
                        st.session_state.pop("scan_foto", None)
                        st.rerun()
            else:
                st.caption("Vul een productnaam in om op te slaan.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — MIJN BIBLIOTHEEK
    # ══════════════════════════════════════════════════════════════════════════
    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)

        # Zoek en filter
        f1, f2 = st.columns([3, 1])
        with f1:
            zoek = st.text_input("🔍 Zoeken op naam",
                placeholder="bijv. havermout", key="bib_zoek",
                label_visibility="collapsed")
        with f2:
            filter_cat = st.selectbox("Categorie",
                ["Alle"] + CATEGORIE_OPTIES, key="bib_filter_cat",
                label_visibility="collapsed")

        toon_fav = st.checkbox("⭐ Alleen favorieten", key="bib_fav_filter")

        producten = _laad_bibliotheek(user_id, zoek, filter_cat)
        if toon_fav:
            producten = [p for p in producten if p.get("favoriet")]

        if not producten:
            st.markdown(
                '<div style="text-align:center;color:#64748b;padding:30px;">'
                'Geen producten gevonden.</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:12px;">'
                f'{len(producten)} product(en) gevonden</div>',
                unsafe_allow_html=True)

            for p in producten:
                fav_ster = "⭐ " if p.get("favoriet") else ""
                portie   = p.get("portie_g") or 0
                kcal     = p.get("kcal_100g") or 0
                kh       = p.get("kh_100g") or 0
                eiwit    = p.get("eiwit_100g") or 0
                vet      = p.get("vet_100g") or 0

                with st.expander(
                    f"{fav_ster}{p.get('naam','')} — {p.get('categorie','')}",
                    expanded=False):

                    # Macros tabel
                    st.markdown(
                        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);'
                        f'gap:8px;margin-bottom:10px;">'
                        f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">KCAL</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:#f97316;">{kcal}</div></div>'
                        f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">KH</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:#f97316;">{kh}g</div></div>'
                        f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">EIWIT</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:#3b82f6;">{eiwit}g</div></div>'
                        f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">VET</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:#8b5cf6;">{vet}g</div></div>'
                        f'</div>'
                        + (f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">'
                           f'Per portie ({portie}g): '
                           f'{round(kcal*portie/100)}kcal · '
                           f'{round(kh*portie/100)}g KH · '
                           f'{round(eiwit*portie/100)}g eiwit · '
                           f'{round(vet*portie/100)}g vet</div>'
                           if portie > 0 else '')
                        + (f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">'
                           f'Suikers: {p.get("suikers_100g") or 0}g · '
                           f'Vezels: {p.get("vezels_100g") or 0}g · '
                           f'Natrium: {p.get("natrium_100g") or 0}mg</div>'),
                        unsafe_allow_html=True)

                    if p.get("notitie"):
                        st.markdown(
                            f'<div style="font-size:0.75rem;color:#94a3b8;'
                            f'font-style:italic;margin-bottom:8px;">{p["notitie"]}</div>',
                            unsafe_allow_html=True)

                    # Acties
                    ba1, ba2 = st.columns(2)
                    with ba1:
                        fav_label = "★ Verwijder uit favorieten" if p.get("favoriet") else "☆ Voeg toe aan favorieten"
                        if st.button(fav_label, key=f"bib_fav_{p['id']}",
                                     use_container_width=True):
                            if _update_product(p["id"], {"favoriet": not p.get("favoriet")}):
                                st.rerun()
                    with ba2:
                        if st.button("🗑 Verwijderen", key=f"bib_del_{p['id']}",
                                     use_container_width=True):
                            if _verwijder_product(p["id"]):
                                st.success("Verwijderd.")
                                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 4 — DAGSCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

MAALTIJD_TEMPLATES = {
    "Klassiek": [
        {"naam": "Ontbijt",        "tijdstip": "07:30", "type": "ontbijt"},
        {"naam": "Lunch",          "tijdstip": "12:30", "type": "lunch"},
        {"naam": "Avondmaal",      "tijdstip": "18:30", "type": "avond"},
    ],
    "Intermittent 16:8": [
        {"naam": "Eerste maaltijd","tijdstip": "12:00", "type": "ontbijt"},
        {"naam": "Tweede maaltijd","tijdstip": "16:00", "type": "lunch"},
        {"naam": "Derde maaltijd", "tijdstip": "19:30", "type": "avond"},
    ],
    "Intermittent 18:6": [
        {"naam": "Eerste maaltijd","tijdstip": "13:00", "type": "ontbijt"},
        {"naam": "Tweede maaltijd","tijdstip": "18:30", "type": "avond"},
    ],
    "Vrij": [],
}

OPTIONELE_MOMENTEN = [
    {"naam": "Tussendoor 1", "tijdstip": "10:00", "type": "tussendoor"},
    {"naam": "Tussendoor 2", "tijdstip": "15:00", "type": "tussendoor"},
    {"naam": "Tussendoor 3", "tijdstip": "21:00", "type": "tussendoor"},
]

PCT_VAST = {
    3: {"ontbijt": 30, "lunch": 35, "avond": 35},
    2: {"ontbijt": 45, "avond": 55},
}

PCT_TUSSENDOOR = 8  # % per optioneel moment

HERSTEL_MACROS = {
    "kh_pct":    52,
    "eiwit_pct": 33,
    "vet_pct":   15,
}

def _bereken_moment_doelen(energie_dag: int, momenten: list,
                            training_timing: str, profiel: dict) -> list:
    """Bereken macro doelen per maaltijdmoment."""
    kh_pct    = profiel.get("kh_doel_pct", 50) or 50
    eiwit_pct = profiel.get("eiwit_doel_pct", 25) or 25
    vet_pct   = profiel.get("vet_doel_pct", 25) or 25

    vaste     = [m for m in momenten if m["type"] in ("ontbijt","lunch","avond")]
    optionele = [m for m in momenten if m["type"] == "tussendoor"]
    n_vast    = len(vaste)
    n_opt     = len(optionele)

    # Basisverdeling vaste momenten
    if n_vast == 3:
        pcts = {"ontbijt": 30, "lunch": 35, "avond": 35}
    elif n_vast == 2:
        types = [m["type"] for m in vaste]
        if "lunch" not in types:
            pcts = {"ontbijt": 45, "avond": 55}
        else:
            pcts = {"ontbijt": 40, "lunch": 60}
    else:
        pcts = {"ontbijt": 100}

    # Optionele momenten: elk 8%, schaal vaste naar beneden
    opt_totaal = n_opt * PCT_TUSSENDOOR
    schaalfactor = (100 - opt_totaal) / 100
    pcts = {k: round(v * schaalfactor) for k, v in pcts.items()}

    # Herstel timing — bepaal welk moment na training valt
    herstel_idx = None
    if training_timing != "Geen training":
        tijden = [m.get("tijdstip","00:00") for m in momenten]
        training_uur = {
            "Ochtend (voor 11u)": "10:30",
            "Middag (11u-15u)":   "14:00",
            "Avond (na 15u)":     "18:00",
        }.get(training_timing, None)
        if training_uur:
            for i, t in enumerate(tijden):
                if t > training_uur:
                    herstel_idx = i
                    break

    result = []
    opt_count = 0
    for i, m in enumerate(momenten):
        if m["type"] == "tussendoor":
            energie_m = round(energie_dag * PCT_TUSSENDOOR / 100)
            opt_count += 1
        else:
            energie_m = round(energie_dag * pcts.get(m["type"], 20) / 100)

        # Herstelmaaltijd: aangepaste macros (stil, geen label)
        if i == herstel_idx:
            kh_m    = round(energie_m * HERSTEL_MACROS["kh_pct"]    / 100 / 4)
            eiwit_m = round(energie_m * HERSTEL_MACROS["eiwit_pct"] / 100 / 4)
            vet_m   = round(energie_m * HERSTEL_MACROS["vet_pct"]   / 100 / 9)
        else:
            kh_m    = round(energie_m * kh_pct    / 100 / 4)
            eiwit_m = round(energie_m * eiwit_pct / 100 / 4)
            vet_m   = round(energie_m * vet_pct   / 100 / 9)

        result.append({**m,
            "energie_doel": energie_m,
            "kh_doel_g":    kh_m,
            "eiwit_doel_g": eiwit_m,
            "vet_doel_g":   vet_m,
        })
    return result

def _laad_dagschema(user_id: str, datum: str) -> dict:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_dagschema").select("*").eq("user_id", user_id).eq("datum", datum).execute()
        return r.data[0] if r.data else {}
    except:
        return {}

def _sla_dagschema_op(user_id: str, datum: str, schema: dict) -> bool:
    try:
        import json as _json
        sb = _get_supabase()
        bestaand = sb.table("fuelc_dagschema").select("id").eq("user_id", user_id).eq("datum", datum).execute()
        schema["user_id"] = user_id
        schema["datum"]   = datum
        if bestaand.data:
            sb.table("fuelc_dagschema").update(schema).eq("user_id", user_id).eq("datum", datum).execute()
        else:
            sb.table("fuelc_dagschema").insert(schema).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan schema: {e}")
        return False

def _laad_maaltijditems(schema_id: str) -> list:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_dagboek").select("*").eq("schema_id", schema_id).order("moment").execute()
        return r.data or []
    except:
        return []

def _sla_maaltijditem_op(user_id: str, schema_id: str, moment: int,
                          product: dict, hoeveelheid: float) -> bool:
    try:
        sb  = _get_supabase()
        f   = hoeveelheid / 100
        item = {
            "user_id":    user_id,
            "schema_id":  schema_id,
            "datum":      str(st.session_state.get("schema_datum", "")),
            "moment":     moment,
            "product_id": product["id"],
            "naam":       product["naam"],
            "hoeveelheid_g": hoeveelheid,
            "kcal":       round((product.get("kcal_100g") or 0) * f, 1),
            "kh_g":       round((product.get("kh_100g") or 0) * f, 1),
            "eiwit_g":    round((product.get("eiwit_100g") or 0) * f, 1),
            "vet_g":      round((product.get("vet_100g") or 0) * f, 1),
            "vezels_g":   round((product.get("vezels_100g") or 0) * f, 1),
        }
        sb.table("fuelc_dagboek").insert(item).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan item: {e}")
        return False

def _verwijder_maaltijditem(item_id: str) -> bool:
    try:
        sb = _get_supabase()
        sb.table("fuelc_dagboek").delete().eq("id", item_id).execute()
        return True
    except:
        return False

def _macro_ring(label: str, waarde: float, doel: float, kleur: str):
    pct  = min(100, round(waarde / doel * 100)) if doel > 0 else 0
    over = waarde > doel
    kleur_balk = "#ef4444" if over else kleur
    st.markdown(
        f'<div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">'
        f'<div style="font-size:0.6rem;color:#64748b;font-weight:700;">{label}</div>'
        f'<div style="font-size:1rem;font-weight:800;color:{kleur_balk};">{round(waarde)}g</div>'
        f'<div style="font-size:0.65rem;color:#475569;">/ {round(doel)}g</div>'
        f'<div style="background:#1e293b;border-radius:3px;height:5px;margin-top:4px;">'
        f'<div style="width:{pct}%;height:100%;background:{kleur_balk};border-radius:3px;"></div>'
        f'</div></div>',
        unsafe_allow_html=True)

def _stap_dagschema(user: dict):
    user_id = user.get("id","")
    profiel = st.session_state.get("fc_profiel", {})
    energie_dag = int(profiel.get("energie_doel", 2000) or 2000)

    _sectie("DAGSCHEMA", "#22c55e")

    # ── Dag selecteren ────────────────────────────────────────────────────────
    from datetime import date as _date
    col_d, col_t, col_if = st.columns(3)
    with col_d:
        gekozen_datum = st.date_input("Datum", value=_date.today(), key="schema_datum")
    with col_t:
        training_timing = st.selectbox("Training vandaag",
            ["Geen training","Ochtend (voor 11u)","Middag (11u-15u)","Avond (na 15u)"],
            key="schema_training")
    with col_if:
        eet_patroon = st.selectbox("Eetpatroon",
            list(MAALTIJD_TEMPLATES.keys()), key="schema_patroon")

    # ── Maaltijdmomenten samenstellen ─────────────────────────────────────────
    _sectie("MAALTIJDMOMENTEN", "#22c55e")

    basis = MAALTIJD_TEMPLATES[eet_patroon].copy()

    if eet_patroon == "Vrij":
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:10px;">'
            'Voeg je eigen maaltijdmomenten toe.</div>',
            unsafe_allow_html=True)

    # Optionele tussendoor momenten
    if eet_patroon in ("Klassiek", "Intermittent 16:8"):
        st.markdown(
            '<div style="font-size:0.75rem;color:#64748b;margin-bottom:8px;">'
            'Extra momenten toevoegen:</div>',
            unsafe_allow_html=True)
        opt_cols = st.columns(3)
        gekozen_opt = []
        for i, opt in enumerate(OPTIONELE_MOMENTEN):
            with opt_cols[i]:
                if st.checkbox(opt["naam"], key=f"schema_opt_{i}"):
                    gekozen_opt.append(opt.copy())
        basis = basis + gekozen_opt

    # Vrij patroon: momenten manueel toevoegen
    if eet_patroon == "Vrij":
        n_vrij = st.session_state.get("schema_n_vrij", 1)
        vrij_momenten = []
        for vi in range(n_vrij):
            vc1, vc2, vc3 = st.columns([3, 2, 0.5])
            with vc1:
                vnaam = st.text_input(f"Naam", placeholder="bijv. Ontbijt",
                    key=f"schema_vrij_naam_{vi}", label_visibility="collapsed")
            with vc2:
                vtijd = st.text_input(f"Tijdstip", placeholder="07:30",
                    key=f"schema_vrij_tijd_{vi}", label_visibility="collapsed")
            with vc3:
                if st.button("✕", key=f"schema_vrij_del_{vi}") and n_vrij > 1:
                    st.session_state["schema_n_vrij"] = n_vrij - 1
                    st.rerun()
            if vnaam:
                vrij_momenten.append({"naam": vnaam, "tijdstip": vtijd or "00:00", "type": "tussendoor"})
        basis = vrij_momenten
        if st.button("➕ Moment toevoegen", key="schema_vrij_add"):
            st.session_state["schema_n_vrij"] = n_vrij + 1
            st.rerun()

    # Tijdstippen aanpasbaar maken
    if basis and eet_patroon != "Vrij":
        st.markdown(
            '<div style="font-size:0.75rem;color:#64748b;margin:8px 0 4px;">Tijdstippen aanpassen:</div>',
            unsafe_allow_html=True)
        tcols = st.columns(min(len(basis), 4))
        for i, m in enumerate(basis):
            with tcols[i % 4]:
                nieuw_tijd = st.text_input(
                    m["naam"], value=m["tijdstip"],
                    key=f"schema_tijd_{i}",
                    label_visibility="visible")
                basis[i]["tijdstip"] = nieuw_tijd

    # Sorteer op tijdstip
    try:
        basis = sorted(basis, key=lambda x: x.get("tijdstip","00:00"))
    except:
        pass

    # Bereken macro doelen
    momenten_met_doelen = _bereken_moment_doelen(
        energie_dag, basis, training_timing, profiel)

    # ── Dagoverzicht ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _sectie("DAGOVERZICHT", "#22c55e")

    kh_dag    = round(energie_dag * (profiel.get("kh_doel_pct",50) or 50) / 100 / 4)
    eiwit_dag = round(energie_dag * (profiel.get("eiwit_doel_pct",25) or 25) / 100 / 4)
    vet_dag   = round(energie_dag * (profiel.get("vet_doel_pct",25) or 25) / 100 / 9)

    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #22c55e;border-radius:10px;'
        f'padding:12px 16px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="font-size:0.65rem;color:#64748b;">ENERGIE DOEL</div>'
        f'<div style="font-size:1.2rem;font-weight:800;color:#22c55e;">{energie_dag} kcal</div></div>'
        f'<div><div style="font-size:0.65rem;color:#64748b;">KH</div>'
        f'<div style="font-size:1rem;font-weight:700;color:#f97316;">{kh_dag}g</div></div>'
        f'<div><div style="font-size:0.65rem;color:#64748b;">EIWIT</div>'
        f'<div style="font-size:1rem;font-weight:700;color:#3b82f6;">{eiwit_dag}g</div></div>'
        f'<div><div style="font-size:0.65rem;color:#64748b;">VET</div>'
        f'<div style="font-size:1rem;font-weight:700;color:#8b5cf6;">{vet_dag}g</div></div>'
        f'<div><div style="font-size:0.65rem;color:#64748b;">MAALTIJDEN</div>'
        f'<div style="font-size:1rem;font-weight:700;color:#22c55e;">{len(basis)}</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    # Opslaan schema knop
    if basis:
        if st.button("💾 Schema opslaan voor deze dag", key="schema_opslaan",
                     use_container_width=True):
            import json as _json
            schema_data = {
                "energie_doel":    energie_dag,
                "kh_doel_g":       kh_dag,
                "eiwit_doel_g":    eiwit_dag,
                "vet_doel_g":      vet_dag,
                "aantal_maaltijden": len(basis),
                "momenten_json":   _json.dumps(momenten_met_doelen),
                "training_timing": training_timing,
                "eet_patroon":     eet_patroon,
            }
            if _sla_dagschema_op(user_id, str(gekozen_datum), schema_data):
                st.success("✅ Schema opgeslagen!")
                st.session_state["actief_schema"] = schema_data
                st.session_state["actief_momenten"] = momenten_met_doelen
                st.rerun()

    # ── Maaltijdmomenten invullen ─────────────────────────────────────────────
    schema_opgeslagen = st.session_state.get("actief_schema") or _laad_dagschema(user_id, str(gekozen_datum))

    if schema_opgeslagen:
        import json as _json
        momenten_actief = st.session_state.get("actief_momenten")
        if not momenten_actief:
            try:
                momenten_actief = _json.loads(schema_opgeslagen.get("momenten_json","[]"))
            except:
                momenten_actief = momenten_met_doelen
        schema_id = schema_opgeslagen.get("id", str(gekozen_datum))

        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("MAALTIJDEN INVULLEN", "#22c55e")

        # Laad alle items voor deze dag
        alle_items = _laad_maaltijditems(str(schema_id)) if schema_opgeslagen.get("id") else []

        # Totalen berekend uit ingevoerde items
        totaal_kcal  = sum(i.get("kcal",0) or 0 for i in alle_items)
        totaal_kh    = sum(i.get("kh_g",0) or 0 for i in alle_items)
        totaal_eiwit = sum(i.get("eiwit_g",0) or 0 for i in alle_items)
        totaal_vet   = sum(i.get("vet_g",0) or 0 for i in alle_items)

        # Progressiebalk dag
        pct_kcal = min(100, round(totaal_kcal / energie_dag * 100)) if energie_dag > 0 else 0
        over_kcal = totaal_kcal > energie_dag
        balk_kleur = "#ef4444" if over_kcal else ("#22c55e" if pct_kcal >= 80 else "#fbbf24")
        st.markdown(
            f'<div style="margin-bottom:16px;">'
            f'<div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:4px;">'
            f'<span style="color:#64748b;">Dag totaal</span>'
            f'<span style="color:{balk_kleur};font-weight:700;">{round(totaal_kcal)} / {energie_dag} kcal</span>'
            f'</div>'
            f'<div style="background:#1e293b;border-radius:4px;height:8px;">'
            f'<div style="width:{pct_kcal}%;height:100%;background:{balk_kleur};border-radius:4px;"></div>'
            f'</div></div>',
            unsafe_allow_html=True)

        for mi, moment in enumerate(momenten_actief):
            moment_naam = moment.get("naam","")
            moment_tijd = moment.get("tijdstip","")
            e_doel      = moment.get("energie_doel", 0)
            kh_doel     = moment.get("kh_doel_g", 0)
            eiwit_doel  = moment.get("eiwit_doel_g", 0)
            vet_doel    = moment.get("vet_doel_g", 0)

            # Items voor dit moment
            items_moment = [it for it in alle_items if it.get("moment") == mi]
            m_kcal  = sum(i.get("kcal",0) or 0 for i in items_moment)
            m_kh    = sum(i.get("kh_g",0) or 0 for i in items_moment)
            m_eiwit = sum(i.get("eiwit_g",0) or 0 for i in items_moment)
            m_vet   = sum(i.get("vet_g",0) or 0 for i in items_moment)

            pct_m = min(100, round(m_kcal / e_doel * 100)) if e_doel > 0 else 0
            over_m = m_kcal > e_doel * 1.1
            kleur_m = "#ef4444" if over_m else ("#22c55e" if pct_m >= 80 else "#fbbf24" if pct_m >= 40 else "#334155")

            with st.expander(
                f"🕐 {moment_tijd} — {moment_naam} — {round(m_kcal)}/{e_doel} kcal",
                expanded=mi == 0):

                # Macro doelen
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1: _macro_ring("KCAL", m_kcal, e_doel, "#22c55e")
                with mc2: _macro_ring("KH", m_kh, kh_doel, "#f97316")
                with mc3: _macro_ring("EIWIT", m_eiwit, eiwit_doel, "#3b82f6")
                with mc4: _macro_ring("VET", m_vet, vet_doel, "#8b5cf6")

                # Ingevoerde items tonen
                if items_moment:
                    st.markdown("<br>", unsafe_allow_html=True)
                    for item in items_moment:
                        ic1, ic2 = st.columns([5, 1])
                        with ic1:
                            st.markdown(
                                f'<div style="font-size:0.82rem;color:#f1f5f9;padding:4px 0;">'
                                f'{item.get("naam","")} — {item.get("hoeveelheid_g",0)}g · '
                                f'{round(item.get("kcal",0))}kcal · '
                                f'{round(item.get("kh_g",0))}g KH · '
                                f'{round(item.get("eiwit_g",0))}g eiwit</div>',
                                unsafe_allow_html=True)
                        with ic2:
                            if st.button("✕", key=f"del_item_{item['id']}"):
                                _verwijder_maaltijditem(item["id"])
                                st.rerun()

                # Maaltijdvoorstel AI
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🤖 Maaltijdvoorstel", key=f"voorstel_{mi}",
                             use_container_width=False):
                    with st.spinner("Voorstel wordt gegenereerd..."):
                        try:
                            import requests as _req3, json as _json2
                            bibliotheek = _laad_bibliotheek(user_id)
                            bib_kort = [{"naam": p["naam"],
                                         "kcal": p.get("kcal_100g",0),
                                         "kh": p.get("kh_100g",0),
                                         "eiwit": p.get("eiwit_100g",0),
                                         "vet": p.get("vet_100g",0),
                                         "portie": p.get("portie_g",100)}
                                        for p in bibliotheek[:30]]
                            prompt = (
                                f"Stel een {moment_naam} voor dat past bij deze doelen: "
                                f"{e_doel} kcal, {kh_doel}g KH, {eiwit_doel}g eiwit, {vet_doel}g vet. "
                                f"Tijdstip: {moment_tijd}. "
                                f"Gebruik bij voorkeur producten uit deze bibliotheek (anders vrij): "
                                f"{_json2.dumps(bib_kort, ensure_ascii=False)}. "
                                f"Geef een kort praktisch voorstel in het Nederlands. Max 80 woorden."
                            )
                            import os as _os3
                            _api_key3 = _os3.environ.get("ANTHROPIC_API_KEY","")
                            resp = _req3.post(
                                "https://api.anthropic.com/v1/messages",
                                json={
                                    "model": "claude-sonnet-4-5",
                                    "max_tokens": 300,
                                    "messages": [{"role":"user","content": prompt}]
                                },
                                headers={
                                    "x-api-key": _api_key3,
                                    "anthropic-version": "2023-06-01",
                                    "content-type": "application/json",
                                },
                                timeout=20
                            ).json()
                            voorstel_tekst = resp["content"][0]["text"]
                            st.session_state[f"voorstel_{mi}"] = voorstel_tekst
                        except Exception as e:
                            st.error(f"Voorstel mislukt: {e}")

                if st.session_state.get(f"voorstel_{mi}"):
                    st.markdown(
                        f'<div style="background:#0f172a;border-left:3px solid #22c55e;'
                        f'border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.82rem;'
                        f'color:#f1f5f9;margin:8px 0;">'
                        f'🤖 {st.session_state[f"voorstel_{mi}"]}</div>',
                        unsafe_allow_html=True)

                # Product toevoegen uit bibliotheek
                st.markdown("<br>", unsafe_allow_html=True)
                _sectie("PRODUCT TOEVOEGEN", "#86efac")
                bibliotheek = _laad_bibliotheek(user_id)
                if not bibliotheek:
                    st.caption("Geen producten in bibliotheek. Voeg eerst producten toe in Blok 3.")
                else:
                    prod_namen = [p["naam"] for p in bibliotheek]
                    zoek_prod = st.selectbox("Kies product",
                        ["— kies —"] + prod_namen,
                        key=f"prod_keuze_{mi}")

                    if zoek_prod != "— kies —":
                        gekozen_prod = next((p for p in bibliotheek if p["naam"] == zoek_prod), None)
                        if gekozen_prod:
                            portie_def = float(gekozen_prod.get("portie_g") or 100)
                            hoeveelheid = st.number_input(
                                f"Hoeveelheid (g/ml)",
                                0.0, 2000.0, portie_def, 5.0,
                                key=f"prod_hoev_{mi}")

                            # Preview
                            f = hoeveelheid / 100
                            st.markdown(
                                f'<div style="font-size:0.75rem;color:#22c55e;margin-top:-8px;">'
                                f'{round((gekozen_prod.get("kcal_100g") or 0)*f)}kcal · '
                                f'{round((gekozen_prod.get("kh_100g") or 0)*f,1)}g KH · '
                                f'{round((gekozen_prod.get("eiwit_100g") or 0)*f,1)}g eiwit · '
                                f'{round((gekozen_prod.get("vet_100g") or 0)*f,1)}g vet'
                                f'</div>',
                                unsafe_allow_html=True)

                            if schema_opgeslagen.get("id") and st.button(
                                    f"➕ Toevoegen aan {moment_naam}",
                                    key=f"prod_add_{mi}", use_container_width=True):
                                if _sla_maaltijditem_op(
                                        user_id, schema_opgeslagen["id"],
                                        mi, gekozen_prod, hoeveelheid):
                                    st.success(f"✅ Toegevoegd!")
                                    st.rerun()
                            elif not schema_opgeslagen.get("id"):
                                st.caption("Sla het schema eerst op om producten toe te voegen.")


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
