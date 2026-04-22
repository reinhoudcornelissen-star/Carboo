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

    tab_add, tab_lijst = st.tabs([
        "➕  Product toevoegen",
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
    # TAB 2 — MIJN BIBLIOTHEEK
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
