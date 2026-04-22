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


@st.cache_resource
def _get_supabase_client():
    """Gecachede Supabase client — één connectie per server instantie."""
    url = _get_secrets("SUPABASE_URL")
    key = _get_secrets("SUPABASE_KEY")
    return create_client(url, key)

def _get_supabase():
    return _get_supabase_client()


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

@st.cache_data(ttl=60)
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
        _laad_profiel.clear()
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

@st.cache_data(ttl=120)
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
        _laad_zones.clear()
        return True
    except Exception as e:
        st.error(f"Fout opslaan zones: {e}")
        return False

@st.cache_data(ttl=60)
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
        _laad_trainingen.clear()
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


@st.cache_data(ttl=30)
def _laad_gecombineerde_bibliotheek_raw(user_id: str) -> list:
    """Gecachede gecombineerde bibliotheek zonder filter."""
    eigen = _laad_bibliotheek_raw(user_id)
    eigen_namen = {p["naam"].lower() for p in eigen}
    databank = []
    for p in VOEDSEL_DB:
        if p["naam"].lower() not in eigen_namen:
            databank.append({
                "id": f"db_{p['naam']}", "naam": p["naam"],
                "categorie": p["cat"], "bron": "databank",
                "portie_g": p["portie"], "kcal_100g": p["kcal"],
                "kh_100g": p["kh"], "suikers_100g": p["suikers"],
                "eiwit_100g": p["eiwit"], "vet_100g": p["vet"],
                "verzadigd_100g": p["verz"], "vezels_100g": p["vezels"],
                "natrium_100g": p["natrium"], "favoriet": False,
            })
    return eigen + databank

def _laad_gecombineerde_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    """Combineer eigen bibliotheek + ingebouwde databank met optionele filters."""
    gecombineerd = _laad_gecombineerde_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        gecombineerd = [p for p in gecombineerd if zoek_l in p["naam"].lower()]
    if categorie and categorie != "Alle":
        gecombineerd = [p for p in gecombineerd if p.get("categorie","") == categorie]
    return gecombineerd

@st.cache_data(ttl=30)
def _laad_bibliotheek_raw(user_id: str) -> list:
    """Laad alle bibliotheek items zonder filter — gecached."""
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_bibliotheek").select("*").eq("user_id", user_id).order("naam").execute()
        return r.data or []
    except Exception as e:
        print(f"Fout laden bibliotheek: {e}")
        return []

def _laad_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    data = _laad_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        data = [p for p in data if zoek_l in (p.get("naam") or "").lower()]
    if categorie and categorie != "Alle":
        data = [p for p in data if p.get("categorie","") == categorie]
    return data

def _sla_product_op(user_id: str, product: dict) -> bool:
    try:
        sb = _get_supabase()
        product["user_id"] = user_id
        if "bron" not in product:
            product["bron"] = "manueel"
        sb.table("fuelc_bibliotheek").insert(product).execute()
        _laad_bibliotheek_raw.clear()
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
        _laad_bibliotheek_raw.clear()
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

# ─── RECEPTENBEHEER ──────────────────────────────────────────────────────────

def _laad_eigen_recepten(user_id: str) -> list:
    try:
        sb = _get_supabase()
        r  = sb.table("fuelc_recepten_eigen").select("*")\
               .or_(f"user_id.eq.{user_id},is_globaal.eq.true")\
               .order("naam").execute()
        return r.data or []
    except Exception as e:
        print(f"Fout laden recepten: {e}")
        return []

def _sla_eigen_recept_op(user_id: str, recept: dict) -> bool:
    try:
        sb = _get_supabase()
        recept["user_id"] = user_id
        sb.table("fuelc_recepten_eigen").insert(recept).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan recept: {e}")
        return False

def _verwijder_eigen_recept(recept_id: str) -> bool:
    try:
        _get_supabase().table("fuelc_recepten_eigen").delete().eq("id", recept_id).execute()
        return True
    except: return False

def _laad_alle_recepten(user_id: str) -> list:
    """Combineer vaste databank + eigen recepten."""
    eigen = _laad_eigen_recepten(user_id)
    # Zet eigen recepten om naar zelfde structuur als RECEPT_DB
    eigen_conv = []
    for r in eigen:
        import json as _j
        ing = r.get("ingredienten") or []
        if isinstance(ing, str):
            try: ing = _j.loads(ing)
            except: ing = []
        eigen_conv.append({
            "id":           r["id"],
            "naam":         r["naam"],
            "type":         r.get("type","lunch"),
            "kcal":         int(r.get("kcal") or 0),
            "kh":           float(r.get("kh") or 0),
            "eiwit":        float(r.get("eiwit") or 0),
            "vet":          float(r.get("vet") or 0),
            "ingredienten": [(i.get("naam",""), i.get("gram",0)) for i in ing] if ing else [],
            "bereiding":    r.get("bereiding",""),
            "eigen":        True,
        })
    return RECEPT_DB + eigen_conv

def _render_receptenbeheer(user_id: str):
    """Tab voor receptenbeheer in bibliotheek."""
    import json as _j

    tab_add, tab_lijst = st.tabs(["➕ Recept toevoegen", "📋 Mijn recepten"])

    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("NIEUW RECEPT", "#22c55e")

        ra1, ra2 = st.columns(2)
        with ra1:
            r_naam = st.text_input("Naam recept *", key="r_naam",
                placeholder="bijv. Havermout met fruit")
        with ra2:
            r_type = st.selectbox("Type *", ["ontbijt","tussendoor","lunch","avond"],
                key="r_type",
                format_func=lambda x: {"ontbijt":"🌅 Ontbijt","tussendoor":"🍎 Tussendoor",
                                        "lunch":"🥗 Lunch","avond":"🍽️ Avond"}[x])

        _sectie("MACRO'S", "#22c55e")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: r_kcal  = st.number_input("Kcal", 0, 2000, 400, 10, key="r_kcal")
        with mc2: r_kh    = st.number_input("KH (g)", 0.0, 300.0, 50.0, 1.0, key="r_kh")
        with mc3: r_eiwit = st.number_input("Eiwit (g)", 0.0, 150.0, 20.0, 1.0, key="r_eiwit")
        with mc4: r_vet   = st.number_input("Vet (g)", 0.0, 100.0, 10.0, 1.0, key="r_vet")

        _sectie("INGREDIËNTEN", "#22c55e")
        n_ing = st.session_state.get("r_n_ing", 3)
        ingredienten = []
        for ii in range(n_ing):
            ic1, ic2, ic3 = st.columns([4,2,0.5])
            with ic1:
                ing_naam = st.text_input(f"Product {ii+1}", key=f"r_ing_naam_{ii}",
                    label_visibility="collapsed" if ii > 0 else "visible",
                    placeholder="bijv. Havermout")
            with ic2:
                ing_gram = st.number_input("gram", 0.0, 1000.0, 100.0, 5.0,
                    key=f"r_ing_gram_{ii}",
                    label_visibility="collapsed" if ii > 0 else "visible")
            with ic3:
                if st.button("✕", key=f"r_ing_del_{ii}") and n_ing > 1:
                    st.session_state["r_n_ing"] = n_ing - 1
                    st.rerun()
            if ing_naam:
                ingredienten.append({"naam": ing_naam, "gram": ing_gram})

        if st.button("➕ Ingredient toevoegen", key="r_ing_add"):
            st.session_state["r_n_ing"] = n_ing + 1
            st.rerun()

        _sectie("BEREIDING", "#22c55e")
        r_bereiding = st.text_area("Bereidingswijze (max 3 stappen)",
            key="r_bereiding", height=80,
            placeholder="1. Kook de havermout 3 min. 2. Voeg fruit toe. 3. Serveer warm.")

        st.markdown("<br>", unsafe_allow_html=True)
        if r_naam:
            if user.get("role","") == "admin":
                r_globaal = st.checkbox("🌍 Globaal recept (zichtbaar voor alle gebruikers)", key="r_globaal")
            if st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True):
                recept = {
                    "naam":         r_naam.strip(),
                    "type":         r_type,
                    "kcal":         r_kcal,
                    "kh":           r_kh,
                    "eiwit":        r_eiwit,
                    "vet":          r_vet,
                    "ingredienten": _j.dumps(ingredienten),
                    "bereiding":    r_bereiding.strip() if r_bereiding else "",
                    "is_globaal":   st.session_state.get("r_globaal", False),
                }
                if _sla_eigen_recept_op(user_id, recept):
                    st.success(f"✅ '{r_naam}' opgeslagen!")
                    for k in ["r_naam","r_kcal","r_kh","r_eiwit","r_vet","r_bereiding","r_n_ing"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True, disabled=True)
            st.caption("Vul minstens een naam in.")

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        eigen_recepten = _laad_eigen_recepten(user_id)

        if not eigen_recepten:
            st.markdown(
                '<div style="text-align:center;color:#64748b;padding:30px;">'
                'Nog geen eigen recepten toegevoegd.</div>',
                unsafe_allow_html=True)
        else:
            TYPE_LABEL = {"ontbijt":"🌅 Ontbijt","tussendoor":"🍎 Tussendoor",
                          "lunch":"🥗 Lunch","avond":"🍽️ Avond"}
            for r in eigen_recepten:
                import json as _j2
                ing = r.get("ingredienten") or []
                if isinstance(ing, str):
                    try: ing = _j2.loads(ing)
                    except: ing = []
                with st.expander(
                    f"{TYPE_LABEL.get(r.get('type',''), '🍴')} {r.get('naam','')} — "
                    f"{r.get('kcal',0)}kcal · {r.get('kh',0)}g KH · {r.get('eiwit',0)}g eiwit",
                    expanded=False):
                    if ing:
                        ing_tekst = " · ".join([f"{i.get('naam','')} {i.get('gram',0)}g" for i in ing])
                        st.markdown(f'<div style="font-size:0.78rem;color:#94a3b8;margin-bottom:6px;">{ing_tekst}</div>', unsafe_allow_html=True)
                    if r.get("bereiding"):
                        st.markdown(f'<div style="font-size:0.78rem;color:#64748b;">{r["bereiding"]}</div>', unsafe_allow_html=True)
                    if st.button("🗑 Verwijderen", key=f"r_del_{r['id']}"):
                        _verwijder_eigen_recept(r["id"])
                        st.rerun()



def _stap_bibliotheek(user: dict):
    user_id = user.get("id", "")

    _sectie("VOEDSELBIBLIOTHEEK", "#22c55e")

    tab_add, tab_db, tab_scan, tab_lijst, tab_recepten = st.tabs([
        "➕  Manueel toevoegen",
        "🔍  Voedselbank zoeken",
        "📷  Etiketscan",
        "📋  Mijn bibliotheek",
        "🍴  Recepten",
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

    with tab_recepten:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_receptenbeheer(user_id)



RECEPT_DB = [
    # ── ONTBIJT ───────────────────────────────────────────────────────────────
    {
        "naam": "Havermout met banaan en honing",
        "type": "ontbijt",
        "kcal": 420, "kh": 72, "eiwit": 14, "vet": 8,
        "ingredienten": [
            ("Havermout", 80), ("Volle melk", 200), ("Banaan", 120), ("Honing", 15)
        ],
        "bereiding": "1. Kook de havermout 3 min in de melk. 2. Snijd de banaan in schijfjes. 3. Leg op de pap en druppel honing erover."
    },
    {
        "naam": "Volkoren boterhammen met ei en tomaat",
        "type": "ontbijt",
        "kcal": 390, "kh": 48, "eiwit": 22, "vet": 12,
        "ingredienten": [
            ("Volkorenbrood", 105), ("Ei groot", 120), ("Tomaat", 100), ("Boter", 10)
        ],
        "bereiding": "1. Bak de eieren in boter. 2. Snijd tomaat in schijfjes. 3. Beleg de boterhammen."
    },
    {
        "naam": "Griekse yoghurt met bosbes en granola",
        "type": "ontbijt",
        "kcal": 380, "kh": 52, "eiwit": 18, "vet": 10,
        "ingredienten": [
            ("Griekse yoghurt vol", 200), ("Bosbes", 100), ("Granola", 45)
        ],
        "bereiding": "1. Schep yoghurt in een kom. 2. Verdeel bosbessen erover. 3. Strooi granola erbovenop."
    },
    {
        "naam": "Roerei met champignons op brood",
        "type": "ontbijt",
        "kcal": 450, "kh": 44, "eiwit": 26, "vet": 18,
        "ingredienten": [
            ("Ei groot", 180), ("Champignon", 100), ("Bruin brood", 70), ("Boter", 10)
        ],
        "bereiding": "1. Bak champignons 3 min in boter. 2. Klop eieren los en roer door de pan. 3. Serveer op geroosterd brood."
    },
    {
        "naam": "Smoothie met havermout en fruit",
        "type": "ontbijt",
        "kcal": 400, "kh": 68, "eiwit": 12, "vet": 7,
        "ingredienten": [
            ("Havermout", 50), ("Banaan", 120), ("Aardbei", 100), ("Halfvolle melk", 200)
        ],
        "bereiding": "1. Doe alle ingrediënten in de blender. 2. Mix tot glad. 3. Direct serveren."
    },
    {
        "naam": "Kwark met rozijnen en appel",
        "type": "ontbijt",
        "kcal": 310, "kh": 48, "eiwit": 20, "vet": 2,
        "ingredienten": [
            ("Kwark mager", 200), ("Appel", 150), ("Rozijnen", 30)
        ],
        "bereiding": "1. Snijd appel in kleine stukjes. 2. Meng met kwark. 3. Voeg rozijnen toe en roer goed."
    },
    {
        "naam": "Pannenkoeken met appelmoes",
        "type": "ontbijt",
        "kcal": 480, "kh": 78, "eiwit": 14, "vet": 12,
        "ingredienten": [
            ("Pannenkoek", 240), ("Appelmoes", 120), ("Honing", 15)
        ],
        "bereiding": "1. Bak pannenkoeken goudbruin. 2. Serveer met appelmoes. 3. Druppel honing erover."
    },
    {
        "naam": "Muesli met halfvolle melk en banaan",
        "type": "ontbijt",
        "kcal": 430, "kh": 70, "eiwit": 12, "vet": 9,
        "ingredienten": [
            ("Muesli", 80), ("Halfvolle melk", 200), ("Banaan", 120)
        ],
        "bereiding": "1. Doe muesli in een kom. 2. Giet melk erover. 3. Snijd banaan in schijfjes en voeg toe."
    },
    {
        "naam": "Volkoren toast met pindakaas en banaan",
        "type": "ontbijt",
        "kcal": 460, "kh": 62, "eiwit": 16, "vet": 16,
        "ingredienten": [
            ("Volkorenbrood", 105), ("Pindakaas", 40), ("Banaan", 120)
        ],
        "bereiding": "1. Rooster de boterhammen. 2. Smeer pindakaas erop. 3. Beleg met schijfjes banaan."
    },
    {
        "naam": "Skyr met kiwi en noten",
        "type": "ontbijt",
        "kcal": 340, "kh": 38, "eiwit": 24, "vet": 9,
        "ingredienten": [
            ("Skyr", 200), ("Kiwi", 100), ("Walnoten", 20), ("Honing", 10)
        ],
        "bereiding": "1. Schep skyr in een kom. 2. Snijd kiwi en leg bovenop. 3. Strooi gehakte walnoten en honing erover."
    },

    # ── TUSSENDOOR ────────────────────────────────────────────────────────────
    {
        "naam": "Appel met amandelboter",
        "type": "tussendoor",
        "kcal": 220, "kh": 28, "eiwit": 4, "vet": 11,
        "ingredienten": [
            ("Appel", 150), ("Amandelboter", 20)
        ],
        "bereiding": "1. Snijd appel in partjes. 2. Serveer met amandelboter als dip."
    },
    {
        "naam": "Rijstwafels met hummus",
        "type": "tussendoor",
        "kcal": 200, "kh": 32, "eiwit": 6, "vet": 6,
        "ingredienten": [
            ("Rijstwafel naturel", 36), ("Hummus", 50)
        ],
        "bereiding": "1. Smeer hummus op de rijstwafels. 2. Eventueel bestrooien met paprikapoeder."
    },
    {
        "naam": "Banaan met walnoten",
        "type": "tussendoor",
        "kcal": 250, "kh": 32, "eiwit": 4, "vet": 12,
        "ingredienten": [
            ("Banaan", 120), ("Walnoten", 25)
        ],
        "bereiding": "1. Pel de banaan. 2. Eet samen met een handjevol walnoten."
    },
    {
        "naam": "Volkoren cracker met plattekaas en tomaat",
        "type": "tussendoor",
        "kcal": 190, "kh": 22, "eiwit": 9, "vet": 7,
        "ingredienten": [
            ("Cracker volkoren", 30), ("Plattekaas", 60), ("Tomaat", 80)
        ],
        "bereiding": "1. Smeer plattekaas op crackers. 2. Beleg met schijfjes tomaat."
    },
    {
        "naam": "Griekse yoghurt met honing",
        "type": "tussendoor",
        "kcal": 210, "kh": 22, "eiwit": 14, "vet": 7,
        "ingredienten": [
            ("Griekse yoghurt vol", 150), ("Honing", 15)
        ],
        "bereiding": "1. Schep yoghurt in een kommetje. 2. Druppel honing erover."
    },
    {
        "naam": "Dadels met cashewnoten",
        "type": "tussendoor",
        "kcal": 240, "kh": 38, "eiwit": 4, "vet": 9,
        "ingredienten": [
            ("Dadel gedroogd", 40), ("Cashewnoten", 20)
        ],
        "bereiding": "1. Combineer dadels en cashewnoten in een bakje. 2. Direct serveren."
    },
    {
        "naam": "Kwark met aardbei",
        "type": "tussendoor",
        "kcal": 170, "kh": 20, "eiwit": 16, "vet": 1,
        "ingredienten": [
            ("Kwark mager", 150), ("Aardbei", 100), ("Honing", 10)
        ],
        "bereiding": "1. Snijd aardbeien in stukjes. 2. Meng met kwark en honing."
    },
    {
        "naam": "Boterham met kippenham en komkommer",
        "type": "tussendoor",
        "kcal": 220, "kh": 28, "eiwit": 14, "vet": 5,
        "ingredienten": [
            ("Bruin brood", 70), ("Kippenham", 60), ("Komkommer", 60)
        ],
        "bereiding": "1. Beleg boterham met kippenham. 2. Voeg schijfjes komkommer toe."
    },

    # ── LUNCH ─────────────────────────────────────────────────────────────────
    {
        "naam": "Volkoren boterhammen met kipfilet en sla",
        "type": "lunch",
        "kcal": 480, "kh": 52, "eiwit": 36, "vet": 12,
        "ingredienten": [
            ("Volkorenbrood", 140), ("Kipfilet", 100), ("Sla gemengd", 50),
            ("Tomaat", 80), ("Mayonaise", 15)
        ],
        "bereiding": "1. Snijd kipfilet in reepjes en kruid. 2. Bak 6 min in pan. 3. Beleg brood met sla, tomaat en kip."
    },
    {
        "naam": "Pasta met tonijn en tomaat",
        "type": "lunch",
        "kcal": 520, "kh": 68, "eiwit": 32, "vet": 9,
        "ingredienten": [
            ("Pasta wit gekookt", 250), ("Tonijn in water", 120),
            ("Tomatensaus", 100), ("Paprika rood", 80)
        ],
        "bereiding": "1. Kook pasta al dente. 2. Verwarm tomatensaus met paprika. 3. Meng met tonijn en pasta."
    },
    {
        "naam": "Rijst met kipfilet en groenten",
        "type": "lunch",
        "kcal": 540, "kh": 65, "eiwit": 38, "vet": 8,
        "ingredienten": [
            ("Rijst wit gekookt", 200), ("Kipfilet", 120),
            ("Broccoli", 150), ("Wortel", 80), ("Sojasaus", 15)
        ],
        "bereiding": "1. Kook rijst. 2. Bak kipfilet 8 min en snijd in stukjes. 3. Stoom groenten 5 min en serveer met sojasaus."
    },
    {
        "naam": "Soep met brood",
        "type": "lunch",
        "kcal": 380, "kh": 52, "eiwit": 16, "vet": 10,
        "ingredienten": [
            ("Wortel", 100), ("Ui", 80), ("Aardappel gekookt", 175),
            ("Kipfilet", 60), ("Volkorenbrood", 70)
        ],
        "bereiding": "1. Kook groenten en kip 20 min in bouillon. 2. Mix tot soep. 3. Serveer met volkorenbrood."
    },
    {
        "naam": "Quinoa salade met ei en groenten",
        "type": "lunch",
        "kcal": 490, "kh": 52, "eiwit": 24, "vet": 18,
        "ingredienten": [
            ("Quinoa gekookt", 185), ("Ei groot", 120),
            ("Komkommer", 100), ("Tomaat", 100), ("Olijfolie", 15)
        ],
        "bereiding": "1. Kook eieren 8 min. 2. Snijd groenten fijn. 3. Meng met quinoa en besprenkel met olijfolie."
    },
    {
        "naam": "Wraps met kalkoen en avocado",
        "type": "lunch",
        "kcal": 560, "kh": 55, "eiwit": 34, "vet": 22,
        "ingredienten": [
            ("Wrap", 120), ("Kalkoenfilet", 100),
            ("Avocado", 80), ("Sla gemengd", 50), ("Tomaat", 80)
        ],
        "bereiding": "1. Bak kalkoen 6 min en snijd in reepjes. 2. Prak avocado grof. 3. Vul wraps met alle ingrediënten."
    },
    {
        "naam": "Aardappelsalade met haring",
        "type": "lunch",
        "kcal": 500, "kh": 50, "eiwit": 24, "vet": 20,
        "ingredienten": [
            ("Aardappel gekookt", 300), ("Haring", 100),
            ("Ui", 60), ("Mayonaise", 30), ("Sla gemengd", 50)
        ],
        "bereiding": "1. Snijd aardappelen in blokjes. 2. Meng met mayonaise en ui. 3. Serveer met haring op sla."
    },
    {
        "naam": "Broodje zalm met komkommer",
        "type": "lunch",
        "kcal": 460, "kh": 44, "eiwit": 28, "vet": 18,
        "ingredienten": [
            ("Stokbrood", 100), ("Zalm", 100),
            ("Plattekaas", 50), ("Komkommer", 80)
        ],
        "bereiding": "1. Snijd stokbrood open. 2. Smeer plattekaas erop. 3. Beleg met zalm en komkommer."
    },
    {
        "naam": "Couscous met kip en paprika",
        "type": "lunch",
        "kcal": 510, "kh": 62, "eiwit": 34, "vet": 10,
        "ingredienten": [
            ("Couscous gekookt", 200), ("Kipfilet", 100),
            ("Paprika rood", 100), ("Wortel", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bereid couscous per verpakking. 2. Bak kip en groenten 8 min. 3. Meng alles en besprenkel met olijfolie."
    },
    {
        "naam": "Linzensoep met brood",
        "type": "lunch",
        "kcal": 430, "kh": 62, "eiwit": 22, "vet": 7,
        "ingredienten": [
            ("Linzen gekookt", 200), ("Wortel", 100),
            ("Ui", 80), ("Tomatensaus", 80), ("Volkorenbrood", 70)
        ],
        "bereiding": "1. Fruit ui aan. 2. Voeg linzen, wortel en tomatensaus toe, kook 15 min. 3. Serveer met brood."
    },
    {
        "naam": "Rijstwafel met kippenham en kaas",
        "type": "lunch",
        "kcal": 350, "kh": 40, "eiwit": 20, "vet": 11,
        "ingredienten": [
            ("Rijstwafel naturel", 36), ("Kippenham", 90),
            ("Edammer 30+", 30), ("Tomaat", 80)
        ],
        "bereiding": "1. Beleg rijstwafels met ham. 2. Voeg kaas en tomaat toe. 3. Direct serveren."
    },

    # ── AVOND ─────────────────────────────────────────────────────────────────
    {
        "naam": "Spaghetti bolognese",
        "type": "avond",
        "kcal": 620, "kh": 72, "eiwit": 36, "vet": 18,
        "ingredienten": [
            ("Pasta wit gekookt", 300), ("Rundergehakt mager", 120),
            ("Tomatensaus", 150), ("Ui", 80), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak ui en gehakt 8 min. 2. Voeg tomatensaus toe, sudder 10 min. 3. Serveer over pasta."
    },
    {
        "naam": "Kipfilet met aardappelen en broccoli",
        "type": "avond",
        "kcal": 580, "kh": 52, "eiwit": 48, "vet": 14,
        "ingredienten": [
            ("Kipfilet", 180), ("Aardappel gekookt", 300),
            ("Broccoli", 200), ("Boter", 10), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak kip 10 min in olie. 2. Kook aardappelen 20 min. 3. Stoom broccoli 5 min en serveer met beetje boter."
    },
    {
        "naam": "Zalm met rijst en courgette",
        "type": "avond",
        "kcal": 610, "kh": 56, "eiwit": 42, "vet": 20,
        "ingredienten": [
            ("Zalm", 180), ("Rijst wit gekookt", 200),
            ("Courgette", 150), ("Olijfolie", 15), ("Citroen", 30)
        ],
        "bereiding": "1. Kruid zalm en bak 4 min per kant. 2. Gril courgette in olie. 3. Serveer met rijst en citroensap."
    },
    {
        "naam": "Stoemp met worst en spek",
        "type": "avond",
        "kcal": 640, "kh": 58, "eiwit": 28, "vet": 28,
        "ingredienten": [
            ("Aardappel gekookt", 350), ("Wortel", 150),
            ("Spek", 40), ("Boter", 15), ("Halfvolle melk", 50)
        ],
        "bereiding": "1. Kook aardappelen en wortels gaar. 2. Stamp met boter en melk. 3. Bak spek krokant en meng erdoor."
    },
    {
        "naam": "Pasta pesto met kip en spinazie",
        "type": "avond",
        "kcal": 630, "kh": 64, "eiwit": 40, "vet": 22,
        "ingredienten": [
            ("Pasta volkoren gekookt", 280), ("Kipfilet", 150),
            ("Spinazie", 100), ("Pesto groen", 30)
        ],
        "bereiding": "1. Kook pasta. 2. Bak kip in reepjes 8 min. 3. Meng pasta met spinazie, kip en pesto."
    },
    {
        "naam": "Gebakken kabeljauw met aardappelpuree",
        "type": "avond",
        "kcal": 520, "kh": 48, "eiwit": 40, "vet": 14,
        "ingredienten": [
            ("Kabeljauw", 200), ("Aardappel gekookt", 300),
            ("Boter", 15), ("Halfvolle melk", 60), ("Broccoli", 150)
        ],
        "bereiding": "1. Stamp aardappelen met boter en melk. 2. Bak kabeljauw 4 min per kant. 3. Serveer met gestoomde broccoli."
    },
    {
        "naam": "Rijst met gehakt en paprika",
        "type": "avond",
        "kcal": 600, "kh": 66, "eiwit": 34, "vet": 18,
        "ingredienten": [
            ("Rijst wit gekookt", 220), ("Rundergehakt mager", 120),
            ("Paprika rood", 150), ("Ui", 80), ("Tomatensaus", 100)
        ],
        "bereiding": "1. Bak gehakt en ui 8 min. 2. Voeg paprika en saus toe, 10 min sudderen. 3. Serveer over rijst."
    },
    {
        "naam": "Linzen met zoete aardappel en spinazie",
        "type": "avond",
        "kcal": 560, "kh": 78, "eiwit": 24, "vet": 10,
        "ingredienten": [
            ("Linzen gekookt", 200), ("Zoete aardappel gekookt", 250),
            ("Spinazie", 100), ("Ui", 80), ("Olijfolie", 15)
        ],
        "bereiding": "1. Bak ui aan in olie. 2. Voeg linzen en zoete aardappel toe, 10 min verwarmen. 3. Roer spinazie erdoor."
    },
    {
        "naam": "Kip met groentewok en noedels",
        "type": "avond",
        "kcal": 570, "kh": 62, "eiwit": 38, "vet": 14,
        "ingredienten": [
            ("Kipfilet", 150), ("Pasta wit gekookt", 200),
            ("Broccoli", 120), ("Wortel", 100), ("Sojasaus", 20)
        ],
        "bereiding": "1. Bak kip 6 min. 2. Voeg groenten toe en roerbak 4 min. 3. Meng met noedels en sojasaus."
    },
    {
        "naam": "Biefstuk met frietjes en salade",
        "type": "avond",
        "kcal": 680, "kh": 58, "eiwit": 38, "vet": 28,
        "ingredienten": [
            ("Biefstuk", 150), ("Aardappel gekookt", 300),
            ("Sla gemengd", 80), ("Olijfolie", 15)
        ],
        "bereiding": "1. Bak biefstuk 3 min per kant. 2. Bak aardappelen als blokjes in oven 25 min. 3. Serveer met salade."
    },
    {
        "naam": "Ovenschotel met kip en groenten",
        "type": "avond",
        "kcal": 540, "kh": 44, "eiwit": 42, "vet": 18,
        "ingredienten": [
            ("Kipfilet", 180), ("Aardappel gekookt", 250),
            ("Courgette", 150), ("Paprika rood", 100), ("Olijfolie", 15)
        ],
        "bereiding": "1. Snijd alles in stukken en kruid. 2. Besprenkel met olijfolie. 3. Oven 200°C, 30 min bakken."
    },
    {
        "naam": "Varkenshaas met appel en aardappelen",
        "type": "avond",
        "kcal": 590, "kh": 54, "eiwit": 40, "vet": 18,
        "ingredienten": [
            ("Varkenshaas", 160), ("Aardappel gekookt", 280),
            ("Appel", 150), ("Boter", 15), ("Ui", 60)
        ],
        "bereiding": "1. Bak varkenshaas 10 min. 2. Fruit appel en ui in boter. 3. Serveer met gekookte aardappelen."
    },
    {
        "naam": "Tonijnpasta met olijven en tomaat",
        "type": "avond",
        "kcal": 550, "kh": 66, "eiwit": 34, "vet": 12,
        "ingredienten": [
            ("Pasta volkoren gekookt", 280), ("Tonijn in water", 150),
            ("Tomatensaus", 120), ("Olijfolie", 10)
        ],
        "bereiding": "1. Kook pasta al dente. 2. Verwarm tomatensaus. 3. Meng met tonijn en pasta, besprenkel met olijfolie."
    },
    {
        "naam": "Gehaktballen met aardappelpuree en erwtjes",
        "type": "avond",
        "kcal": 640, "kh": 60, "eiwit": 36, "vet": 24,
        "ingredienten": [
            ("Rundergehakt mager", 150), ("Aardappel gekookt", 300),
            ("Erwten", 100), ("Boter", 15), ("Halfvolle melk", 60)
        ],
        "bereiding": "1. Vorm gehaktballen en bak 12 min. 2. Stamp aardappelen met boter en melk. 3. Serveer met erwtjes."
    },
    {
        "naam": "Makreel met rijst en groene salade",
        "type": "avond",
        "kcal": 580, "kh": 52, "eiwit": 36, "vet": 22,
        "ingredienten": [
            ("Makreel", 150), ("Rijst volkoren gekookt", 200),
            ("Sla gemengd", 80), ("Citroen", 30), ("Olijfolie", 10)
        ],
        "bereiding": "1. Bak makreel 4 min per kant. 2. Kook rijst. 3. Serveer met salade en citroensap."
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 4 — WEEKSCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

MAALTIJD_TEMPLATES = {
    "Klassiek": [
        {"naam": "Ontbijt",   "tijdstip": "07:30", "type": "ontbijt"},
        {"naam": "Lunch",     "tijdstip": "12:30", "type": "lunch"},
        {"naam": "Avondmaal", "tijdstip": "18:30", "type": "avond"},
    ],
    "Intermittent 16:8": [
        {"naam": "Eerste maaltijd", "tijdstip": "12:00", "type": "ontbijt"},
        {"naam": "Tweede maaltijd", "tijdstip": "16:00", "type": "lunch"},
        {"naam": "Derde maaltijd",  "tijdstip": "19:30", "type": "avond"},
    ],
    "Intermittent 18:6": [
        {"naam": "Eerste maaltijd", "tijdstip": "13:00", "type": "ontbijt"},
        {"naam": "Tweede maaltijd", "tijdstip": "18:30", "type": "avond"},
    ],
}

OPTIONELE_MOMENTEN = [
    {"naam": "Tussendoor 1", "tijdstip": "10:00", "type": "tussendoor"},
    {"naam": "Tussendoor 2", "tijdstip": "15:00", "type": "tussendoor"},
    {"naam": "Tussendoor 3", "tijdstip": "21:00", "type": "tussendoor"},
]

PCT_TUSSENDOOR  = 8
HERSTEL_MACROS  = {"kh_pct": 52, "eiwit_pct": 33, "vet_pct": 15}
DAGEN_NL        = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

AI_SYSTEEM_PROMPT = """Je bent een Belgische sportdiëtist. Je stelt maaltijden voor die:
- Typisch Belgisch of Nederlands zijn (boterhammen, pap, aardappelen, soep, stoemp, pasta, rijst)
- Enkel uit natuurlijke voedingsmiddelen bestaan — GEEN supplementen of proteïnepoeders
- Praktisch en snel klaar te maken zijn
- Een korte bereidingswijze bevatten (max 3 stappen)
Je antwoordt altijd in het Nederlands."""

def _bereken_moment_doelen(energie_dag, momenten, training_timing, profiel):
    kh_pct    = profiel.get("kh_doel_pct", 50) or 50
    eiwit_pct = profiel.get("eiwit_doel_pct", 25) or 25
    vet_pct   = profiel.get("vet_doel_pct", 25) or 25
    vaste     = [m for m in momenten if m["type"] in ("ontbijt","lunch","avond")]
    n_vast    = len(vaste)
    n_opt     = len([m for m in momenten if m["type"] == "tussendoor"])
    if n_vast == 3:   pcts = {"ontbijt":30,"lunch":35,"avond":35}
    elif n_vast == 2:
        types = [m["type"] for m in vaste]
        pcts  = {"ontbijt":45,"avond":55} if "lunch" not in types else {"ontbijt":40,"lunch":60}
    else: pcts = {"ontbijt":100}
    schaalfactor = (100 - n_opt * PCT_TUSSENDOOR) / 100
    pcts = {k: round(v * schaalfactor) for k, v in pcts.items()}
    herstel_idx = None
    if training_timing and training_timing != "Geen training":
        uur = {"Ochtend (voor 11u)":"10:30","Middag (11u-15u)":"14:00","Avond (na 15u)":"18:00"}.get(training_timing)
        if uur:
            for i, m in enumerate(momenten):
                if m.get("tijdstip","00:00") > uur:
                    herstel_idx = i
                    break
    result = []
    for i, m in enumerate(momenten):
        e = round(energie_dag * (PCT_TUSSENDOOR if m["type"]=="tussendoor" else pcts.get(m["type"],20)) / 100)
        if i == herstel_idx:
            kh_m = round(e * HERSTEL_MACROS["kh_pct"] / 100 / 4)
            ei_m = round(e * HERSTEL_MACROS["eiwit_pct"] / 100 / 4)
            vt_m = round(e * HERSTEL_MACROS["vet_pct"] / 100 / 9)
        else:
            kh_m = round(e * kh_pct / 100 / 4)
            ei_m = round(e * eiwit_pct / 100 / 4)
            vt_m = round(e * vet_pct / 100 / 9)
        result.append({**m, "energie_doel":e, "kh_doel_g":kh_m, "eiwit_doel_g":ei_m, "vet_doel_g":vt_m})
    return result

def _laad_dagschema(user_id, datum):
    try:
        r = _get_supabase().table("fuelc_dagschema").select("*").eq("user_id",user_id).eq("datum",datum).execute()
        return r.data[0] if r.data else {}
    except: return {}

def _sla_dagschema_op(user_id, datum, schema):
    try:
        import json as _j
        sb = _get_supabase()
        schema["user_id"] = user_id
        schema["datum"]   = datum
        bestaand = sb.table("fuelc_dagschema").select("id").eq("user_id",user_id).eq("datum",datum).execute()
        if bestaand.data:
            sb.table("fuelc_dagschema").update(schema).eq("user_id",user_id).eq("datum",datum).execute()
            return bestaand.data[0]["id"]
        r = sb.table("fuelc_dagschema").insert(schema).execute()
        return r.data[0]["id"] if r.data else None
    except Exception as e:
        st.error(f"Fout: {e}")
        return None

def _laad_dagboek_items(user_id, datum, moment):
    try:
        cache_key = f"dagboek_cache_{datum}"
        if cache_key not in st.session_state:
            r = _get_supabase().table("fuelc_dagboek")                .select("id,datum,moment,naam,hoeveelheid_g,kcal,kh_g,eiwit_g,vet_g,vezels_g,product_id")                .eq("user_id",user_id).eq("datum",datum).execute()
            st.session_state[cache_key] = r.data or []
        return [i for i in st.session_state[cache_key] if i.get("moment") == moment]
    except: return []

def _invalideer_dagboek_cache(datum):
    """Verwijder cache na toevoegen/verwijderen."""
    cache_key = f"dagboek_cache_{datum}"
    if cache_key in st.session_state:
        del st.session_state[cache_key]

def _verwijder_dagboek_item(item_id, datum=None):
    try:
        _get_supabase().table("fuelc_dagboek").delete().eq("id",item_id).execute()
        if datum:
            _invalideer_dagboek_cache(datum)
        return True
    except: return False

def _sla_dagboek_item(user_id, datum, moment, product, hoeveelheid):
    try:
        f = hoeveelheid / 100
        # Zorg dat schema bestaat voor deze dag
        schema = _laad_dagschema(user_id, datum)
        if not schema:
            _sla_dagschema_op(user_id, datum, {
                "energie_doel": 2000, "kh_doel_g": 250,
                "eiwit_doel_g": 125, "vet_doel_g": 56,
                "aantal_maaltijden": 3, "momenten_json": "[]",
                "training_timing": "Geen training", "eet_patroon": "Klassiek",
            })
        # Enkel echte UUID's als product_id — databank items hebben fake ID
        prod_id = product.get("id","")
        if not prod_id or str(prod_id).startswith("db_"):
            prod_id = None

        _get_supabase().table("fuelc_dagboek").insert({
            "user_id":       user_id,
            "datum":         datum,
            "moment":        moment,
            "product_id":    prod_id,
            "naam":          product["naam"],
            "hoeveelheid_g": hoeveelheid,
            "kcal":          round((product.get("kcal_100g") or 0)*f, 1),
            "kh_g":          round((product.get("kh_100g") or 0)*f, 1),
            "eiwit_g":       round((product.get("eiwit_100g") or 0)*f, 1),
            "vet_g":         round((product.get("vet_100g") or 0)*f, 1),
            "vezels_g":      round((product.get("vezels_100g") or 0)*f, 1),
        }).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False

def _kies_recept(moment_type: str, energie_doel: int, alle_recepten: list = None) -> dict:
    """Kies het best passende recept op basis van type en energiedoel."""
    pool = alle_recepten if alle_recepten else RECEPT_DB
    kandidaten = [r for r in pool if r.get("type") == moment_type]
    if not kandidaten:
        kandidaten = pool
    return min(kandidaten, key=lambda r: abs((r.get("kcal") or 0) - energie_doel))

def _formatteer_recept(recept: dict, moment_naam: str, tijdstip: str) -> str:
    """Formatteer recept als leesbare tekst."""
    ingredienten = "\n".join([f"- {naam} — {gram}g" for naam, gram in recept["ingredienten"]])
    return (
        f"## {moment_naam} — {tijdstip}\n"
        f"**{recept['naam']}**\n"
        f"Ingrediënten:\n{ingredienten}\n\n"
        f"Bereiding: {recept['bereiding']}\n\n"
        f"Macro\'s: {recept['kcal']}kcal · {recept['kh']}g KH · {recept['eiwit']}g eiwit · {recept['vet']}g vet\n\n---"
    )

def _genereer_dagplan(momenten, training_timing, bibliotheek, user_id: str = ""):
    """Gratis dagplan op basis van vaste + eigen receptendatabank."""
    alle = _laad_alle_recepten(user_id) if user_id else RECEPT_DB
    secties = []
    for m in momenten:
        recept = _kies_recept(m.get("type","lunch"), m.get("energie_doel",500), alle)
        secties.append(_formatteer_recept(recept, m["naam"], m.get("tijdstip","")))
    return "\n\n".join(secties)

def _genereer_dagplan_ai(momenten, training_timing, bibliotheek):
    """AI dagplan — enkel op expliciete vraag (kost geld)."""
    import requests as _r, os as _o, json as _j
    bib = [p for p in bibliotheek if p.get("categorie","") != "Sportvoeding"][:20]
    bib_kort = [{"naam":p["naam"],"kcal":p.get("kcal_100g",0),"kh":p.get("kh_100g",0),
                 "eiwit":p.get("eiwit_100g",0),"portie":p.get("portie_g",100)} for p in bib]
    info = "\n".join([
        f"- {m['naam']} {m['tijdstip']}: {m['energie_doel']}kcal · {m['kh_doel_g']}g KH · {m['eiwit_doel_g']}g eiwit · {m['vet_doel_g']}g vet"
        for m in momenten])
    prompt = (
        f"Maak een persoonlijk dagplan voor {len(momenten)} maaltijden. Training: {training_timing}\n\n"
        f"Doelen:\n{info}\n\n"
        f"Bibliotheek (gebruik bij voorkeur):\n{_j.dumps(bib_kort, ensure_ascii=False)}\n\n"
        f"Geef voor ELKE maaltijd:\n## [Naam] — [tijdstip]\n**[Gerecht]**\n"
        f"Ingrediënten:\n- [product] — [g]\n\nBereiding: [max 3 stappen]\n\n"
        f"Macro\'s: [kcal]kcal · [kh]g KH · [eiwit]g eiwit · [vet]g vet\n\n---\n\n"
    )
    resp = _r.post("https://api.anthropic.com/v1/messages",
        json={"model":"claude-sonnet-4-5","max_tokens":2000,
              "system":AI_SYSTEEM_PROMPT,
              "messages":[{"role":"user","content":prompt}]},
        headers={"x-api-key":_o.environ.get("ANTHROPIC_API_KEY",""),
                 "anthropic-version":"2023-06-01","content-type":"application/json"},
        timeout=40).json()
    if "content" not in resp:
        raise Exception(resp.get("error",{}).get("message",str(resp)))
    return resp["content"][0]["text"]

def _stap_dagschema(user: dict):
    import json as _json
    from datetime import date as _date, timedelta as _td

    user_id     = user.get("id","")
    profiel     = st.session_state.get("fc_profiel", {})
    energie_dag = int(profiel.get("energie_doel", 2000) or 2000)
    kh_dag      = round(energie_dag * (profiel.get("kh_doel_pct",50) or 50) / 100 / 4)
    eiwit_dag   = round(energie_dag * (profiel.get("eiwit_doel_pct",25) or 25) / 100 / 4)
    vet_dag     = round(energie_dag * (profiel.get("vet_doel_pct",25) or 25) / 100 / 9)

    _sectie("WEEKSCHEMA", "#22c55e")

    # ── Weekinstellingen ──────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:#1e293b;border-radius:12px;padding:14px 16px;margin-bottom:16px;">',
        unsafe_allow_html=True)

    wi1, wi2, wi3 = st.columns(3)
    with wi1:
        week_start = st.date_input("Week van", value=_date.today(), key="week_start")
        # Naar maandag
        maandag = week_start - _td(days=week_start.weekday())
    with wi2:
        eet_patroon = st.selectbox("Eetpatroon (week)", ["Klassiek","Intermittent 16:8","Intermittent 18:6"], key="week_patroon")
    with wi3:
        st.markdown(
            f'<div style="padding-top:24px;font-size:0.75rem;color:#64748b;">'
            f'{maandag.strftime("%d/%m")} — {(maandag + _td(days=6)).strftime("%d/%m/%Y")}</div>',
            unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    # Tussendoor momenten
    if eet_patroon in ("Klassiek", "2 maaltijden", "Intermittent 16:8", "Intermittent 18:6"):
        st.markdown(
            '<div style="background:#1e293b;border-radius:10px;padding:10px 14px;margin-bottom:12px;">'
            '<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">Tussendoor momenten toevoegen aan alle dagen:</div>',
            unsafe_allow_html=True)
        opt_cols = st.columns(3)
        for _oi, _opt in enumerate(OPTIONELE_MOMENTEN):
            with opt_cols[_oi]:
                if st.checkbox(_opt["naam"], key=f"week_opt_{_oi}"):
                    pass  # Wordt gebruikt bij opbouw basis per dag
        st.markdown('</div>', unsafe_allow_html=True)

    def _bouw_basis(patroon):
        basis = MAALTIJD_TEMPLATES.get(patroon, MAALTIJD_TEMPLATES["Klassiek"]).copy()
        for _oi, _opt in enumerate(OPTIONELE_MOMENTEN):
            if st.session_state.get(f"week_opt_{_oi}", False):
                basis.append(_opt.copy())
        return sorted(basis, key=lambda x: x.get("tijdstip","00:00"))


    # Bibliotheek laden (1x)
    bibliotheek = _laad_gecombineerde_bibliotheek(user_id)

    # Laad alle schemas voor de week in één query
    @st.cache_data(ttl=60)
    def _laad_week_schemas(uid, ma_str, zo_str):
        try:
            r = _get_supabase().table("fuelc_dagschema").select("*")                .eq("user_id",uid).gte("datum",ma_str).lte("datum",zo_str).execute()
            return {row["datum"]: row for row in (r.data or [])}
        except: return {}

    zondag_str = str(maandag + _td(days=6))
    week_schemas = _laad_week_schemas(user_id, str(maandag), zondag_str)

    # ── 7 dagen ───────────────────────────────────────────────────────────────
    for dag_idx in range(7):
        dag_datum  = maandag + _td(days=dag_idx)
        dag_naam   = DAGEN_NL[dag_idx]
        dag_str    = str(dag_datum)
        dag_label  = f"{dag_naam} {dag_datum.strftime('%d/%m')}"
        is_vandaag = (dag_datum == _date.today())

        # Gebruik gecachede schemas
        schema_dag  = week_schemas.get(dag_str, {})
        heeft_plan  = bool(schema_dag)
        plan_key    = f"dagplan_{dag_str}"
        plan_tekst  = st.session_state.get(plan_key, "")

        # Dag header kleur
        border_kleur = "#22c55e" if heeft_plan else ("#f97316" if is_vandaag else "#334155")

        # Bouw momenten voor deze dag
        basis = _bouw_basis(eet_patroon)
        training_dag = st.session_state.get(f"training_{dag_str}", "Geen training")
        momenten = _bereken_moment_doelen(energie_dag, basis, training_dag, profiel)

        if schema_dag.get("momenten_json"):
            try:
                momenten = _json.loads(schema_dag["momenten_json"])
            except: pass

        # Dag totaal — gebruik _laad_dagboek_items cache
        alle_items_dag = []
        n_mom = len(_bereken_moment_doelen(energie_dag, _bouw_basis(eet_patroon),
                    st.session_state.get(f"training_{dag_str}","Geen training"), profiel))
        for _mi in range(max(n_mom, 5)):
            alle_items_dag += _laad_dagboek_items(user_id, dag_str, _mi)
        tot_kcal  = sum(i.get("kcal",0) or 0 for i in alle_items_dag)
        pct_dag   = min(100, round(tot_kcal/energie_dag*100)) if energie_dag > 0 else 0
        kleur_dag = "#22c55e" if pct_dag >= 80 else ("#fbbf24" if pct_dag >= 40 else "#334155")

        # ── Dag blok ─────────────────────────────────────────────────────────
        dag_open_key = f"dag_open_{dag_str}"

        # Dag header (altijd zichtbaar)
        h1, h2, h3, h4 = st.columns([3, 2, 1, 1])
        with h1:
            st.markdown(
                f'<div style="padding:8px 0;">'
                f'<span style="font-size:0.95rem;font-weight:800;color:#f8fafc;">{dag_label}</span>'
                f'{"<span style=\"background:#f97316;color:white;border-radius:4px;font-size:0.6rem;font-weight:700;padding:1px 6px;margin-left:8px;\">VANDAAG</span>" if is_vandaag else ""}'
                f'</div>',
                unsafe_allow_html=True)
        with h2:
            # Training selectie
            training_dag = st.selectbox("Training",
                ["Geen training","Ochtend (voor 11u)","Middag (11u-15u)","Avond (na 15u)"],
                key=f"training_{dag_str}",
                label_visibility="collapsed")
        with h3:
            if st.button("📋 Dagplan", key=f"gen_{dag_str}", use_container_width=True):
                mom = _bereken_moment_doelen(energie_dag, basis, training_dag, profiel)
                plan = _genereer_dagplan(mom, training_dag, bibliotheek, user_id)
                st.session_state[plan_key] = plan
                sid = _sla_dagschema_op(user_id, dag_str, {
                    "energie_doel":energie_dag,"kh_doel_g":kh_dag,
                    "eiwit_doel_g":eiwit_dag,"vet_doel_g":vet_dag,
                    "aantal_maaltijden":len(basis),
                    "momenten_json":_json.dumps(mom),
                    "training_timing":training_dag,
                    "eet_patroon":eet_patroon,
                })
                st.session_state[f"schema_id_{dag_str}"] = sid
                st.session_state[dag_open_key] = True
                st.rerun()
        with h4:
            label_open = "▲ Dicht" if st.session_state.get(dag_open_key) else "▼ Open"
            if st.button(label_open, key=f"toggle_{dag_str}", use_container_width=True):
                st.session_state[dag_open_key] = not st.session_state.get(dag_open_key, False)
                st.rerun()

        # Voortgangsbalk dag
        st.markdown(
            f'<div style="background:#1e293b;border-radius:3px;height:4px;margin-bottom:4px;">'
            f'<div style="width:{pct_dag}%;height:100%;background:{kleur_dag};border-radius:3px;"></div>'
            f'</div>'
            f'<div style="font-size:0.65rem;color:#64748b;margin-bottom:8px;">'
            f'{round(tot_kcal)} / {energie_dag} kcal · {len(alle_items_dag)} producten</div>',
            unsafe_allow_html=True)

        # ── Dag detail (inklapbaar) ───────────────────────────────────────────
        if st.session_state.get(dag_open_key, False):
            st.markdown(
                f'<div style="background:#1e293b;border-radius:12px;'
                f'border-left:3px solid {border_kleur};padding:14px;margin-bottom:4px;">',
                unsafe_allow_html=True)

            # Dag acties bovenaan
            da1, da2, da3 = st.columns(3)
            with da1:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#64748b;padding-top:8px;">' +
                    f'{"✅ Schema opgeslagen" if schema_dag else "⚠️ Nog niet opgeslagen"}</div>',
                    unsafe_allow_html=True)
            with da2:
                if st.button("💾 Dag opslaan", key=f"dag_ops_{dag_str}",
                             use_container_width=True):
                    mom = _bereken_moment_doelen(energie_dag, _bouw_basis(eet_patroon),
                        st.session_state.get(f"training_{dag_str}","Geen training"), profiel)
                    sid = _sla_dagschema_op(user_id, dag_str, {
                        "energie_doel": energie_dag, "kh_doel_g": kh_dag,
                        "eiwit_doel_g": eiwit_dag, "vet_doel_g": vet_dag,
                        "aantal_maaltijden": len(mom),
                        "momenten_json": _json.dumps(mom),
                        "training_timing": st.session_state.get(f"training_{dag_str}","Geen training"),
                        "eet_patroon": eet_patroon,
                    })
                    if sid:
                        week_schemas[dag_str] = {"id": sid}
                        st.success("✅ Dag opgeslagen!")
                        st.rerun()
            with da3:
                if plan_tekst and st.button("🗑 Dagplan wissen", key=f"plan_wis_{dag_str}",
                             use_container_width=True):
                    st.session_state.pop(plan_key, None)
                    st.session_state.pop(f"ai_plan_{dag_str}", None)
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Dagplan voorstel tonen
            ai_plan_key = f"ai_plan_{dag_str}"
            toon_plan = st.session_state.get(ai_plan_key, plan_tekst)

            pc1, pc2 = st.columns([3,1])
            with pc2:
                if st.button("✨ Verras me", key=f"ai_{dag_str}",
                             use_container_width=True,
                             help="AI genereert een persoonlijk voorstel (kost krediet)"):
                    with st.spinner("AI aan het werk..."):
                        try:
                            mom_ai = _bereken_moment_doelen(energie_dag, basis, training_dag, profiel)
                            ai_plan = _genereer_dagplan_ai(mom_ai, training_dag, bibliotheek)
                            st.session_state[ai_plan_key] = ai_plan
                            st.rerun()
                        except Exception as e:
                            st.error(f"AI mislukt: {e}")

            if toon_plan:
                st.markdown(
                    f'<div style="background:#0f172a;border-radius:8px;padding:14px;'
                    f'font-size:0.82rem;color:#f1f5f9;line-height:1.8;margin-bottom:14px;">'
                    f'{toon_plan.replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True)

            # Maaltijdmomenten
            schema_id = st.session_state.get(f"schema_id_{dag_str}") or schema_dag.get("id")

            for mi, moment in enumerate(momenten):
                m_naam   = moment.get("naam","")
                m_tijd   = moment.get("tijdstip","")
                e_doel   = moment.get("energie_doel",0)
                kh_doel  = moment.get("kh_doel_g",0)
                ei_doel  = moment.get("eiwit_doel_g",0)
                vt_doel  = moment.get("vet_doel_g",0)

                items    = _laad_dagboek_items(user_id, dag_str, mi)
                m_kcal   = sum(i.get("kcal",0) or 0 for i in items)
                m_kh     = sum(i.get("kh_g",0) or 0 for i in items)
                m_eiwit  = sum(i.get("eiwit_g",0) or 0 for i in items)
                m_vet    = sum(i.get("vet_g",0) or 0 for i in items)
                pct_m    = min(100, round(m_kcal/e_doel*100)) if e_doel > 0 else 0
                kleur_m  = "#ef4444" if m_kcal > e_doel*1.1 else ("#22c55e" if pct_m>=80 else "#fbbf24" if pct_m>=40 else "#475569")

                # Moment header
                mo_open_key = f"mo_open_{dag_str}_{mi}"
                mh1, mh2 = st.columns([4,1])
                with mh1:
                    st.markdown(
                        f'<div style="padding:6px 0 2px;">'
                        f'<span style="font-size:0.72rem;color:#64748b;">{m_tijd}</span>'
                        f'<span style="font-size:0.85rem;font-weight:700;color:#f8fafc;margin-left:8px;">{m_naam}</span>'
                        f'<span style="font-size:0.72rem;color:{kleur_m};margin-left:8px;">{round(m_kcal)}/{e_doel} kcal</span>'
                        f'</div>'
                        f'<div style="background:#0f172a;border-radius:3px;height:4px;margin-bottom:4px;">'
                        f'<div style="width:{pct_m}%;height:100%;background:{kleur_m};border-radius:3px;"></div>'
                        f'</div>',
                        unsafe_allow_html=True)
                with mh2:
                    mo_label = "▲" if st.session_state.get(mo_open_key) else "▼"
                    if st.button(mo_label, key=f"mo_toggle_{dag_str}_{mi}"):
                        st.session_state[mo_open_key] = not st.session_state.get(mo_open_key, False)
                        st.rerun()

                # Moment detail
                if st.session_state.get(mo_open_key, False):
                    st.markdown(
                        '<div style="background:#0f172a;border-radius:8px;padding:12px;margin-bottom:8px;">',
                        unsafe_allow_html=True)

                    # Macro doelen rij
                    st.markdown(
                        f'<div style="display:flex;gap:12px;font-size:0.7rem;margin-bottom:10px;">'
                        f'<span style="color:#f97316;">KH: {round(m_kh)}/{kh_doel}g</span>'
                        f'<span style="color:#3b82f6;">Eiwit: {round(m_eiwit)}/{ei_doel}g</span>'
                        f'<span style="color:#8b5cf6;">Vet: {round(m_vet)}/{vt_doel}g</span>'
                        f'</div>',
                        unsafe_allow_html=True)

                    # ── Geselecteerde producten overzicht ─────────────────────
                    # Maaltijd wissen knop
                    if items:
                        mc1, mc2 = st.columns([2,3])
                        with mc1:
                            if st.button("🗑 Maaltijd wissen",
                                         key=f"clear_mom_{dag_str}_{mi}"):
                                for _item in items:
                                    _verwijder_dagboek_item(_item["id"], dag_str)
                                st.rerun()
                    if items:
                        # Totaalrij
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:6px;padding:6px 10px;'
                            f'margin-bottom:6px;font-size:0.72rem;">'
                            f'<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr 1fr 0.5fr;'
                            f'gap:4px;color:#64748b;font-weight:700;margin-bottom:4px;">'
                            f'<span>PRODUCT</span><span>GRAM</span><span>KCAL</span>'
                            f'<span>KH</span><span>EIWIT</span><span></span></div>',
                            unsafe_allow_html=True)
                        for item in items:
                            ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([3,1,1,1,1,0.5])
                            with ic1:
                                st.markdown(
                                    f'<div style="font-size:0.78rem;color:#f1f5f9;padding:2px 0;">'
                                    f'{item.get("naam","")}</div>',
                                    unsafe_allow_html=True)
                            with ic2:
                                st.markdown(f'<div style="font-size:0.78rem;color:#94a3b8;padding:2px 0;">{item.get("hoeveelheid_g",0)}g</div>', unsafe_allow_html=True)
                            with ic3:
                                st.markdown(f'<div style="font-size:0.78rem;color:#f97316;padding:2px 0;">{round(item.get("kcal",0))}</div>', unsafe_allow_html=True)
                            with ic4:
                                st.markdown(f'<div style="font-size:0.78rem;color:#f97316;padding:2px 0;">{round(item.get("kh_g",0))}g</div>', unsafe_allow_html=True)
                            with ic5:
                                st.markdown(f'<div style="font-size:0.78rem;color:#3b82f6;padding:2px 0;">{round(item.get("eiwit_g",0))}g</div>', unsafe_allow_html=True)
                            with ic6:
                                if st.button("✕", key=f"del_{item['id']}"):
                                    _verwijder_dagboek_item(item["id"], dag_str)
                                    st.rerun()
                        # Totaalrij
                        st.markdown(
                            f'<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr 1fr 0.5fr;'
                            f'gap:4px;border-top:1px solid #334155;padding-top:4px;margin-top:2px;">'
                            f'<span style="font-size:0.72rem;color:#f8fafc;font-weight:700;">Totaal</span>'
                            f'<span style="font-size:0.72rem;color:#94a3b8;">—</span>'
                            f'<span style="font-size:0.72rem;color:#f97316;font-weight:700;">{round(m_kcal)}</span>'
                            f'<span style="font-size:0.72rem;color:#f97316;font-weight:700;">{round(m_kh)}g</span>'
                            f'<span style="font-size:0.72rem;color:#3b82f6;font-weight:700;">{round(m_eiwit)}g</span>'
                            f'<span></span></div></div>',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div style="font-size:0.75rem;color:#475569;margin-bottom:8px;">'
                            'Nog geen producten toegevoegd.</div>',
                            unsafe_allow_html=True)

                    # ── Product toevoegen ─────────────────────────────────────
                    if not schema_id:
                        st.markdown(
                            '<div style="font-size:0.75rem;color:#64748b;">Genereer eerst een dagplan.</div>',
                            unsafe_allow_html=True)
                    elif not bibliotheek:
                        st.caption("Voeg eerst producten toe in Blok 3.")
                    else:
                        fz1, fz2, fz3 = st.columns([3,2,1])
                        with fz1:
                            zoek = st.text_input("Zoek",
                                placeholder="Zoek product...",
                                key=f"zoek_{dag_str}_{mi}",
                                label_visibility="collapsed")
                        with fz2:
                            cat_filter = st.selectbox("Categorie",
                                ["Alle"] + CATEGORIE_OPTIES,
                                key=f"cat_{dag_str}_{mi}",
                                label_visibility="collapsed")
                        with fz3:
                            fav_only = st.checkbox("⭐", key=f"fav_{dag_str}_{mi}",
                                help="Enkel favorieten")

                        # Filter bibliotheek
                        gefilterd = [p for p in bibliotheek
                                     if (not zoek or zoek.lower() in p["naam"].lower())
                                     and (cat_filter == "Alle" or p.get("categorie","") == cat_filter)
                                     and (not fav_only or p.get("favoriet", False))]

                        if gefilterd:
                            keuze = st.selectbox(
                                "Product kiezen",
                                ["— kies product —"] + [p["naam"] for p in gefilterd],
                                key=f"pk_{dag_str}_{mi}",
                                label_visibility="collapsed")

                            if keuze != "— kies product —":
                                gekozen = next((p for p in gefilterd if p["naam"]==keuze), None)
                                if gekozen:
                                    portie = float(gekozen.get("portie_g") or 100)
                                    ac1, ac2 = st.columns([2,1])
                                    with ac1:
                                        hoev = st.number_input(
                                            "Hoeveelheid (g/ml)",
                                            0.0, 2000.0, portie, 5.0,
                                            key=f"hoev_{dag_str}_{mi}",
                                            label_visibility="collapsed")
                                    with ac2:
                                        f = hoev/100
                                        st.markdown(
                                            f'<div style="font-size:0.7rem;color:#22c55e;padding-top:6px;">'
                                            f'{round((gekozen.get("kcal_100g") or 0)*f)}kcal<br>'
                                            f'{round((gekozen.get("kh_100g") or 0)*f,1)}g KH</div>',
                                            unsafe_allow_html=True)

                                    if st.button("➕ Toevoegen",
                                                 key=f"add_{dag_str}_{mi}",
                                                 use_container_width=True):
                                        if _sla_dagboek_item(user_id, dag_str, mi, gekozen, hoev):
                                            _invalideer_dagboek_cache(dag_str)
                                            for k in [f"zoek_{dag_str}_{mi}", f"pk_{dag_str}_{mi}"]:
                                                st.session_state.pop(k, None)
                                            st.rerun()
                        elif zoek:
                            st.markdown(
                                f'<div style="font-size:0.75rem;color:#64748b;">'
                                f'Geen producten gevonden voor "{zoek}".</div>',
                                unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # Scheidingslijn tussen dagen
        st.markdown('<hr style="border-color:#1e293b;margin:4px 0 12px;">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 5 — VOEDINGSDAGBOEK
# ═══════════════════════════════════════════════════════════════════════════════

DAGEN_NL_DB = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

VOEDING_OPTIES   = ["Volledig", "Gedeeltelijk", "Niet"]
TRAINING_OPTIES  = ["Vlot", "Matig", "Slecht"]
HRV_OPTIES       = ["Hoog", "Gemiddeld", "Laag"]
KWALITEIT_OPTIES = ["Goed", "Matig", "Slecht"]
SPIERPIJN_OPTIES = ["Geen", "Licht", "Zwaar"]
STRESS_OPTIES    = ["Laag", "Matig", "Hoog"]

KLEUR_MAP = {
    "Volledig": "#22c55e", "Gedeeltelijk": "#fbbf24", "Niet": "#ef4444",
    "Vlot": "#22c55e",     "Matig": "#fbbf24",        "Slecht": "#ef4444",
    "Hoog": "#22c55e",     "Gemiddeld": "#fbbf24",    "Laag": "#ef4444",
    "Goed": "#22c55e",     "Geen": "#22c55e",
    "Licht": "#fbbf24",    "Zwaar": "#ef4444",
    "Laag": "#22c55e",     "Hoog": "#ef4444",
}

def _laad_welzijn_week(user_id: str, maandag: object) -> dict:
    """Laad alle welzijn entries voor de week in één query."""
    from datetime import timedelta as _td
    try:
        zondag = str(maandag + _td(days=6))
        r = _get_supabase().table("fuelc_dagboek_welzijn").select("*")\
            .eq("user_id", user_id)\
            .gte("datum", str(maandag))\
            .lte("datum", zondag)\
            .execute()
        return {row["datum"]: row for row in (r.data or [])}
    except: return {}

def _sla_welzijn_op(user_id: str, datum: str, data: dict) -> bool:
    try:
        sb = _get_supabase()
        data["user_id"] = user_id
        data["datum"]   = datum
        bestaand = sb.table("fuelc_dagboek_welzijn").select("id")\
            .eq("user_id", user_id).eq("datum", datum).execute()
        if bestaand.data:
            sb.table("fuelc_dagboek_welzijn").update(data)\
                .eq("user_id", user_id).eq("datum", datum).execute()
        else:
            sb.table("fuelc_dagboek_welzijn").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False

def _chip(label: str, kleur: str) -> str:
    return (
        f'<span style="background:{kleur}22;color:{kleur};border:1px solid {kleur}44;'
        f'border-radius:4px;padding:2px 8px;font-size:0.7rem;font-weight:700;">'
        f'{label}</span>'
    )

def _radio_kleur(label: str, opties: list, key: str, huidig: str = None) -> str:
    """Radio als gekleurde knoppen."""
    idx = opties.index(huidig) if huidig and huidig in opties else 0
    return st.radio(label, opties, index=idx, horizontal=True, key=key)


def _render_voedingsdagboek(user: dict):
    from datetime import date as _date, timedelta as _td

    user_id = user.get("id", "")
    profiel = st.session_state.get("fc_profiel", {})

    _sectie("VOEDINGSDAGBOEK", "#22c55e")

    wi1, wi2 = st.columns([2,3])
    with wi1:
        week_ref = st.date_input("Week van", value=_date.today(), key="db_week_start")
        maandag  = week_ref - _td(days=week_ref.weekday())
    with wi2:
        st.markdown(
            f'<div style="padding-top:26px;font-size:0.8rem;color:#64748b;">'
            f'{maandag.strftime("%d/%m")} — {(maandag+_td(days=6)).strftime("%d/%m/%Y")}</div>',
            unsafe_allow_html=True)

    welzijn_week  = _laad_welzijn_week(user_id, maandag)
    schema_week   = {}
    for _d in range(7):
        _dd = str(maandag + _td(days=_d))
        _s  = _laad_dagschema(user_id, _dd)
        if _s: schema_week[_dd] = _s

    # Week overzicht chips
    chips_html = '<div style="display:flex;gap:6px;margin:8px 0 16px;flex-wrap:wrap;">'
    for _d in range(7):
        _dd     = str(maandag + _td(days=_d))
        _naam   = DAGEN_NL_DB[_d][:2]
        _num    = (maandag + _td(days=_d)).strftime("%d")
        _w      = welzijn_week.get(_dd, {})
        _vg     = _w.get("voeding_gevolgd","")
        _kleur  = KLEUR_MAP.get(_vg, "#334155")
        _vd     = _dd == str(_date.today())
        chips_html += (
            f'<div style="text-align:center;background:#1e293b;border-radius:8px;' +
            f'padding:6px 10px;border:2px solid {_kleur};">' +
            f'<div style="font-size:0.65rem;color:#64748b;">{_naam}</div>' +
            f'<div style="font-size:0.85rem;font-weight:800;color:#f8fafc;">{_num}</div>' +
            ('<div style="font-size:0.55rem;color:#f97316;font-weight:700;">VANDAAG</div>' if _vd else '') +
            '</div>'
        )
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    for d in range(7):
        dag_datum  = maandag + _td(days=d)
        dag_str    = str(dag_datum)
        dag_naam   = DAGEN_NL_DB[d]
        dag_label  = f"{dag_naam} {dag_datum.strftime('%d/%m')}"
        is_vandaag = dag_datum == _date.today()
        is_toekomst = dag_datum > _date.today()

        welzijn    = welzijn_week.get(dag_str, {})
        schema_dag = schema_week.get(dag_str, {})
        heeft_training = schema_dag.get("training_timing","Geen training") != "Geen training"
        ingevuld   = bool(welzijn)

        if is_toekomst:   border = "#1e293b"
        elif ingevuld:    border = "#22c55e"
        else:             border = "#f97316" if is_vandaag else "#334155"

        dh1, dh2 = st.columns([4,1])
        with dh1:
            chips = ""
            if welzijn.get("voeding_gevolgd"):
                chips += _chip(welzijn["voeding_gevolgd"], KLEUR_MAP.get(welzijn["voeding_gevolgd"],"#64748b")) + " "
            if welzijn.get("training_gevoel") and heeft_training:
                chips += _chip(welzijn["training_gevoel"], KLEUR_MAP.get(welzijn["training_gevoel"],"#64748b")) + " "
            if welzijn.get("hrv"):
                chips += _chip(f"HRV {welzijn['hrv']}", KLEUR_MAP.get(welzijn["hrv"],"#64748b"))
            st.markdown(
                f'<div style="padding:6px 0;">' +
                f'<span style="font-size:0.9rem;font-weight:800;color:#f8fafc;">{dag_label}</span>' +
                ('<span style="background:#f97316;color:white;border-radius:4px;font-size:0.6rem;' +
                 'font-weight:700;padding:1px 6px;margin-left:8px;">VANDAAG</span>' if is_vandaag else "") +
                ('<span style="color:#475569;font-size:0.75rem;margin-left:8px;">— nog niet beschikbaar</span>' if is_toekomst else "") +
                f'</div><div style="margin-top:2px;">{chips}</div>',
                unsafe_allow_html=True)
        with dh2:
            if not is_toekomst:
                dag_open_key = f"db_open_{dag_str}"
                lbl = "▲ Dicht" if st.session_state.get(dag_open_key) else "▼ Invullen"
                if st.button(lbl, key=f"db_toggle_{dag_str}", use_container_width=True):
                    st.session_state[dag_open_key] = not st.session_state.get(dag_open_key, False)
                    st.rerun()

        if not is_toekomst and st.session_state.get(f"db_open_{dag_str}", False):
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;border-left:3px solid {border};' +
                f'padding:14px;margin-bottom:4px;">',
                unsafe_allow_html=True)

            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin-bottom:8px;">🥦 VOEDING</div>', unsafe_allow_html=True)
            vg_val = _radio_kleur("Voedingsschema gevolgd", VOEDING_OPTIES, f"db_vg_{dag_str}", welzijn.get("voeding_gevolgd"))

            tr_val = None
            if heeft_training:
                st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">🏃 TRAINING</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:6px;">{schema_dag.get("training_timing","")}</div>', unsafe_allow_html=True)
                tr_val = _radio_kleur("Hoe verliep de training", TRAINING_OPTIES, f"db_tr_{dag_str}", welzijn.get("training_gevoel"))

            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">💚 HERSTEL & WELZIJN</div>', unsafe_allow_html=True)
            rc1, rc2 = st.columns(2)
            with rc1:
                hrv_val      = _radio_kleur("HRV", HRV_OPTIES, f"db_hrv_{dag_str}", welzijn.get("hrv"))
                fris_val     = _radio_kleur("Frisheid", KWALITEIT_OPTIES, f"db_fris_{dag_str}", welzijn.get("frisheid"))
                spierpijn_val= _radio_kleur("Spierpijn", SPIERPIJN_OPTIES, f"db_sp_{dag_str}", welzijn.get("spierpijn"))
            with rc2:
                slaap_kwal_val = _radio_kleur("Slaapkwaliteit", KWALITEIT_OPTIES, f"db_sk_{dag_str}", welzijn.get("slaap_kwaliteit"))
                stress_val     = _radio_kleur("Stress", STRESS_OPTIES, f"db_stress_{dag_str}", welzijn.get("stress"))

            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">📊 METINGEN</div>', unsafe_allow_html=True)
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                slaap_val = st.number_input("Slaap (uur)", 0.0, 14.0, float(welzijn.get("slaap_uur") or 7.5), 0.5, key=f"db_slaap_{dag_str}")
            with mc2:
                rhr_val   = st.number_input("Rusthartslag (bpm)", 0, 120, int(welzijn.get("rusthartslag") or 0), 1, key=f"db_rhr_{dag_str}")
            with mc3:
                water_val = st.number_input("Water (liter)", 0.0, 8.0, float(welzijn.get("waterinname_l") or 0.0), 0.25, key=f"db_water_{dag_str}")

            gewicht_val = welzijn.get("gewicht_kg")
            if dag_datum.weekday() == 3:
                st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">⚖️ GEWICHT (wekelijks)</div>', unsafe_allow_html=True)
                gw1, _ = st.columns([1,2])
                with gw1:
                    gewicht_val = st.number_input("Gewicht (kg)", 30.0, 200.0,
                        float(welzijn.get("gewicht_kg") or float(profiel.get("gewicht_kg") or 70)),
                        0.1, key=f"db_gew_{dag_str}")

            notitie_val = st.text_input("Notitie (optioneel)",
                value=welzijn.get("notitie",""),
                placeholder="bijv. zware benen, slecht geslapen...",
                key=f"db_notitie_{dag_str}", label_visibility="collapsed")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Opslaan", key=f"db_ops_{dag_str}", use_container_width=True):
                data = {
                    "voeding_gevolgd":  vg_val,
                    "training_gevoel":  tr_val,
                    "hrv":              hrv_val,
                    "slaap_uur":        slaap_val if slaap_val > 0 else None,
                    "slaap_kwaliteit":  slaap_kwal_val,
                    "frisheid":         fris_val,
                    "rusthartslag":     rhr_val if rhr_val > 0 else None,
                    "spierpijn":        spierpijn_val,
                    "stress":           stress_val,
                    "waterinname_l":    water_val if water_val > 0 else None,
                    "gewicht_kg":       gewicht_val if dag_datum.weekday()==0 and gewicht_val else None,
                    "notitie":          notitie_val if notitie_val else None,
                }
                if _sla_welzijn_op(user_id, dag_str, data):
                    welzijn_week[dag_str] = {**data, "datum": dag_str}
                    st.success("✅ Opgeslagen!")
                    st.session_state[f"db_open_{dag_str}"] = False
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e293b;margin:4px 0 10px;">', unsafe_allow_html=True)

def _render_analyses(user: dict):
    import json as _json
    from datetime import date as _date, timedelta as _td

    user_id = user.get("id", "")
    profiel = st.session_state.get("fc_profiel", {})
    gewicht_prof = float(profiel.get("gewicht_kg") or 70)
    lengte_prof  = float(profiel.get("lengte_cm") or 175)
    energie_doel = int(profiel.get("energie_doel") or 2000)

    _sectie("ANALYSES", "#22c55e")

    # ── Periode selector ──────────────────────────────────────────────────────
    pc1, pc2 = st.columns([2,3])
    with pc1:
        periode = st.selectbox("Periode", ["Laatste 7 dagen","Laatste 30 dagen","Laatste 90 dagen"],
            key="dash_periode")
    dagen = {"Laatste 7 dagen":7,"Laatste 30 dagen":30,"Laatste 90 dagen":90}[periode]
    vandaag  = _date.today()
    startdag = vandaag - _td(days=dagen-1)

    # ── Data laden ────────────────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def _laad_welzijn_periode(uid, start, einde):
        try:
            r = _get_supabase().table("fuelc_dagboek_welzijn").select("*")\
                .eq("user_id",uid).gte("datum",str(start)).lte("datum",str(einde))\
                .order("datum").execute()
            return r.data or []
        except: return []

    @st.cache_data(ttl=300)
    def _laad_dagboek_periode(uid, start, einde):
        try:
            r = _get_supabase().table("fuelc_dagboek").select("*")\
                .eq("user_id",uid).gte("datum",str(start)).lte("datum",str(einde))\
                .order("datum").execute()
            return r.data or []
        except: return []

    @st.cache_data(ttl=300)
    def _laad_dagschemas_periode(uid, start, einde):
        try:
            r = _get_supabase().table("fuelc_dagschema").select("*")\
                .eq("user_id",uid).gte("datum",str(start)).lte("datum",str(einde))\
                .order("datum").execute()
            return r.data or []
        except: return []

    welzijn_data   = _laad_welzijn_periode(user_id, startdag, vandaag)
    dagboek_items  = _laad_dagboek_periode(user_id, startdag, vandaag)
    dagschemas     = _laad_dagschemas_periode(user_id, startdag, vandaag)

    # Bouw dagelijkse samenvattingen
    dag_dict = {}
    for d in range(dagen):
        dag = str(startdag + _td(days=d))
        dag_dict[dag] = {"datum":dag,"kcal":0,"kh":0,"eiwit":0,"vet":0,
                         "verz":0,"suikers":0,"vezels":0,"natrium":0,
                         "water":0,"items":[]}

    # Voeg bibliotheekdata toe voor verzadigd/onverzadigd vet, suikers etc
    bib_cache = {}
    try:
        bib_r = _get_supabase().table("fuelc_bibliotheek").select(
            "id,naam,categorie,kcal_100g,kh_100g,eiwit_100g,vet_100g,"
            "verzadigd_100g,suikers_100g,vezels_100g,natrium_100g,gi"
        ).eq("user_id",user_id).execute()
        for p in (bib_r.data or []):
            bib_cache[p["id"]] = p
    except: pass

    for item in dagboek_items:
        dag = item.get("datum","")[:10]
        if dag not in dag_dict: continue
        hg = float(item.get("hoeveelheid_g") or 0) / 100
        prod = bib_cache.get(item.get("product_id",""), {})
        dag_dict[dag]["kcal"]    += float(item.get("kcal") or 0)
        dag_dict[dag]["kh"]      += float(item.get("kh_g") or 0)
        dag_dict[dag]["eiwit"]   += float(item.get("eiwit_g") or 0)
        dag_dict[dag]["vet"]     += float(item.get("vet_g") or 0)
        dag_dict[dag]["verz"]    += float(prod.get("verzadigd_100g") or 0) * hg
        dag_dict[dag]["suikers"] += float(prod.get("suikers_100g") or 0) * hg
        dag_dict[dag]["vezels"]  += float(prod.get("vezels_100g") or 0) * hg
        dag_dict[dag]["natrium"] += float(prod.get("natrium_100g") or 0) * hg
        dag_dict[dag]["items"].append({**item, "prod": prod})

    for w in welzijn_data:
        dag = w.get("datum","")[:10]
        if dag in dag_dict:
            dag_dict[dag].update({
                "hrv":         w.get("hrv",""),
                "slaap":       float(w.get("slaap_uur") or 0),
                "slaap_kwal":  w.get("slaap_kwaliteit",""),
                "frisheid":    w.get("frisheid",""),
                "rhr":         int(w.get("rusthartslag") or 0),
                "spierpijn":   w.get("spierpijn",""),
                "stress":      w.get("stress",""),
                "water":       float(w.get("waterinname_l") or 0),
                "gewicht":     float(w.get("gewicht_kg") or 0),
                "voeding_gev": w.get("voeding_gevolgd",""),
            })

    dagen_lijst       = sorted(dag_dict.values(), key=lambda x: x["datum"])
    dagen_met_data    = [d for d in dagen_lijst if d["kcal"] > 0]
    dagen_met_welzijn = [d for d in dagen_lijst if d.get("voeding_gev") or d.get("hrv") or d.get("slaap",0) > 0]

    def _kleur_balk(waarde, doel, kleur="#22c55e"):
        pct = min(100, round(waarde/doel*100)) if doel > 0 else 0
        over = waarde > doel * 1.1
        k = "#ef4444" if over else kleur
        return (f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<div style="flex:1;background:#1e293b;border-radius:3px;height:6px;">'
                f'<div style="width:{pct}%;height:100%;background:{k};border-radius:3px;"></div></div>'
                f'<span style="font-size:0.7rem;color:{k};width:40px;">{round(waarde)}</span></div>')

    # ═══════════════════════════════════════════════════════════════════════
    # 🎯 WEEKSCORE
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:16px 0 8px;">🎯 WEEKSCORE</div>', unsafe_allow_html=True)

    if dagen_met_data:
        n_w = max(len(dagen_met_welzijn), 1)
        n_d = max(len(dagen_met_data), 1)
        # Voeding gevolgd: enkel tellen als NIET "Volledig" ook telt
        score_voeding = round(sum(
            {"Volledig":100,"Gedeeltelijk":50,"Niet":0}.get(d.get("voeding_gev",""),0)
            for d in dagen_met_welzijn) / n_w) if dagen_met_welzijn else 0
        # Slaap: >= 7u = goed, 6-7 = matig, <6 = slecht
        score_slaap = round(sum(
            100 if d.get("slaap",0) >= 7 else (50 if d.get("slaap",0) >= 6 else 0)
            for d in dagen_met_welzijn if d.get("slaap",0) > 0) /
            max(len([d for d in dagen_met_welzijn if d.get("slaap",0) > 0]),1)) if dagen_met_welzijn else 0
        # HRV: Hoog=100, Gemiddeld=60, Laag=20
        score_hrv = round(sum(
            {"Hoog":100,"Gemiddeld":60,"Laag":20}.get(d.get("hrv",""),0)
            for d in dagen_met_welzijn if d.get("hrv")) /
            max(len([d for d in dagen_met_welzijn if d.get("hrv")]),1)) if dagen_met_welzijn else 0
        # Stress: Laag=100, Matig=60, Hoog=20
        score_stress = round(sum(
            {"Laag":100,"Matig":60,"Hoog":20}.get(d.get("stress",""),0)
            for d in dagen_met_welzijn if d.get("stress")) /
            max(len([d for d in dagen_met_welzijn if d.get("stress")]),1)) if dagen_met_welzijn else 0
        # Kcal: binnen 15% van doel = goed
        score_kcal = round(sum(
            100 if energie_doel > 0 and abs(d["kcal"] - energie_doel) / energie_doel < 0.15 else
            (50 if energie_doel > 0 and abs(d["kcal"] - energie_doel) / energie_doel < 0.30 else 0)
            for d in dagen_met_data) / n_d) if dagen_met_data else 0
        totaal_score  = round(score_voeding*0.3 + score_slaap*0.2 + score_hrv*0.2 + score_stress*0.15 + score_kcal*0.15)
        score_kleur   = "#22c55e" if totaal_score >= 70 else ("#fbbf24" if totaal_score >= 50 else "#ef4444")

        st.markdown(
            f'<div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:12px;">'
            f'<div style="display:flex;align-items:center;gap:20px;">'
            f'<div style="text-align:center;">'
            f'<div style="font-size:2.5rem;font-weight:900;color:{score_kleur};">{totaal_score}</div>'
            f'<div style="font-size:0.65rem;color:#64748b;">/ 100</div></div>'
            f'<div style="flex:1;">'
            f'<div style="font-size:0.7rem;color:#64748b;margin-bottom:4px;">Voeding gevolgd</div>'
            f'{_kleur_balk(score_voeding,100,"#f97316")}'
            f'<div style="font-size:0.7rem;color:#64748b;margin:4px 0;">Slaap ≥ 7u</div>'
            f'{_kleur_balk(score_slaap,100,"#3b82f6")}'
            f'<div style="font-size:0.7rem;color:#64748b;margin:4px 0;">HRV goed</div>'
            f'{_kleur_balk(score_hrv,100,"#22c55e")}'
            f'<div style="font-size:0.7rem;color:#64748b;margin:4px 0;">Stress OK</div>'
            f'{_kleur_balk(score_stress,100,"#8b5cf6")}'
            f'<div style="font-size:0.7rem;color:#64748b;margin:4px 0;">Energie op doel</div>'
            f'{_kleur_balk(score_kcal,100,"#fbbf24")}'
            f'</div></div></div>',
            unsafe_allow_html=True)
    else:
        st.info("Vul het voedingsdagboek in om je weekscore te zien.")

    # ═══════════════════════════════════════════════════════════════════════
    # ⚖️ GEWICHT & BMI
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">⚖️ GEWICHT & BMI</div>', unsafe_allow_html=True)

    gewicht_punten = [(d["datum"], d["gewicht"]) for d in dagen_lijst if d.get("gewicht",0) > 0]

    if len(gewicht_punten) >= 1:
        laatste_gew = gewicht_punten[-1][1]
        bmi         = round(laatste_gew / ((lengte_prof/100)**2), 1) if lengte_prof > 0 else 0
        bmi_cat     = "Ondergewicht" if bmi < 18.5 else ("Normaal" if bmi < 25 else ("Overgewicht" if bmi < 30 else "Obesitas"))
        bmi_kleur   = "#22c55e" if bmi < 25 else ("#fbbf24" if bmi < 30 else "#ef4444")

        # Metrics rij
        gm1, gm2, gm3, gm4 = st.columns(4)
        with gm1:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                f'<div style="font-size:0.6rem;color:#64748b;">HUIDIG GEWICHT</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:#f8fafc;">{laatste_gew}kg</div></div>',
                unsafe_allow_html=True)
        with gm2:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                f'<div style="font-size:0.6rem;color:#64748b;">BMI</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:{bmi_kleur};">{bmi}</div>' +
                f'<div style="font-size:0.65rem;color:{bmi_kleur};">{bmi_cat}</div></div>',
                unsafe_allow_html=True)
        with gm3:
            if len(gewicht_punten) >= 2:
                trend = gewicht_punten[-1][1] - gewicht_punten[0][1]
                trend_tekst = f"▲ +{round(trend,1)}kg" if trend > 0.1 else (f"▼ {round(trend,1)}kg" if trend < -0.1 else "→ Stabiel")
                trend_kleur = "#ef4444" if trend > 0.5 else ("#22c55e" if trend < -0.5 else "#fbbf24")
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">TREND</div>' +
                    f'<div style="font-size:0.9rem;font-weight:800;color:{trend_kleur};">{trend_tekst}</div>' +
                    f'<div style="font-size:0.65rem;color:#64748b;">{len(gewicht_punten)} metingen</div></div>',
                    unsafe_allow_html=True)
        with gm4:
            if len(gewicht_punten) >= 2:
                gem_gew = round(sum(p[1] for p in gewicht_punten) / len(gewicht_punten), 1)
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">' +
                    f'<div style="font-size:0.6rem;color:#64748b;">GEMIDDELD</div>' +
                    f'<div style="font-size:1.1rem;font-weight:800;color:#f8fafc;">{gem_gew}kg</div></div>',
                    unsafe_allow_html=True)

        # Gewicht grafiek
        if len(gewicht_punten) >= 2:
            st.markdown('<div style="font-size:0.7rem;color:#64748b;margin:10px 0 4px;">Gewichtsevolutie</div>', unsafe_allow_html=True)
            max_gew = max(p[1] for p in gewicht_punten)
            min_gew = min(p[1] for p in gewicht_punten)
            spread  = max_gew - min_gew or 1
            grafiek = '<div style="display:flex;align-items:flex-end;gap:4px;height:80px;margin-bottom:4px;">'
            for datum, gew in gewicht_punten:
                h = round(((gew - min_gew) / spread) * 65) + 10
                k = "#ef4444" if gew > gewicht_punten[0][1] + 0.5 else ("#22c55e" if gew < gewicht_punten[0][1] - 0.5 else "#fbbf24")
                grafiek += (
                    f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;">' +
                    f'<div style="font-size:0.6rem;color:#f8fafc;margin-bottom:2px;">{gew}</div>' +
                    f'<div style="width:100%;background:{k};border-radius:3px 3px 0 0;height:{h}px;"></div>' +
                    f'<div style="font-size:0.5rem;color:#475569;margin-top:2px;">{datum[8:]}/{datum[5:7]}</div></div>'
                )
            grafiek += '</div>'
            st.markdown(grafiek, unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:0.7rem;color:#64748b;">Gewicht wordt elke donderdag ingevoerd in het Dagboek.</div>',
                unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#1e293b;border-radius:8px;padding:12px;color:#64748b;font-size:0.8rem;">' +
            '⚖️ Nog geen gewichtsdata. Vul je gewicht in via het Dagboek (elke donderdag).</div>',
            unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════════════════════
    # ⚡ ENERGIE & MACRO'S
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">⚡ ENERGIE & MACRO\'S</div>', unsafe_allow_html=True)

    if dagen_met_data:
        gem_kcal  = round(sum(d["kcal"] for d in dagen_met_data) / len(dagen_met_data))
        gem_kh    = round(sum(d["kh"] for d in dagen_met_data) / len(dagen_met_data))
        gem_eiwit = round(sum(d["eiwit"] for d in dagen_met_data) / len(dagen_met_data))
        gem_vet   = round(sum(d["vet"] for d in dagen_met_data) / len(dagen_met_data))

        em1,em2,em3,em4 = st.columns(4)
        for col, label, val, doel, kleur in [
            (em1,"KCAL gem/dag",gem_kcal,energie_doel,"#22c55e"),
            (em2,"KH gem/dag (g)",gem_kh,round(energie_doel*0.5/4),"#f97316"),
            (em3,"EIWIT gem/dag (g)",gem_eiwit,round(energie_doel*0.25/4),"#3b82f6"),
            (em4,"VET gem/dag (g)",gem_vet,round(energie_doel*0.25/9),"#8b5cf6"),
        ]:
            pct = min(100, round(val/doel*100)) if doel > 0 else 0
            over = val > doel*1.1
            k = "#ef4444" if over else kleur
            with col:
                st.markdown(
                    f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                    f'<div style="font-size:0.6rem;color:#64748b;">{label}</div>'
                    f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{val}</div>'
                    f'<div style="font-size:0.65rem;color:#475569;">doel: {doel}</div>'
                    f'<div style="background:#0f172a;border-radius:3px;height:4px;margin-top:4px;">'
                    f'<div style="width:{pct}%;height:100%;background:{k};border-radius:3px;"></div>'
                    f'</div></div>',
                    unsafe_allow_html=True)

        # Kcal per dag balkgrafiek
        st.markdown('<div style="font-size:0.7rem;color:#64748b;margin:12px 0 4px;">Kcal per dag vs doel</div>', unsafe_allow_html=True)
        grafiek = '<div style="display:flex;align-items:flex-end;gap:2px;height:60px;">'
        max_kcal = max(d["kcal"] for d in dagen_lijst) or energie_doel
        for d in dagen_lijst[-14:]:
            h = round((d["kcal"] / max(max_kcal, energie_doel)) * 55) if d["kcal"] > 0 else 2
            over = d["kcal"] > energie_doel * 1.1
            k = "#ef4444" if over else ("#22c55e" if d["kcal"] > energie_doel*0.85 else "#334155")
            grafiek += (f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;">'
                       f'<div style="width:100%;background:{k};border-radius:2px 2px 0 0;height:{h}px;"></div>'
                       f'<div style="font-size:0.5rem;color:#475569;">{d["datum"][8:]}</div></div>')
        grafiek += '</div>'
        st.markdown(grafiek, unsafe_allow_html=True)
    else:
        st.info("Voeg maaltijden toe in het weekschema om data te zien.")

    # ═══════════════════════════════════════════════════════════════════════
    # 🍬 SUIKERS, GI & VEZELS
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">🍬 SUIKERS, GI & VEZELS</div>', unsafe_allow_html=True)

    if dagen_met_data:
        gem_suikers = round(sum(d["suikers"] for d in dagen_met_data) / len(dagen_met_data), 1)
        gem_vezels  = round(sum(d["vezels"] for d in dagen_met_data) / len(dagen_met_data), 1)
        suiker_doel = 50  # WHO aanbeveling: max 50g toegevoegde suikers/dag
        vezel_doel  = 30  # aanbeveling: 30g/dag

        sg1, sg2, sg3 = st.columns(3)
        with sg1:
            k = "#ef4444" if gem_suikers > suiker_doel else "#22c55e"
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">SUIKERS gem/dag</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{gem_suikers}g</div>'
                f'<div style="font-size:0.65rem;color:#475569;">max {suiker_doel}g (WHO)</div></div>',
                unsafe_allow_html=True)
        with sg2:
            k = "#22c55e" if gem_vezels >= vezel_doel else "#fbbf24"
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">VEZELS gem/dag</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{gem_vezels}g</div>'
                f'<div style="font-size:0.65rem;color:#475569;">doel: {vezel_doel}g</div></div>',
                unsafe_allow_html=True)

        # GI analyse
        with sg3:
            hoog_gi_items = []
            for d in dagen_met_data:
                for item in d.get("items",[]):
                    gi = item.get("prod",{}).get("gi")
                    if gi and gi >= 70:
                        hoog_gi_items.append({"naam":item.get("naam",""),"gi":gi,"datum":d["datum"]})
            gi_pct = round(len(hoog_gi_items) / max(sum(len(d.get("items",[])) for d in dagen_met_data),1) * 100)
            k = "#ef4444" if gi_pct > 30 else ("#fbbf24" if gi_pct > 15 else "#22c55e")
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">HOOG GI producten</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{gi_pct}%</div>'
                f'<div style="font-size:0.65rem;color:#475569;">van alle producten</div></div>',
                unsafe_allow_html=True)

        if hoog_gi_items:
            st.markdown(
                '<div style="font-size:0.72rem;color:#ef4444;margin:8px 0 4px;">⚠️ Hoog GI producten deze periode:</div>',
                unsafe_allow_html=True)
            uniek = {}
            for item in hoog_gi_items:
                uniek[item["naam"]] = item["gi"]
            chips = "".join([
                f'<span style="background:#ef444422;color:#ef4444;border:1px solid #ef444444;'
                f'border-radius:4px;padding:2px 8px;font-size:0.7rem;margin:2px;">'
                f'{naam} (GI {gi})</span>'
                for naam, gi in list(uniek.items())[:8]
            ])
            st.markdown(f'<div style="margin-bottom:8px;">{chips}</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="background:#1e293b;border-radius:8px;padding:10px;font-size:0.78rem;color:#94a3b8;">'
                '💡 Hoge GI producten veroorzaken snelle bloedsuikerstijging → energiedip na 2-3u, '
                'verstoring slaap en lagere HRV. Wissel af met lage GI alternatieven (havermout, volkoren, peulvruchten).'
                '</div>',
                unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 🧈 VETTEN
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">🧈 VETTEN</div>', unsafe_allow_html=True)

    if dagen_met_data:
        gem_vet_tot  = round(sum(d["vet"] for d in dagen_met_data) / len(dagen_met_data), 1)
        gem_verz     = round(sum(d["verz"] for d in dagen_met_data) / len(dagen_met_data), 1)
        gem_onverz   = round(gem_vet_tot - gem_verz, 1)
        verz_doel    = round(energie_doel * 0.10 / 9)  # max 10% energie uit verzadigd vet
        onverz_doel  = round(energie_doel * 0.20 / 9)

        vt1, vt2, vt3 = st.columns(3)
        with vt1:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">TOTAAL VET gem/dag</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:#8b5cf6;">{gem_vet_tot}g</div></div>',
                unsafe_allow_html=True)
        with vt2:
            k = "#ef4444" if gem_verz > verz_doel else "#22c55e"
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">VERZADIGD gem/dag</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{gem_verz}g</div>'
                f'<div style="font-size:0.65rem;color:#475569;">max {verz_doel}g</div></div>',
                unsafe_allow_html=True)
        with vt3:
            k = "#22c55e" if gem_onverz >= onverz_doel*0.8 else "#fbbf24"
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">ONVERZADIGD gem/dag</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{k};">{gem_onverz}g</div>'
                f'<div style="font-size:0.65rem;color:#475569;">doel: >{onverz_doel}g</div></div>',
                unsafe_allow_html=True)

        # Verhouding balk
        if gem_vet_tot > 0:
            verz_pct  = round(gem_verz / gem_vet_tot * 100)
            onverz_pct = 100 - verz_pct
            st.markdown(
                f'<div style="margin-top:8px;">'
                f'<div style="font-size:0.7rem;color:#64748b;margin-bottom:4px;">Verhouding verzadigd/onverzadigd</div>'
                f'<div style="display:flex;border-radius:6px;overflow:hidden;height:20px;">'
                f'<div style="width:{verz_pct}%;background:#ef4444;display:flex;align-items:center;justify-content:center;">'
                f'<span style="font-size:0.65rem;color:white;font-weight:700;">{verz_pct}% verz.</span></div>'
                f'<div style="width:{onverz_pct}%;background:#22c55e;display:flex;align-items:center;justify-content:center;">'
                f'<span style="font-size:0.65rem;color:white;font-weight:700;">{onverz_pct}% onverz.</span></div>'
                f'</div>'
                f'<div style="font-size:0.7rem;color:#64748b;margin-top:4px;">Aanbeveling: max 1/3 verzadigd</div>'
                f'</div>',
                unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 💧 VOCHT
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">💧 VOCHT</div>', unsafe_allow_html=True)

    water_data = [d for d in dagen_lijst if d.get("water",0) > 0]
    if water_data:
        gem_water = round(sum(d["water"] for d in water_data) / len(water_data), 1)
        water_doel = 2.0
        k = "#22c55e" if gem_water >= water_doel else ("#fbbf24" if gem_water >= 1.5 else "#ef4444")
        wc1, wc2 = st.columns([1,3])
        with wc1:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;">'
                f'<div style="font-size:0.6rem;color:#64748b;">GEM/DAG</div>'
                f'<div style="font-size:1.4rem;font-weight:900;color:{k};">{gem_water}L</div>'
                f'<div style="font-size:0.65rem;color:#475569;">doel: {water_doel}L</div></div>',
                unsafe_allow_html=True)
        with wc2:
            grafiek = '<div style="display:flex;align-items:flex-end;gap:3px;height:50px;">'
            for d in water_data[-14:]:
                h = round((d["water"] / 4.0) * 45) + 5
                k2 = "#3b82f6" if d["water"] >= water_doel else ("#fbbf24" if d["water"] >= 1.5 else "#ef4444")
                grafiek += (f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;">'
                           f'<div style="width:100%;background:{k2};border-radius:2px 2px 0 0;height:{h}px;"></div>'
                           f'<div style="font-size:0.5rem;color:#475569;">{d["datum"][8:]}</div></div>')
            grafiek += '</div>'
            st.markdown(grafiek, unsafe_allow_html=True)
    else:
        st.info("Voer waterinname in via het Dagboek.")

    # ═══════════════════════════════════════════════════════════════════════
    # 🥗 VOEDINGSGROEPEN
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">🥗 VOEDINGSGROEPEN</div>', unsafe_allow_html=True)

    if dagen_met_data:
        groepen = {
            "Groenten & fruit": {"cat":["Groenten","Fruit"],"kleur":"#22c55e","gram":0},
            "Granen":           {"cat":["Granen & brood"],"kleur":"#f97316","gram":0},
            "Vlees & vis":      {"cat":["Vlees & vis"],"kleur":"#ef4444","gram":0},
            "Zuivel":           {"cat":["Zuivel"],"kleur":"#3b82f6","gram":0},
            "Restgroep":        {"cat":["Sauzen & spreads","Snacks","Dranken","Sportvoeding","Overige"],"kleur":"#64748b","gram":0},
        }
        for d in dagen_met_data:
            for item in d.get("items",[]):
                cat = item.get("prod",{}).get("categorie","") or ""
                gram = float(item.get("hoeveelheid_g") or 0)
                for groep, info in groepen.items():
                    if cat in info["cat"]:
                        info["gram"] += gram
                        break

        n_dagen = max(len(dagen_met_data), 1)
        totaal_gram = sum(g["gram"] for g in groepen.values()) or 1

        for groep, info in groepen.items():
            gem_gram = round(info["gram"] / n_dagen)
            pct = round(info["gram"] / totaal_gram * 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                f'<div style="font-size:0.75rem;color:#f8fafc;width:140px;">{groep}</div>'
                f'<div style="flex:1;background:#1e293b;border-radius:3px;height:14px;">'
                f'<div style="width:{pct}%;height:100%;background:{info["kleur"]};border-radius:3px;"></div></div>'
                f'<div style="font-size:0.72rem;color:{info["kleur"]};width:80px;text-align:right;">'
                f'{gem_gram}g/dag ({pct}%)</div></div>',
                unsafe_allow_html=True)

        # Groenten+fruit tip
        gf_gram = round(groepen["Groenten & fruit"]["gram"] / n_dagen)
        if gf_gram < 400:
            st.markdown(
                f'<div style="background:#1e293b;border-left:3px solid #fbbf24;border-radius:0 8px 8px 0;'
                f'padding:8px 12px;font-size:0.78rem;color:#94a3b8;margin-top:8px;">'
                f'⚠️ Gemiddeld {gf_gram}g groenten & fruit per dag — aanbeveling is 400g+. '
                f'Meer variatie in groenten en fruit verbetert darmflora, HRV en herstel.</div>',
                unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 🌿 PLANTAARDIG / DIERLIJK
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">🌿 PLANTAARDIG / DIERLIJK</div>', unsafe_allow_html=True)

    if dagen_met_data:
        plantaardig_cat = ["Groenten","Fruit","Granen & brood","Sauzen & spreads","Snacks"]
        dierlijk_cat    = ["Vlees & vis","Zuivel"]
        pl_gram = 0
        di_gram = 0
        for d in dagen_met_data:
            for item in d.get("items",[]):
                cat  = item.get("prod",{}).get("categorie","") or ""
                gram = float(item.get("hoeveelheid_g") or 0)
                if cat in plantaardig_cat: pl_gram += gram
                elif cat in dierlijk_cat:  di_gram += gram

        totaal_pd = pl_gram + di_gram or 1
        pl_pct    = round(pl_gram / totaal_pd * 100)
        di_pct    = 100 - pl_pct
        n_dagen   = max(len(dagen_met_data),1)

        st.markdown(
            f'<div style="background:#1e293b;border-radius:10px;padding:14px;margin-bottom:8px;">'
            f'<div style="display:flex;gap:20px;margin-bottom:10px;">'
            f'<div><div style="font-size:0.6rem;color:#64748b;">PLANTAARDIG</div>'
            f'<div style="font-size:1.2rem;font-weight:800;color:#22c55e;">{pl_pct}%</div>'
            f'<div style="font-size:0.7rem;color:#64748b;">{round(pl_gram/n_dagen)}g/dag</div></div>'
            f'<div><div style="font-size:0.6rem;color:#64748b;">DIERLIJK</div>'
            f'<div style="font-size:1.2rem;font-weight:800;color:#f97316;">{di_pct}%</div>'
            f'<div style="font-size:0.7rem;color:#64748b;">{round(di_gram/n_dagen)}g/dag</div></div>'
            f'<div style="flex:1;display:flex;align-items:center;">'
            f'<div style="width:100%;">'
            f'<div style="display:flex;border-radius:6px;overflow:hidden;height:24px;">'
            f'<div style="width:{pl_pct}%;background:#22c55e;"></div>'
            f'<div style="width:{di_pct}%;background:#f97316;"></div>'
            f'</div>'
            f'<div style="font-size:0.65rem;color:#64748b;margin-top:4px;">Aanbeveling: 60-70% plantaardig</div>'
            f'</div></div></div></div>',
            unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 💚 HERSTELCORRELATIES
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:2px;margin:20px 0 8px;">💚 HERSTELCORRELATIES</div>', unsafe_allow_html=True)

    def _correlatie_kaart(titel, bevinding, kleur, uitleg):
        st.markdown(
            f'<div style="background:#1e293b;border-left:3px solid {kleur};border-radius:0 10px 10px 0;'
            f'padding:12px 14px;margin-bottom:8px;">'
            f'<div style="font-size:0.75rem;font-weight:700;color:#f8fafc;margin-bottom:4px;">{titel}</div>'
            f'<div style="font-size:0.85rem;font-weight:800;color:{kleur};margin-bottom:4px;">{bevinding}</div>'
            f'<div style="font-size:0.72rem;color:#64748b;">{uitleg}</div>'
            f'</div>',
            unsafe_allow_html=True)

    if len(dagen_met_data) >= 3:
        # Slaap ↔ HRV volgende dag
        slaap_hrv_pairs = []
        for i, d in enumerate(dagen_lijst[:-1]):
            volgende = dagen_lijst[i+1]
            if d.get("slaap",0) > 0 and volgende.get("hrv"):
                slaap_hrv_pairs.append((d["slaap"], volgende["hrv"]))
        if slaap_hrv_pairs:
            gem_slaap_hoog_hrv = [s for s,h in slaap_hrv_pairs if h=="Hoog"]
            gem_slaap_laag_hrv = [s for s,h in slaap_hrv_pairs if h=="Laag"]
            if gem_slaap_hoog_hrv and gem_slaap_laag_hrv:
                diff = round(sum(gem_slaap_hoog_hrv)/len(gem_slaap_hoog_hrv) - sum(gem_slaap_laag_hrv)/len(gem_slaap_laag_hrv), 1)
                kleur = "#22c55e" if diff > 0 else "#fbbf24"
                bevinding = f"Bij hoge HRV sliep je gemiddeld {abs(diff)}u {'meer' if diff > 0 else 'minder'}"
                _correlatie_kaart("😴 Slaap → HRV volgende ochtend", bevinding, kleur,
                    "Meer slaap = hogere HRV de volgende dag. Slaap is de sterkste voorspeller van hartslagvariabiliteit.")

        # KH-inname ↔ HRV
        kh_hrv = [(d["kh"], d.get("hrv","")) for d in dagen_met_data if d.get("hrv")]
        if len(kh_hrv) >= 3:
            kh_hoog = [k for k,h in kh_hrv if h=="Hoog"]
            kh_laag = [k for k,h in kh_hrv if h=="Laag"]
            if kh_hoog and kh_laag:
                diff = round(sum(kh_hoog)/len(kh_hoog) - sum(kh_laag)/len(kh_laag))
                kleur = "#22c55e" if diff > 10 else "#fbbf24"
                bevinding = f"Op hoge HRV dagen at je {abs(diff)}g KH {'meer' if diff > 0 else 'minder'}"
                _correlatie_kaart("🍞 KH-inname → HRV", bevinding, kleur,
                    "Voldoende koolhydraten vullen glycogeen aan. Lage KH = hoger cortisol = lagere HRV.")

        # Suikers ↔ slaapkwaliteit
        suiker_slaap = [(d["suikers"], d.get("slaap_kwal","")) for d in dagen_met_data if d.get("slaap_kwal")]
        if len(suiker_slaap) >= 3:
            s_goed = [s for s,sk in suiker_slaap if sk=="Goed"]
            s_slecht = [s for s,sk in suiker_slaap if sk=="Slecht"]
            if s_goed and s_slecht:
                diff = round(sum(s_slecht)/len(s_slecht) - sum(s_goed)/len(s_goed), 1)
                kleur = "#ef4444" if diff > 10 else "#22c55e"
                bevinding = f"Bij slechte slaap at je {abs(diff)}g suiker {'meer' if diff > 0 else 'minder'}"
                _correlatie_kaart("🍬 Suikerinname → Slaapkwaliteit", bevinding, kleur,
                    "Hoge suikerinname veroorzaakt bloedsuikerpieken die de slaap verstoren.")

        # Eiwit ↔ spierpijn
        eiwit_sp = [(d["eiwit"], d.get("spierpijn","")) for d in dagen_met_data if d.get("spierpijn")]
        if len(eiwit_sp) >= 3:
            e_geen = [e for e,s in eiwit_sp if s=="Geen"]
            e_zwaar = [e for e,s in eiwit_sp if s=="Zwaar"]
            if e_geen and e_zwaar:
                diff = round(sum(e_geen)/len(e_geen) - sum(e_zwaar)/len(e_zwaar))
                kleur = "#22c55e" if diff > 5 else "#fbbf24"
                bevinding = f"Bij geen spierpijn at je {abs(diff)}g eiwit {'meer' if diff > 0 else 'minder'}"
                _correlatie_kaart("💪 Eiwitinname → Spierpijn", bevinding, kleur,
                    "Voldoende eiwit (>1.6g/kg) versnelt spierherstel aantoonbaar.")

        # Water ↔ frisheid
        water_fris = [(d.get("water",0), d.get("frisheid","")) for d in dagen_met_data if d.get("frisheid") and d.get("water",0) > 0]
        if len(water_fris) >= 3:
            w_goed = [w for w,f in water_fris if f=="Goed"]
            w_slecht = [w for w,f in water_fris if f=="Slecht"]
            if w_goed and w_slecht:
                diff = round(sum(w_goed)/len(w_goed) - sum(w_slecht)/len(w_slecht), 1)
                kleur = "#22c55e" if diff > 0.2 else "#fbbf24"
                bevinding = f"Op frisse dagen dronk je {abs(diff)}L {'meer' if diff > 0 else 'minder'} water"
                _correlatie_kaart("💧 Waterinname → Frisheid", bevinding, kleur,
                    "Al 1-2% vochttekort vermindert cognitief functioneren en energieniveau meetbaar.")

        # Kcal ↔ rusthartslag
        kcal_rhr = [(d["kcal"], d.get("rhr",0)) for d in dagen_met_data if d.get("rhr",0) > 0]
        if len(kcal_rhr) >= 3:
            lage_kcal_rhr  = [r for k,r in kcal_rhr if k < energie_doel * 0.85]
            hoge_kcal_rhr  = [r for k,r in kcal_rhr if k >= energie_doel * 0.85]
            if lage_kcal_rhr and hoge_kcal_rhr:
                diff = round(sum(lage_kcal_rhr)/len(lage_kcal_rhr) - sum(hoge_kcal_rhr)/len(hoge_kcal_rhr), 1)
                kleur = "#ef4444" if diff > 3 else "#22c55e"
                bevinding = f"Bij onvoldoende kcal was je RHR {abs(diff)} bpm {'hoger' if diff > 0 else 'lager'}"
                _correlatie_kaart("⚡ Energie-inname → Rusthartslag", bevinding, kleur,
                    "Energietekort verhoogt cortisolniveau → hogere rusthartslag en trager herstel.")

    elif len(dagen_met_data) > 0:
        st.markdown(
            '<div style="background:#1e293b;border-radius:8px;padding:12px;color:#64748b;font-size:0.8rem;">'
            '📊 Vul het Dagboek minstens 3 dagen in om correlaties te berekenen.</div>',
            unsafe_allow_html=True)
    else:
        st.info("Vul het Voedingsdagboek in om correlaties te zien.")

def _stap_dashboard(user: dict):
    tab_db, tab_an = st.tabs(["📓 Dagboek", "📊 Analyses"])
    with tab_db:
        _render_voedingsdagboek(user)
    with tab_an:
        _render_analyses(user)


def render_fuelc(user: dict):
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">' +
        '<div style="font-size:2rem;font-weight:900;letter-spacing:3px;color:#f8fafc;">' +
        'FUEL<span style="color:#22c55e;">C</span></div>' +
        '<div style="font-size:0.85rem;font-weight:700;color:#22c55e;letter-spacing:2px;' +
        'border:1px solid #22c55e;border-radius:6px;padding:3px 10px;">' +
        'ENERGIE COACH</div></div>',
        unsafe_allow_html=True)

    if st.button("← Terug naar modules", key="fc_terug_top"):
        st.session_state.module = "menu"
        st.rerun()

    # Navigatieknoppen
    stap   = st.session_state.get("fc_stap", 1)
    namen  = ["Profiel","Trainingen","Bibliotheek","Weekschema","Analyses"]
    emojis = ["👤","🏃","🥦","📅","📊"]

    nav_cols = st.columns(5)
    for i, (col, naam_stap, emoji) in enumerate(zip(nav_cols, namen, emojis)):
        with col:
            actief = (i+1) == stap
            if st.button(
                f"{emoji}  {naam_stap}",
                key=f"nav_stap_{i+1}",
                use_container_width=True,
                type="primary" if actief else "secondary"):
                st.session_state.fc_stap = i+1
                st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if "fc_profiel" not in st.session_state:
        st.session_state.fc_profiel = _laad_profiel(user.get("id",""))

    profiel_ingevuld = bool(st.session_state.fc_profiel.get("bmr"))

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
