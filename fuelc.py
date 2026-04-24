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

    # ── Maaltijdmomenten instelling ──────────────────────────────────────────
    _sectie("EETPATROON & MAALTIJDMOMENTEN")
    st.markdown(
        '<div style="font-size:0.78rem;color:#64748b;margin-bottom:12px;">' +
        'Stel je eetpatroon in en pas de tijdstippen aan. Wordt toegepast op het weekschema.</div>',
        unsafe_allow_html=True)

    ep1, ep2 = st.columns(2)
    with ep1:
        patroon_keuze = st.selectbox("Eetpatroon",
            ["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"],
            index=["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"].index(
                p.get("eet_patroon","Klassiek (3 maaltijden)"))
            if p.get("eet_patroon") in ["Klassiek (3 maaltijden)","Intermittent 16:8","Intermittent 18:6"] else 0,
            key="prof_patroon")

    MAALTIJD_DEFAULTS = {
        "Klassiek (3 maaltijden)": [
            {"naam":"Ontbijt","tijdstip":"07:30","type":"ontbijt"},
            {"naam":"Lunch","tijdstip":"12:30","type":"lunch"},
            {"naam":"Avondmaal","tijdstip":"18:30","type":"avond"},
        ],
        "Intermittent 16:8": [
            {"naam":"Eerste maaltijd","tijdstip":"12:00","type":"ontbijt"},
            {"naam":"Tweede maaltijd","tijdstip":"16:00","type":"lunch"},
            {"naam":"Derde maaltijd","tijdstip":"19:30","type":"avond"},
        ],
        "Intermittent 18:6": [
            {"naam":"Eerste maaltijd","tijdstip":"13:00","type":"ontbijt"},
            {"naam":"Tweede maaltijd","tijdstip":"18:30","type":"avond"},
        ],
    }

    with ep2:
        if patroon_keuze == "Klassiek (3 maaltijden)":
            st.markdown('<div style="font-size:0.72rem;color:#64748b;padding-top:28px;">Tussendoor momenten:</div>', unsafe_allow_html=True)

    # Tussendoor (enkel bij klassiek)
    tussendoor_aan = []
    if patroon_keuze == "Klassiek (3 maaltijden)":
        td_cols = st.columns(3)
        td_namen = ["Tussendoor voormiddag","Tussendoor namiddag","Avondsnack"]
        td_tijden = ["10:00","15:00","21:00"]
        for ti in range(3):
            with td_cols[ti]:
                if st.checkbox(td_namen[ti], key=f"prof_td_{ti}",
                    value=bool(p.get(f"td_{ti}", False))):
                    tussendoor_aan.append(ti)

    # Tijdstippen aanpassen
    import json as _json_prof
    momenten_prof = MAALTIJD_DEFAULTS.get(patroon_keuze, MAALTIJD_DEFAULTS["Klassiek (3 maaltijden)"])
    opgeslagen_mom = p.get("momenten_tijden")
    if opgeslagen_mom:
        try: opgeslagen_mom = _json_prof.loads(opgeslagen_mom) if isinstance(opgeslagen_mom, str) else opgeslagen_mom
        except: opgeslagen_mom = None

    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin:10px 0 6px;">Tijdstippen aanpassen:</div>', unsafe_allow_html=True)
    tijd_cols = st.columns(len(momenten_prof))
    nieuwe_tijden = {}
    for i, m in enumerate(momenten_prof):
        with tijd_cols[i]:
            huidig = (opgeslagen_mom or {}).get(str(i), m["tijdstip"]) if opgeslagen_mom else m["tijdstip"]
            nieuwe_tijden[str(i)] = st.text_input(
                m["naam"], value=huidig,
                key=f"prof_tijd_{i}", placeholder="HH:MM")

    if patroon_keuze == "Klassiek (3 maaltijden)":
        td_cols2 = st.columns(3)
        for ti in tussendoor_aan:
            with td_cols2[ti]:
                huidig_td = (opgeslagen_mom or {}).get(f"td_{ti}", td_tijden[ti])
                nieuwe_tijden[f"td_{ti}"] = st.text_input(
                    td_namen[ti], value=huidig_td,
                    key=f"prof_tdtijd_{ti}", placeholder="HH:MM")

    # ── Opslaan ───────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<style>[data-testid="stButton"] button[kind="primary"],'
        '.fc-groen button{background:#22c55e!important;color:#0a0f1e!important;'
        'font-weight:800!important;}</style>',
        unsafe_allow_html=True)
    if totaal_pct != 100:
        st.markdown(
            f'<div style="background:#1a0a0a;border-left:3px solid #fbbf24;border-radius:0 8px 8px 0;padding:8px 14px;font-size:0.8rem;color:#fbbf24;margin-bottom:8px;">' +
            f'⚠️ Macro verdeling is {totaal_pct}% — aanbeveling is 100%. Je kan toch opslaan.</div>',
            unsafe_allow_html=True)

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
            import json as _json_save
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
                "eet_patroon":    st.session_state.get("prof_patroon","Klassiek (3 maaltijden)"),
                "momenten_tijden":_json_save.dumps({
                    str(i): st.session_state.get(f"prof_tijd_{i}", "") for i in range(6)
                }),
                "td_0": 0 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
                "td_1": 1 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
                "td_2": 2 in [ti for ti in range(3) if st.session_state.get(f"prof_td_{ti}")],
            }
            if _sla_profiel_op(user_id, profiel_data):
                st.session_state.fc_profiel = profiel_data
                st.success("✅ Profiel opgeslagen!")
                st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDERS ANDERE BLOKKEN
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# BLOK 2 — TRAININGEN (MANUELE INVOER)
# ═══════════════════════════════════════════════════════════════════════════════

SPORT_OPTIES = ["Lopen", "Fietsen", "Zwemmen", "Roeien", "Crosstrainer", "Indoor lopen", "Kracht", "Andere"]

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

# MET per sport voor nauwkeurigere kcal berekening
SPORT_MET_FACTOR = {
    "Lopen":          {"Z1":6.0,"Z2":8.5,"Z3":11.0,"Z4":13.0,"Z5":16.0},
    "Fietsen":        {"Z1":4.0,"Z2":6.0,"Z3":8.0,"Z4":10.0,"Z5":12.0},
    "Zwemmen":        {"Z1":5.0,"Z2":7.0,"Z3":9.0,"Z4":11.0,"Z5":13.0},
    "Roeien":         {"Z1":4.5,"Z2":7.0,"Z3":9.5,"Z4":11.5,"Z5":14.0},
    "Crosstrainer":   {"Z1":4.0,"Z2":6.0,"Z3":8.0,"Z4":10.0,"Z5":12.0},
    "Indoor lopen":   {"Z1":6.0,"Z2":8.5,"Z3":11.0,"Z4":13.0,"Z5":16.0},
    "Kracht":         {"Z1":3.5,"Z2":5.0,"Z3":6.0,"Z4":7.0,"Z5":8.0},
    "Andere":         {"Z1":4.0,"Z2":6.0,"Z3":8.5,"Z4":10.5,"Z5":13.0},
}

def _bereken_kcal(gewicht_kg: float, minuten: float, zone: str, sport: str = "") -> int:
    """MET-gebaseerde kcalberekening per sport."""
    z_key = zone[:2].upper() if zone else "Z2"
    sport_mets = SPORT_MET_FACTOR.get(sport, SPORT_MET_FACTOR["Andere"])
    met = sport_mets.get(z_key, 6.0)
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
        _laad_trainingen.clear()
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

def _parse_tempo(s: str):
    """Converteer tempo string (5:30 of 5.5) naar decimaal getal."""
    if not s: return None
    s = s.strip()
    if ":" in s:
        parts = s.split(":")
        try: return int(parts[0]) + int(parts[1])/60
        except: return None
    try: return float(s)
    except: return None


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
        _sectie("ALGEMEEN", "#22c55e")
        c1, c2, c3 = st.columns(3)
        with c1:
            sport = st.selectbox("Sport", SPORT_OPTIES, key="tr_sport")
        with c2:
            datum = st.date_input("Datum", key="tr_datum")
        with c3:
            omschrijving = st.text_input("Naam / omschrijving",
                placeholder="bijv. Lange duurloop", key="tr_naam")

        zones_data = _laad_zones(user_id, sport)
        eenheid    = zones_data.get("eenheid", "hartslag")

        if sport == "Lopen":
            invoer_modus = st.radio("Invoer op basis van",
                ["Tijd (minuten)", "Afstand (km)"],
                horizontal=True, key="tr_invoer_modus")
        else:
            invoer_modus = "Tijd (minuten)"

        def _zone_selectbox(label, key, default_idx=1):
            zone = st.selectbox(label, ZONE_LABELS, index=default_idx, key=key)
            info = _zone_info(zones_data, zone, eenheid, sport)
            if info:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#86efac;margin-top:-8px;margin-bottom:4px;">→ {info}</div>',
                    unsafe_allow_html=True)
            return zone

        def _invoer_blok(prefix, label_min, label_km, default_min, default_km, zone_idx):
            if invoer_modus == "Afstand (km)" and sport == "Lopen":
                km = st.number_input(label_km, 0.0, 200.0, default_km, 0.1, key=f"{prefix}_km")
                zone = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                tempo = zones_data.get(f"{zone[:2].lower()}_tempo")
                minuten = round(km * tempo) if tempo and tempo > 0 and km > 0 else round(km * 6) if km > 0 else 0
                return minuten, km, zone
            else:
                minuten = st.number_input(label_min, 0, 300, default_min, key=f"{prefix}_min")
                zone = _zone_selectbox("Intensiteitszone", f"{prefix}_zone", zone_idx)
                km_auto = 0.0
                return minuten, km_auto, zone

        _sectie("OPWARMING", "#22c55e")
        ow1, ow2 = st.columns(2)
        with ow1:
            opw_min, opw_km, opw_zone = _invoer_blok("tr_opw","Duur (min)","Afstand (km)",10,2.0,0)
        with ow2:
            opw_kcal = _bereken_kcal(gewicht, opw_min, opw_zone, sport) if opw_min > 0 else 0
            if opw_min > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                _metric_card("KCAL", str(opw_kcal), "kcal", "#22c55e")

        _sectie("KERN", "#22c55e")
        kern_type = st.radio("Type kern",
            ["Doorlopend","Intervalblokken","Ramp up","Ramp down"],
            horizontal=True, key="tr_kern_type")

        kern_min=0; kern_km=0.0; kern_zone=ZONE_LABELS[1]; kern_notitie=""

        if kern_type == "Doorlopend":
            k1, k2 = st.columns(2)
            with k1:
                kern_min, kern_km, kern_zone = _invoer_blok("tr_kern","Duur (min)","Afstand (km)",40,8.0,1)
            with k2:
                kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone, sport) if kern_min > 0 else 0
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
                int_werk = st.number_input("Werkblok (min)", 1, 60, 4, key="tr_int_werk")
                int_rust  = st.number_input("Rustblok (min)", 1, 30, 2, key="tr_int_rust")
            kern_min = int_herh * (int_werk + int_rust)
            kern_zone = int_zone_w
            kern_notitie = f"{int_herh}× {int_werk}min {int_zone_w[:2]} + {int_rust}min {int_zone_r[:2]}"
            with ic3:
                st.markdown(f'<div style="font-size:0.8rem;color:#22c55e;padding-top:28px;">{kern_notitie}</div>', unsafe_allow_html=True)
        elif kern_type == "Ramp up":
            ru1, ru2, ru3 = st.columns(3)
            with ru1: ramp_min = st.number_input("Duur (min)", 5, 120, 20, key="tr_ramp_min")
            with ru2: ramp_van  = _zone_selectbox("Van zone", "tr_ramp_van", 1)
            with ru3: ramp_naar = _zone_selectbox("Naar zone", "tr_ramp_naar", 3)
            kern_min = ramp_min; kern_zone = ramp_naar
            kern_notitie = f"Ramp: {ramp_van[:2]} → {ramp_naar[:2]}"
        elif kern_type == "Ramp down":
            rd1, rd2, rd3 = st.columns(3)
            with rd1: ramp_min = st.number_input("Duur (min)", 5, 120, 20, key="tr_rampd_min")
            with rd2: ramp_van  = _zone_selectbox("Van zone", "tr_rampd_van", 3)
            with rd3: ramp_naar = _zone_selectbox("Naar zone", "tr_rampd_naar", 1)
            kern_min = ramp_min; kern_zone = ramp_van
            kern_notitie = f"Ramp: {ramp_van[:2]} → {ramp_naar[:2]}"

        kern_kcal = _bereken_kcal(gewicht, kern_min, kern_zone, sport) if kern_min > 0 else 0

        _sectie("COOLING DOWN", "#22c55e")
        cd1, cd2 = st.columns(2)
        with cd1:
            cool_min, cool_km, cool_zone = _invoer_blok("tr_cool","Duur (min)","Afstand (km)",10,2.0,0)
        with cd2:
            cool_kcal = _bereken_kcal(gewicht, cool_min, cool_zone, sport) if cool_min > 0 else 0
            if cool_min > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                _metric_card("KCAL", str(cool_kcal), "kcal", "#22c55e")

        totaal_min  = opw_min + kern_min + cool_min
        totaal_kcal = opw_kcal + kern_kcal + cool_kcal
        blokken     = [(opw_zone, opw_min), (kern_zone, kern_min), (cool_zone, cool_min)]
        dom_zone    = _dominante_zone(blokken) if totaal_min > 0 else "—"

        if totaal_min > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("SAMENVATTING", "#22c55e")
            m1, m2, m3 = st.columns(3)
            with m1: _metric_card("TOTALE DUUR", f"{totaal_min//60}u{totaal_min%60:02d}", "min", "#22c55e")
            with m2: _metric_card("KCAL", str(totaal_kcal), "kcal", "#4ade80")
            with m3: _metric_card("DOM. ZONE", dom_zone[:2], dom_zone[4:], "#16a34a")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Training opslaan", key="tr_opslaan", use_container_width=True):
                zone_verdeling = {}
                for z, m in blokken:
                    key = z[:2].lower()
                    zone_verdeling[key] = zone_verdeling.get(key, 0) + m
                notitie_vol = (
                    f"{omschrijving + ' | ' if omschrijving else ''}"
                    f"OPW: {opw_min}min {opw_zone[:2]} | KERN: {kern_min}min {kern_zone[:2]}"
                    f"{chr(32)+kern_notitie if kern_notitie else ''} | COOL: {cool_min}min {cool_zone[:2]}"
                ).strip(" | ")
                import json as _jtr
                training_data = {
                    "datum":           str(datum),
                    "sport":           sport,
                    "duur_min":        totaal_min,
                    "kcal_verbranding":totaal_kcal,
                    "zone_verdeling":  _jtr.dumps(zone_verdeling),
                    "notitie":         notitie_vol,
                }
                if _sla_training_op(user_id, training_data):
                    _laad_trainingen.clear()
                    st.session_state["tr_saved"] = True
                    for k in [k for k in st.session_state
                              if k.startswith(("tr_opw","tr_kern","tr_cool",
                                               "tr_naam","tr_int","tr_ramp"))]:
                        st.session_state.pop(k, None)
                    st.rerun()

            if st.session_state.pop("tr_saved", False):
                st.success("✅ Training opgeslagen! Ga naar 📋 Mijn trainingen.")
        else:
            st.button("💾 Training opslaan", key="tr_opslaan", use_container_width=True, disabled=True)
            st.caption("Vul minstens één blok in.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ZONE KALIBRATIE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_zones:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZONE KALIBRATIE PER SPORT", "#22c55e")
        st.markdown(
            '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:16px;">' +
            'Koppel je intensiteitszones aan tempo of hartslag. ' +
            'Voer tempo in als decimale minuten: 5.30 = 5min30sec/km.</div>',
            unsafe_allow_html=True)

        kal_sport = st.selectbox("Sport", SPORT_OPTIES, key="kal_sport")
        kal_zones = _laad_zones(user_id, kal_sport)

        # Toon status per sport
        sport_status = []
        for sp in SPORT_OPTIES:
            z = _laad_zones(user_id, sp)
            if z:
                sport_status.append(f'<span style="background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;border-radius:4px;padding:2px 8px;font-size:0.7rem;margin:2px;">{sp} ✓</span>')
            else:
                sport_status.append(f'<span style="background:#1e293b;color:#475569;border:1px solid #334155;border-radius:4px;padding:2px 8px;font-size:0.7rem;margin:2px;">{sp}</span>')
        st.markdown(
            '<div style="margin-bottom:12px;">' + " ".join(sport_status) + '</div>',
            unsafe_allow_html=True)

        if kal_sport == "Lopen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/km)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Indoor lopen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/km)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Fietsen":
            kal_eenheid = st.radio("Koppelen aan",
                ["Watt", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Roeien":
            kal_eenheid = st.radio("Koppelen aan",
                ["Tempo (min/500m)", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        elif kal_sport == "Crosstrainer":
            kal_eenheid = st.radio("Koppelen aan",
                ["Watt", "Hartslag (bpm)", "Beide"],
                horizontal=True, key="kal_eenheid")
        else:
            kal_eenheid = "Hartslag (bpm)"

        toon_tempo = kal_eenheid in ["Tempo (min/km)", "Tempo (min/500m)", "Watt", "Beide"]
        toon_hs    = kal_eenheid in ["Hartslag (bpm)", "Beide"]
        if kal_sport in ("Lopen", "Indoor lopen"):
            tempo_label = "Tempo (min/km)"
        elif kal_sport == "Roeien":
            tempo_label = "Tempo (min/500m)"
        else:
            tempo_label = "Watt"

        nieuwe_zones = {"eenheid": "tempo" if toon_tempo and not toon_hs else "hartslag"}

        for z in ZONE_LABELS:
            z_key = z[:2].lower()
            st.markdown(
                f'<div style="font-size:0.75rem;font-weight:700;color:#22c55e;margin:14px 0 4px;' +
                f'padding:4px 8px;background:#0f172a;border-left:3px solid #22c55e;border-radius:0 4px 4px 0;">' +
                f'{z}</div>', unsafe_allow_html=True)

            if toon_tempo:
                t1, t2 = st.columns(2)
                with t1:
                    # Gebruik text_input voor tempo om automatisch aanpassen te voorkomen
                    huidig_van_raw = kal_zones.get(f"{z_key}_tempo_van") or 0
                    huidig_van_str = _format_tempo(float(huidig_van_raw)) if huidig_van_raw else ""
                    tempo_van_str = st.text_input(
                        f"{tempo_label} — van (langzamer)",
                        value=huidig_van_str,
                        key=f"kal_{z_key}_tempo_van_str",
                        placeholder="bijv. 5:30",
                        help="Formaat: min:sec bijv. 5:30 of 5.5")
                    # Converteer terug naar decimaal
                    nieuwe_zones[f"{z_key}_tempo_van"] = _parse_tempo(tempo_van_str)

                with t2:
                    huidig_tot_raw = kal_zones.get(f"{z_key}_tempo_tot") or 0
                    huidig_tot_str = _format_tempo(float(huidig_tot_raw)) if huidig_tot_raw else ""
                    tempo_tot_str = st.text_input(
                        f"{tempo_label} — tot (sneller)",
                        value=huidig_tot_str,
                        key=f"kal_{z_key}_tempo_tot_str",
                        placeholder="bijv. 5:00",
                        help="Formaat: min:sec bijv. 5:00 of 5.0")
                    nieuwe_zones[f"{z_key}_tempo_tot"] = _parse_tempo(tempo_tot_str)

                van_val = nieuwe_zones.get(f"{z_key}_tempo_van")
                tot_val = nieuwe_zones.get(f"{z_key}_tempo_tot")
                if van_val and tot_val:
                    if kal_sport == "Lopen":
                        preview = f"{_format_tempo(van_val)} — {_format_tempo(tot_val)} min/km"
                    else:
                        preview = f"{int(van_val)}—{int(tot_val)}W"
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {preview}</div>', unsafe_allow_html=True)

            if toon_hs:
                h1, h2 = st.columns(2)
                with h1:
                    hs_van = st.number_input("Hartslag — van (bpm)", 0, 220,
                        int(kal_zones.get(f"{z_key}_hs_van") or 0), 1,
                        key=f"kal_{z_key}_hs_van")
                    nieuwe_zones[f"{z_key}_hs_van"] = hs_van if hs_van > 0 else None
                with h2:
                    hs_tot = st.number_input("Hartslag — tot (bpm)", 0, 220,
                        int(kal_zones.get(f"{z_key}_hs_tot") or 0), 1,
                        key=f"kal_{z_key}_hs_tot")
                    nieuwe_zones[f"{z_key}_hs_tot"] = hs_tot if hs_tot > 0 else None
                if hs_van and hs_tot:
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#86efac;margin-top:-6px;margin-bottom:4px;">' +
                        f'→ {int(hs_van)}—{int(hs_tot)} bpm</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"💾 Zones opslaan voor {kal_sport}", key=f"kal_ops_{kal_sport}", use_container_width=True):
            if _sla_zones_op(user_id, kal_sport, nieuwe_zones):
                _laad_zones.clear()
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
                '<div style="text-align:center;color:#64748b;padding:30px;">' +
                'Nog geen trainingen toegevoegd.</div>',
                unsafe_allow_html=True)
        else:
            from datetime import date as _dt2, timedelta as _td2
            vandaag    = _dt2.today()
            week_start = vandaag - _td2(days=vandaag.weekday())
            week_kcal  = sum(t.get("kcal_verbranding",0) or 0 for t in trainingen if t.get("datum","") >= str(week_start))
            week_min   = sum(t.get("duur_min",0) or 0 for t in trainingen if t.get("datum","") >= str(week_start))
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #22c55e;border-radius:10px;' +
                f'padding:12px 16px;margin-bottom:16px;display:flex;gap:24px;">' +
                f'<div><div style="font-size:0.65rem;color:#64748b;">DEZE WEEK</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">{week_min//60}u{week_min%60:02d} · {week_kcal} kcal</div></div>' +
                f'<div><div style="font-size:0.65rem;color:#64748b;">TRAININGEN</div>' +
                f'<div style="font-size:1.1rem;font-weight:800;color:#22c55e;">' +
                f'{len([t for t in trainingen if t.get("datum","") >= str(week_start)])}</div></div></div>',
                unsafe_allow_html=True)

            SPORT_EMOJI = {"Lopen":"🏃","Fietsen":"🚴","Zwemmen":"🏊","Kracht":"💪","Andere":"⚡"}
            ZONE_KLEUR  = {"z1":"#64748b","z2":"#22c55e","z3":"#fbbf24","z4":"#f97316","z5":"#ef4444"}

            for t in trainingen:
                import json as _jt
                sport_em = SPORT_EMOJI.get(t.get("sport",""),"⚡")
                duur_min = t.get("duur_min",0) or 0
                kcal     = t.get("kcal_verbranding",0) or 0
                notitie  = t.get("notitie","") or ""
                zv = t.get("zone_verdeling") or {}
                if isinstance(zv,str):
                    try: zv = _jt.loads(zv)
                    except: zv = {}
                totaal_zv = sum(zv.values()) if zv else max(duur_min,1)
                zone_balken = "".join([
                    f'<div style="display:inline-block;width:{round(zv.get(z,0)/totaal_zv*100)}%;' +
                    f'height:6px;background:{kleur};"></div>'
                    for z,kleur in ZONE_KLEUR.items() if zv.get(z,0) > 0
                ])

                with st.expander(
                    f"{sport_em} {t.get('sport','')} — {t.get('datum','')[:10]} — "
                    f"{duur_min//60}u{duur_min%60:02d} — {kcal}kcal",
                    expanded=False):
                    if notitie:
                        st.markdown(f'<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">{notitie[:100]}</div>', unsafe_allow_html=True)
                    if zone_balken:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden;margin-bottom:6px;">{zone_balken}</div>',
                            unsafe_allow_html=True)

                    # Bevestiging verwijder
                    confirm_key = f"confirm_del_{t['id']}"
                    if not st.session_state.get(confirm_key, False):
                        if st.button("🗑 Verwijderen", key=f"tr_del_{t['id']}"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Ben je zeker dat je deze training wilt verwijderen?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Ja, verwijderen", key=f"tr_del_ja_{t['id']}", use_container_width=True):
                                if _verwijder_training(t["id"]):
                                    _laad_trainingen.clear()
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                        with c2:
                            if st.button("❌ Annuleren", key=f"tr_del_nee_{t['id']}", use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# VOEDSEL_DB — NEVO-GEBASEERD, 120+ PRODUCTEN MET HUISHOUDMATEN
# ═══════════════════════════════════════════════════════════════════════════════

VOEDSEL_DB = [
    # ── GRANEN & BROOD ────────────────────────────────────────────────────────
    {"naam":"Volkorenbrood","cat":"Granen & brood","moment":["ontbijt","lunch"],
     "portie":35,"portie_label":"1 snede","gi":50,
     "kcal":224,"kh":40,"suikers":3,"vezels":7,"eiwit":9,"vet":3,"verz":0.5,
     "natrium":400,"kalium":230,"calcium":25,"ijzer":2.0,"magnesium":45,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Wit brood","cat":"Granen & brood","moment":["ontbijt","lunch"],
     "portie":35,"portie_label":"1 snede","gi":70,
     "kcal":265,"kh":49,"suikers":4,"vezels":2,"eiwit":8,"vet":3,"verz":0.6,
     "natrium":500,"kalium":100,"calcium":40,"ijzer":1.5,"magnesium":20,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Havermout","cat":"Granen & brood","moment":["ontbijt"],
     "portie":45,"portie_label":"6 el droog","gi":55,
     "kcal":370,"kh":60,"suikers":1,"vezels":10,"eiwit":13,"vet":7,"verz":1.2,
     "natrium":5,"kalium":360,"calcium":50,"ijzer":3.9,"magnesium":130,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Rijst wit gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":64,
     "kcal":130,"kh":28,"suikers":0,"vezels":0,"eiwit":3,"vet":0,"verz":0,
     "natrium":0,"kalium":35,"calcium":10,"ijzer":0.2,"magnesium":12,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Rijst volkoren gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":50,
     "kcal":110,"kh":23,"suikers":0,"vezels":2,"eiwit":3,"vet":1,"verz":0.1,
     "natrium":0,"kalium":84,"calcium":10,"ijzer":0.5,"magnesium":44,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Pasta volkoren gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":180,"portie_label":"3 opscheplepels","gi":42,
     "kcal":150,"kh":28,"suikers":1,"vezels":4,"eiwit":6,"vet":1,"verz":0.1,
     "natrium":0,"kalium":90,"calcium":20,"ijzer":1.5,"magnesium":47,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Aardappel gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":175,"portie_label":"2 middelgrote","gi":72,
     "kcal":87,"kh":20,"suikers":1,"vezels":2,"eiwit":2,"vet":0,"verz":0,
     "natrium":5,"kalium":410,"calcium":6,"ijzer":0.3,"magnesium":20,"vitc":12,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Zoete aardappel gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 middelgrote","gi":61,
     "kcal":90,"kh":21,"suikers":4,"vezels":3,"eiwit":2,"vet":0,"verz":0,
     "natrium":36,"kalium":337,"calcium":30,"ijzer":0.7,"magnesium":25,"vitc":20,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Quinoa gekookt","cat":"Granen & brood","moment":["lunch","avond"],
     "portie":185,"portie_label":"3 opscheplepels","gi":53,
     "kcal":120,"kh":21,"suikers":1,"vezels":3,"eiwit":4,"vet":2,"verz":0.2,
     "natrium":5,"kalium":172,"calcium":17,"ijzer":1.5,"magnesium":64,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Rijstwafel naturel","cat":"Granen & brood","moment":["tussendoor","ontbijt"],
     "portie":9,"portie_label":"1 wafel","gi":82,
     "kcal":385,"kh":81,"suikers":1,"vezels":2,"eiwit":8,"vet":3,"verz":0.5,
     "natrium":10,"kalium":95,"calcium":5,"ijzer":0.5,"magnesium":35,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    # ── ZUIVEL & ALTERNATIEVEN ────────────────────────────────────────────────
    {"naam":"Volle melk","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":27,
     "kcal":64,"kh":5,"suikers":5,"vezels":0,"eiwit":3,"vet":4,"verz":2.4,
     "natrium":43,"kalium":150,"calcium":120,"ijzer":0.1,"magnesium":11,"vitc":1,"vitd":0.1,"vitb12":0.5,"omega3":0.1},
    {"naam":"Halfvolle melk","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":27,
     "kcal":46,"kh":5,"suikers":5,"vezels":0,"eiwit":3,"vet":2,"verz":1.1,
     "natrium":43,"kalium":150,"calcium":120,"ijzer":0.1,"magnesium":11,"vitc":1,"vitd":0.1,"vitb12":0.5,"omega3":0},
    {"naam":"Griekse yoghurt vol","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kommetje","gi":11,
     "kcal":130,"kh":4,"suikers":4,"vezels":0,"eiwit":9,"vet":8,"verz":5.0,
     "natrium":40,"kalium":170,"calcium":110,"ijzer":0.1,"magnesium":11,"vitc":0,"vitd":0.1,"vitb12":0.8,"omega3":0.1},
    {"naam":"Kwark mager","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"3 el","gi":15,
     "kcal":57,"kh":4,"suikers":4,"vezels":0,"eiwit":9,"vet":0,"verz":0,
     "natrium":40,"kalium":130,"calcium":95,"ijzer":0.1,"magnesium":9,"vitc":0,"vitd":0,"vitb12":0.5,"omega3":0},
    {"naam":"Skyr","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kommetje","gi":14,
     "kcal":63,"kh":4,"suikers":4,"vezels":0,"eiwit":11,"vet":0,"verz":0,
     "natrium":50,"kalium":160,"calcium":130,"ijzer":0.1,"magnesium":12,"vitc":0,"vitd":0.1,"vitb12":1.0,"omega3":0},
    {"naam":"Edammer 30+","cat":"Zuivel","moment":["ontbijt","lunch"],
     "portie":20,"portie_label":"1 plakje","gi":0,
     "kcal":270,"kh":0,"suikers":0,"vezels":0,"eiwit":27,"vet":18,"verz":11.0,
     "natrium":800,"kalium":100,"calcium":770,"ijzer":0.2,"magnesium":30,"vitc":0,"vitd":0.2,"vitb12":1.5,"omega3":0.2},
    {"naam":"Mozzarella","cat":"Zuivel","moment":["lunch","avond"],
     "portie":50,"portie_label":"halve bol","gi":0,
     "kcal":280,"kh":2,"suikers":1,"vezels":0,"eiwit":19,"vet":22,"verz":13.0,
     "natrium":600,"kalium":76,"calcium":505,"ijzer":0.3,"magnesium":20,"vitc":0,"vitd":0.2,"vitb12":1.3,"omega3":0.2},
    {"naam":"Haverdrank","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":49,
     "kcal":45,"kh":7,"suikers":4,"vezels":1,"eiwit":1,"vet":1,"verz":0.2,
     "natrium":60,"kalium":60,"calcium":120,"ijzer":0.2,"magnesium":10,"vitc":0,"vitd":1.0,"vitb12":0,"omega3":0},
    {"naam":"Sojadrank","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":200,"portie_label":"1 glas","gi":30,
     "kcal":40,"kh":3,"suikers":2,"vezels":0,"eiwit":3,"vet":2,"verz":0.3,
     "natrium":50,"kalium":130,"calcium":120,"ijzer":0.4,"magnesium":19,"vitc":0,"vitd":1.0,"vitb12":0.4,"omega3":0.3},
    {"naam":"Plattekaas","cat":"Zuivel","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"3 el","gi":10,
     "kcal":72,"kh":3,"suikers":3,"vezels":0,"eiwit":8,"vet":3,"verz":2.0,
     "natrium":55,"kalium":120,"calcium":85,"ijzer":0.1,"magnesium":8,"vitc":0,"vitd":0,"vitb12":0.5,"omega3":0},

    # ── VLEES & VIS ───────────────────────────────────────────────────────────
    {"naam":"Kipfilet gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 filet","gi":0,
     "kcal":165,"kh":0,"suikers":0,"vezels":0,"eiwit":31,"vet":4,"verz":1.0,
     "natrium":74,"kalium":370,"calcium":12,"ijzer":1.0,"magnesium":28,"vitc":0,"vitd":0.1,"vitb12":0.3,"omega3":0.1},
    {"naam":"Zalm gebakken","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":208,"kh":0,"suikers":0,"vezels":0,"eiwit":20,"vet":13,"verz":3.0,
     "natrium":59,"kalium":440,"calcium":15,"ijzer":0.5,"magnesium":27,"vitc":0,"vitd":9.0,"vitb12":3.0,"omega3":2.3},
    {"naam":"Tonijn in water","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 blikje uitgelekt","gi":0,
     "kcal":108,"kh":0,"suikers":0,"vezels":0,"eiwit":25,"vet":1,"verz":0.2,
     "natrium":320,"kalium":280,"calcium":10,"ijzer":1.3,"magnesium":30,"vitc":0,"vitd":3.0,"vitb12":2.0,"omega3":0.3},
    {"naam":"Rundergehakt mager","cat":"Vlees & vis","moment":["avond"],
     "portie":120,"portie_label":"1 portie","gi":0,
     "kcal":200,"kh":0,"suikers":0,"vezels":0,"eiwit":20,"vet":13,"verz":5.0,
     "natrium":75,"kalium":300,"calcium":10,"ijzer":2.5,"magnesium":20,"vitc":0,"vitd":0,"vitb12":2.0,"omega3":0.1},
    {"naam":"Kabeljauw","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":150,"portie_label":"1 filet","gi":0,
     "kcal":82,"kh":0,"suikers":0,"vezels":0,"eiwit":18,"vet":1,"verz":0.1,
     "natrium":54,"kalium":340,"calcium":15,"ijzer":0.3,"magnesium":30,"vitc":0,"vitd":1.0,"vitb12":1.5,"omega3":0.3},
    {"naam":"Makreel gerookt","cat":"Vlees & vis","moment":["lunch"],
     "portie":100,"portie_label":"1 filet","gi":0,
     "kcal":205,"kh":0,"suikers":0,"vezels":0,"eiwit":19,"vet":14,"verz":3.0,
     "natrium":700,"kalium":330,"calcium":12,"ijzer":1.0,"magnesium":30,"vitc":0,"vitd":5.0,"vitb12":7.0,"omega3":2.2},
    {"naam":"Garnalen","cat":"Vlees & vis","moment":["lunch","avond"],
     "portie":100,"portie_label":"1 portie","gi":0,
     "kcal":99,"kh":0,"suikers":0,"vezels":0,"eiwit":21,"vet":1,"verz":0.3,
     "natrium":111,"kalium":220,"calcium":60,"ijzer":1.5,"magnesium":30,"vitc":0,"vitd":0,"vitb12":1.0,"omega3":0.6},
    {"naam":"Kippenham","cat":"Vlees & vis","moment":["ontbijt","lunch"],
     "portie":30,"portie_label":"2 plakjes","gi":0,
     "kcal":105,"kh":2,"suikers":1,"vezels":0,"eiwit":18,"vet":3,"verz":1.0,
     "natrium":900,"kalium":200,"calcium":10,"ijzer":0.5,"magnesium":15,"vitc":0,"vitd":0,"vitb12":0.2,"omega3":0},
    {"naam":"Biefstuk","cat":"Vlees & vis","moment":["avond"],
     "portie":150,"portie_label":"1 stuk","gi":0,
     "kcal":217,"kh":0,"suikers":0,"vezels":0,"eiwit":26,"vet":12,"verz":4.0,
     "natrium":66,"kalium":380,"calcium":10,"ijzer":2.8,"magnesium":24,"vitc":0,"vitd":0,"vitb12":2.5,"omega3":0.1},
    {"naam":"Sardines in blik","cat":"Vlees & vis","moment":["lunch"],
     "portie":100,"portie_label":"1 blikje","gi":0,
     "kcal":208,"kh":0,"suikers":0,"vezels":0,"eiwit":25,"vet":11,"verz":1.5,
     "natrium":505,"kalium":300,"calcium":380,"ijzer":2.9,"magnesium":39,"vitc":0,"vitd":4.0,"vitb12":8.0,"omega3":1.5},

    # ── EIEREN ────────────────────────────────────────────────────────────────
    {"naam":"Ei gekookt","cat":"Eieren","moment":["ontbijt","lunch"],
     "portie":60,"portie_label":"1 ei (M)","gi":0,
     "kcal":155,"kh":1,"suikers":1,"vezels":0,"eiwit":13,"vet":11,"verz":3.0,
     "natrium":124,"kalium":130,"calcium":50,"ijzer":1.8,"magnesium":12,"vitc":0,"vitd":2.0,"vitb12":0.9,"omega3":0.1},
    {"naam":"Ei gebakken","cat":"Eieren","moment":["ontbijt","lunch"],
     "portie":60,"portie_label":"1 ei (M)","gi":0,
     "kcal":185,"kh":1,"suikers":0,"vezels":0,"eiwit":13,"vet":14,"verz":3.5,
     "natrium":130,"kalium":130,"calcium":50,"ijzer":1.8,"magnesium":12,"vitc":0,"vitd":2.0,"vitb12":0.9,"omega3":0.1},

    # ── GROENTEN ──────────────────────────────────────────────────────────────
    {"naam":"Broccoli gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":10,
     "kcal":34,"kh":7,"suikers":2,"vezels":3,"eiwit":3,"vet":0,"verz":0,
     "natrium":33,"kalium":316,"calcium":47,"ijzer":0.7,"magnesium":21,"vitc":65,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Spinazie gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":15,
     "kcal":23,"kh":4,"suikers":0,"vezels":2,"eiwit":3,"vet":0,"verz":0,
     "natrium":79,"kalium":466,"calcium":99,"ijzer":2.7,"magnesium":87,"vitc":28,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Wortel rauw","cat":"Groenten","moment":["lunch","tussendoor"],
     "portie":80,"portie_label":"1 middelgrote","gi":35,
     "kcal":41,"kh":10,"suikers":5,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":69,"kalium":320,"calcium":33,"ijzer":0.3,"magnesium":12,"vitc":6,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Tomaat","cat":"Groenten","moment":["lunch","avond"],
     "portie":120,"portie_label":"1 tomaat","gi":15,
     "kcal":18,"kh":4,"suikers":3,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":5,"kalium":237,"calcium":10,"ijzer":0.3,"magnesium":11,"vitc":14,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Paprika rood","cat":"Groenten","moment":["lunch","avond","tussendoor"],
     "portie":120,"portie_label":"1 paprika","gi":15,
     "kcal":31,"kh":7,"suikers":5,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":4,"kalium":212,"calcium":7,"ijzer":0.4,"magnesium":10,"vitc":128,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Courgette","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"2 opscheplepels","gi":15,
     "kcal":17,"kh":3,"suikers":2,"vezels":1,"eiwit":1,"vet":0,"verz":0,
     "natrium":8,"kalium":261,"calcium":16,"ijzer":0.4,"magnesium":18,"vitc":17,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Champignon","cat":"Groenten","moment":["ontbijt","lunch","avond"],
     "portie":100,"portie_label":"handjevol","gi":10,
     "kcal":22,"kh":3,"suikers":2,"vezels":1,"eiwit":3,"vet":0,"verz":0,
     "natrium":5,"kalium":318,"calcium":3,"ijzer":0.5,"magnesium":9,"vitc":3,"vitd":1.0,"vitb12":0,"omega3":0},
    {"naam":"Avocado","cat":"Groenten","moment":["ontbijt","lunch"],
     "portie":80,"portie_label":"halve avocado","gi":10,
     "kcal":160,"kh":9,"suikers":1,"vezels":7,"eiwit":2,"vet":15,"verz":2.0,
     "natrium":7,"kalium":485,"calcium":12,"ijzer":0.6,"magnesium":29,"vitc":10,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Linzen gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"3 opscheplepels","gi":32,
     "kcal":116,"kh":20,"suikers":2,"vezels":8,"eiwit":9,"vet":0,"verz":0,
     "natrium":238,"kalium":365,"calcium":19,"ijzer":3.3,"magnesium":36,"vitc":3,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Kikkererwten gekookt","cat":"Groenten","moment":["lunch","avond"],
     "portie":150,"portie_label":"3 opscheplepels","gi":28,
     "kcal":164,"kh":27,"suikers":5,"vezels":8,"eiwit":9,"vet":3,"verz":0.3,
     "natrium":24,"kalium":291,"calcium":49,"ijzer":2.9,"magnesium":48,"vitc":2,"vitd":0,"vitb12":0,"omega3":0.1},

    # ── FRUIT ─────────────────────────────────────────────────────────────────
    {"naam":"Banaan","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":120,"portie_label":"1 banaan (M)","gi":51,
     "kcal":89,"kh":23,"suikers":12,"vezels":3,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":358,"calcium":5,"ijzer":0.3,"magnesium":27,"vitc":9,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Appel","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 appel (M)","gi":38,
     "kcal":52,"kh":14,"suikers":10,"vezels":2,"eiwit":0,"vet":0,"verz":0,
     "natrium":1,"kalium":107,"calcium":6,"ijzer":0.1,"magnesium":5,"vitc":5,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sinaasappel","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 sinaasappel","gi":43,
     "kcal":47,"kh":12,"suikers":9,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":0,"kalium":181,"calcium":40,"ijzer":0.1,"magnesium":10,"vitc":53,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Bosbes","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":100,"portie_label":"handjevol","gi":25,
     "kcal":57,"kh":14,"suikers":10,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":77,"calcium":6,"ijzer":0.3,"magnesium":6,"vitc":10,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Aardbei","cat":"Fruit","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"handjevol","gi":40,
     "kcal":32,"kh":8,"suikers":5,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":153,"calcium":16,"ijzer":0.4,"magnesium":13,"vitc":59,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Mango","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":150,"portie_label":"1 kopje blokjes","gi":51,
     "kcal":60,"kh":15,"suikers":14,"vezels":2,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":168,"calcium":11,"ijzer":0.2,"magnesium":10,"vitc":28,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Kiwi","cat":"Fruit","moment":["tussendoor","ontbijt"],
     "portie":80,"portie_label":"1 kiwi","gi":39,
     "kcal":61,"kh":15,"suikers":9,"vezels":3,"eiwit":1,"vet":1,"verz":0,
     "natrium":3,"kalium":312,"calcium":34,"ijzer":0.3,"magnesium":17,"vitc":93,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Dadel gedroogd","cat":"Fruit","moment":["tussendoor"],
     "portie":30,"portie_label":"3 dadels","gi":42,
     "kcal":277,"kh":75,"suikers":66,"vezels":7,"eiwit":2,"vet":0,"verz":0,
     "natrium":1,"kalium":696,"calcium":64,"ijzer":0.9,"magnesium":54,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Rozijnen","cat":"Fruit","moment":["tussendoor"],
     "portie":30,"portie_label":"2 el","gi":64,
     "kcal":299,"kh":79,"suikers":59,"vezels":4,"eiwit":3,"vet":0,"verz":0,
     "natrium":11,"kalium":749,"calcium":50,"ijzer":1.9,"magnesium":32,"vitc":4,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Peer","cat":"Fruit","moment":["tussendoor"],
     "portie":150,"portie_label":"1 peer (M)","gi":38,
     "kcal":57,"kh":15,"suikers":10,"vezels":3,"eiwit":0,"vet":0,"verz":0,
     "natrium":1,"kalium":119,"calcium":9,"ijzer":0.2,"magnesium":7,"vitc":4,"vitd":0,"vitb12":0,"omega3":0},

    # ── NOTEN & ZADEN ─────────────────────────────────────────────────────────
    {"naam":"Amandelen","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~20st)","gi":0,
     "kcal":579,"kh":22,"suikers":4,"vezels":13,"eiwit":21,"vet":50,"verz":4.0,
     "natrium":1,"kalium":705,"calcium":264,"ijzer":3.7,"magnesium":270,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Walnoten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~7 halve)","gi":0,
     "kcal":654,"kh":14,"suikers":3,"vezels":7,"eiwit":15,"vet":65,"verz":6.0,
     "natrium":2,"kalium":441,"calcium":98,"ijzer":2.9,"magnesium":158,"vitc":1,"vitd":0,"vitb12":0,"omega3":2.6},
    {"naam":"Cashewnoten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"handjevol (~20st)","gi":25,
     "kcal":553,"kh":33,"suikers":6,"vezels":3,"eiwit":18,"vet":44,"verz":9.0,
     "natrium":12,"kalium":660,"calcium":37,"ijzer":6.7,"magnesium":292,"vitc":1,"vitd":0,"vitb12":0,"omega3":0.2},
    {"naam":"Chiazaad","cat":"Noten & zaden","moment":["ontbijt","tussendoor"],
     "portie":15,"portie_label":"1 el","gi":1,
     "kcal":486,"kh":42,"suikers":0,"vezels":34,"eiwit":17,"vet":31,"verz":3.0,
     "natrium":16,"kalium":407,"calcium":631,"ijzer":7.7,"magnesium":335,"vitc":2,"vitd":0,"vitb12":0,"omega3":5.1},
    {"naam":"Lijnzaad","cat":"Noten & zaden","moment":["ontbijt"],
     "portie":10,"portie_label":"1 el","gi":35,
     "kcal":534,"kh":29,"suikers":2,"vezels":27,"eiwit":18,"vet":42,"verz":4.0,
     "natrium":30,"kalium":813,"calcium":255,"ijzer":5.7,"magnesium":392,"vitc":0,"vitd":0,"vitb12":0,"omega3":6.4},
    {"naam":"Pompoenpitten","cat":"Noten & zaden","moment":["tussendoor"],
     "portie":25,"portie_label":"2 el","gi":25,
     "kcal":559,"kh":11,"suikers":1,"vezels":6,"eiwit":30,"vet":49,"verz":9.0,
     "natrium":7,"kalium":809,"calcium":46,"ijzer":8.8,"magnesium":592,"vitc":2,"vitd":0,"vitb12":0,"omega3":0.1},

    # ── VETTEN & OLIËN ────────────────────────────────────────────────────────
    {"naam":"Olijfolie extra vierge","cat":"Vetten & oliën","moment":["lunch","avond"],
     "portie":10,"portie_label":"1 el","gi":0,
     "kcal":884,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":100,"verz":14.0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0.1,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.8},
    {"naam":"Boter","cat":"Vetten & oliën","moment":["ontbijt","lunch"],
     "portie":10,"portie_label":"1 kl","gi":0,
     "kcal":717,"kh":1,"suikers":0,"vezels":0,"eiwit":1,"vet":81,"verz":51.0,
     "natrium":700,"kalium":24,"calcium":24,"ijzer":0.1,"magnesium":2,"vitc":0,"vitd":0.1,"vitb12":0,"omega3":0.3},
    {"naam":"Kokosolie","cat":"Vetten & oliën","moment":["ontbijt","avond"],
     "portie":10,"portie_label":"1 el","gi":0,
     "kcal":862,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":100,"verz":87.0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},

    # ── SAUZEN & SPREADS ──────────────────────────────────────────────────────
    {"naam":"Pindakaas naturel","cat":"Sauzen & spreads","moment":["ontbijt","tussendoor"],
     "portie":20,"portie_label":"1 el","gi":14,
     "kcal":594,"kh":20,"suikers":9,"vezels":6,"eiwit":25,"vet":50,"verz":10.0,
     "natrium":410,"kalium":705,"calcium":49,"ijzer":1.9,"magnesium":154,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Amandelboter","cat":"Sauzen & spreads","moment":["ontbijt","tussendoor"],
     "portie":20,"portie_label":"1 el","gi":0,
     "kcal":614,"kh":19,"suikers":5,"vezels":10,"eiwit":21,"vet":56,"verz":4.0,
     "natrium":5,"kalium":740,"calcium":264,"ijzer":3.7,"magnesium":270,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Hummus","cat":"Sauzen & spreads","moment":["lunch","tussendoor"],
     "portie":50,"portie_label":"2 el","gi":6,
     "kcal":177,"kh":14,"suikers":1,"vezels":6,"eiwit":8,"vet":10,"verz":1.0,
     "natrium":421,"kalium":228,"calcium":38,"ijzer":2.4,"magnesium":35,"vitc":3,"vitd":0,"vitb12":0,"omega3":0.3},
    {"naam":"Honing","cat":"Sauzen & spreads","moment":["ontbijt"],
     "portie":15,"portie_label":"1 el","gi":58,
     "kcal":304,"kh":82,"suikers":82,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":4,"kalium":52,"calcium":6,"ijzer":0.4,"magnesium":2,"vitc":1,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Tomatensaus","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":100,"portie_label":"3 el","gi":35,
     "kcal":72,"kh":12,"suikers":9,"vezels":2,"eiwit":2,"vet":2,"verz":0.3,
     "natrium":590,"kalium":400,"calcium":20,"ijzer":0.7,"magnesium":20,"vitc":15,"vitd":0,"vitb12":0,"omega3":0.1},
    {"naam":"Pesto groen","cat":"Sauzen & spreads","moment":["lunch","avond"],
     "portie":20,"portie_label":"1 el","gi":0,
     "kcal":490,"kh":5,"suikers":2,"vezels":2,"eiwit":8,"vet":49,"verz":9.0,
     "natrium":700,"kalium":200,"calcium":200,"ijzer":2.0,"magnesium":50,"vitc":5,"vitd":0,"vitb12":0,"omega3":0.4},

    # ── DRANKEN ───────────────────────────────────────────────────────────────
    {"naam":"Water","cat":"Dranken","moment":["ontbijt","lunch","avond","tussendoor"],
     "portie":250,"portie_label":"1 glas","gi":0,
     "kcal":0,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":0,"kalium":0,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Koffie zwart","cat":"Dranken","moment":["ontbijt","tussendoor"],
     "portie":150,"portie_label":"1 kopje","gi":0,
     "kcal":2,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":2,"kalium":92,"calcium":2,"ijzer":0.1,"magnesium":6,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Groene thee","cat":"Dranken","moment":["tussendoor","ontbijt"],
     "portie":200,"portie_label":"1 glas","gi":0,
     "kcal":1,"kh":0,"suikers":0,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":0,"kalium":21,"calcium":2,"ijzer":0.1,"magnesium":3,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sinaasappelsap vers","cat":"Dranken","moment":["ontbijt"],
     "portie":150,"portie_label":"1 glas","gi":50,
     "kcal":45,"kh":10,"suikers":9,"vezels":0,"eiwit":1,"vet":0,"verz":0,
     "natrium":1,"kalium":200,"calcium":11,"ijzer":0.2,"magnesium":11,"vitc":50,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Kokoswater","cat":"Dranken","moment":["tussendoor"],
     "portie":250,"portie_label":"1 glas","gi":54,
     "kcal":19,"kh":4,"suikers":4,"vezels":0,"eiwit":1,"vet":0,"verz":0,
     "natrium":105,"kalium":250,"calcium":24,"ijzer":0.3,"magnesium":25,"vitc":2,"vitd":0,"vitb12":0,"omega3":0},

    # ── SPORTVOEDING ──────────────────────────────────────────────────────────
    {"naam":"Energiegel standaard","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":40,"portie_label":"1 gel","gi":80,
     "kcal":100,"kh":25,"suikers":17,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":55,"kalium":30,"calcium":0,"ijzer":0,"magnesium":0,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Sportdrank isotoon","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":500,"portie_label":"1 bidon","gi":70,
     "kcal":140,"kh":35,"suikers":30,"vezels":0,"eiwit":0,"vet":0,"verz":0,
     "natrium":230,"kalium":80,"calcium":0,"ijzer":0,"magnesium":10,"vitc":0,"vitd":0,"vitb12":0,"omega3":0},
    {"naam":"Whey proteïne","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":30,"portie_label":"1 schep","gi":20,
     "kcal":380,"kh":6,"suikers":4,"vezels":0,"eiwit":80,"vet":4,"verz":1.0,
     "natrium":200,"kalium":200,"calcium":200,"ijzer":0.5,"magnesium":50,"vitc":0,"vitd":0,"vitb12":1.0,"omega3":0.2},
    {"naam":"Recovery shake","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":80,"portie_label":"1 portie","gi":55,
     "kcal":350,"kh":50,"suikers":20,"vezels":2,"eiwit":25,"vet":5,"verz":1.0,
     "natrium":300,"kalium":300,"calcium":300,"ijzer":3.0,"magnesium":80,"vitc":20,"vitd":1.0,"vitb12":1.5,"omega3":0.3},
    {"naam":"Energiereep","cat":"Sportvoeding","moment":["tussendoor"],
     "portie":65,"portie_label":"1 reep","gi":65,
     "kcal":380,"kh":60,"suikers":30,"vezels":3,"eiwit":10,"vet":10,"verz":3.0,
     "natrium":200,"kalium":200,"calcium":100,"ijzer":2.0,"magnesium":40,"vitc":0,"vitd":0,"vitb12":0,"omega3":0.1},
]

CATEGORIE_OPTIES = [
    "Granen & brood","Zuivel","Eieren","Vlees & vis","Groenten","Fruit",
    "Noten & zaden","Vetten & oliën","Sauzen & spreads","Dranken","Sportvoeding","Overige"
]


# ── UITGEBREID PRODUCT FORMULIER (manueel + scan) ────────────────────────────

EENHEID_OPTIES = [
    ("gram (g)", 1.0),
    ("stuk", None),      # gebruiker geeft gram per stuk op
    ("snede", None),
    ("plakje", None),
    ("eetlepel (15ml)", 15.0),
    ("koffielepel (5ml)", 5.0),
    ("kopje (150ml)", 150.0),
    ("glas (200ml)", 200.0),
    ("bidon (500ml)", 500.0),
    ("opscheplepel (75g)", 75.0),
    ("handjevol (25g)", 25.0),
    ("portie", None),
    ("ml", 1.0),
]


def _product_formulier(prefix: str, defaults: dict = None) -> dict:
    """Universeel product invoerformulier — zelfde voor manueel en scan."""
    d = defaults or {}

    _sectie("PRODUCTINFO", "#22c55e")
    p1, p2 = st.columns(2)
    with p1:
        naam = st.text_input("Productnaam *",
            value=d.get("naam",""), key=f"{prefix}_naam",
            placeholder="bijv. Havermout Quaker")
    with p2:
        cat_idx = CATEGORIE_OPTIES.index(d.get("categorie","Overige")) \
            if d.get("categorie") in CATEGORIE_OPTIES else len(CATEGORIE_OPTIES)-1
        categorie = st.selectbox("Categorie *", CATEGORIE_OPTIES,
            index=cat_idx, key=f"{prefix}_cat")

    # Portie instelling
    _sectie("PORTIE & EENHEID", "#22c55e")
    eu1, eu2, eu3 = st.columns(3)
    with eu1:
        eenheid_namen = [e[0] for e in EENHEID_OPTIES]
        eenheid = st.selectbox("Eenheid",
            eenheid_namen, key=f"{prefix}_eenheid")
        gram_factor = dict(EENHEID_OPTIES).get(eenheid)
    with eu2:
        portie_hoev = st.number_input(
            "Hoeveelheid per portie",
            0.1, 2000.0,
            float(d.get("portie_g", 100)),
            0.5, key=f"{prefix}_portie_hoev")
    with eu3:
        if gram_factor:
            portie_g = round(portie_hoev * gram_factor, 1)
            st.markdown(
                f'<div style="font-size:0.75rem;color:#22c55e;padding-top:28px;">'
                f'= {portie_g}g</div>', unsafe_allow_html=True)
        else:
            portie_g = portie_hoev
            st.markdown(
                f'<div style="font-size:0.75rem;color:#64748b;padding-top:28px;">'
                f'{portie_g}g per stuk/portie</div>', unsafe_allow_html=True)
    portie_label = f"{portie_hoev} {eenheid}"

    # Macros per 100g
    _sectie("ENERGIE & MACROS per 100g", "#22c55e")
    m1, m2, m3 = st.columns(3)
    with m1:
        kcal = st.number_input("Energie (kcal)", 0.0, 900.0,
            float(d.get("kcal_100g",0) or 0), 1.0, key=f"{prefix}_kcal")
    with m2:
        kh = st.number_input("Koolhydraten (g)", 0.0, 100.0,
            float(d.get("kh_100g",0) or 0), 0.1, key=f"{prefix}_kh")
    with m3:
        suikers = st.number_input("waarvan suikers (g)", 0.0, 100.0,
            float(d.get("suikers_100g",0) or 0), 0.1, key=f"{prefix}_suikers")

    m4, m5, m6 = st.columns(3)
    with m4:
        vezels = st.number_input("Vezels (g)", 0.0, 100.0,
            float(d.get("vezels_100g",0) or 0), 0.1, key=f"{prefix}_vezels")
    with m5:
        eiwit = st.number_input("Eiwit (g)", 0.0, 100.0,
            float(d.get("eiwit_100g",0) or 0), 0.1, key=f"{prefix}_eiwit")
    with m6:
        vet = st.number_input("Vetten totaal (g)", 0.0, 100.0,
            float(d.get("vet_100g",0) or 0), 0.1, key=f"{prefix}_vet")

    m7, m8 = st.columns(2)
    with m7:
        verz = st.number_input("waarvan verzadigd (g)", 0.0, 100.0,
            float(d.get("verzadigd_100g",0) or 0), 0.1, key=f"{prefix}_verz")
    with m8:
        natrium = st.number_input("Natrium (mg)", 0.0, 5000.0,
            float(d.get("natrium_100g",0) or 0), 1.0, key=f"{prefix}_natrium")

    # Extra voedingsstoffen
    _sectie("MINERALEN & VITAMINEN per 100g", "#22c55e")
    st.markdown(
        '<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">'
        'Optioneel — vul in wat op het etiket staat.</div>',
        unsafe_allow_html=True)

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        kalium = st.number_input("Kalium (mg)", 0.0, 5000.0,
            float(d.get("kalium_100g",0) or 0), 1.0, key=f"{prefix}_kalium")
        vitc = st.number_input("Vit C (mg)", 0.0, 1000.0,
            float(d.get("vitc_100g",0) or 0), 0.1, key=f"{prefix}_vitc")
    with v2:
        calcium = st.number_input("Calcium (mg)", 0.0, 2000.0,
            float(d.get("calcium_100g",0) or 0), 1.0, key=f"{prefix}_calcium")
        vitd = st.number_input("Vit D (µg)", 0.0, 100.0,
            float(d.get("vitd_100g",0) or 0), 0.1, key=f"{prefix}_vitd")
    with v3:
        ijzer = st.number_input("IJzer (mg)", 0.0, 50.0,
            float(d.get("ijzer_100g",0) or 0), 0.1, key=f"{prefix}_ijzer")
        vitb12 = st.number_input("Vit B12 (µg)", 0.0, 100.0,
            float(d.get("vitb12_100g",0) or 0), 0.1, key=f"{prefix}_vitb12")
    with v4:
        magnesium = st.number_input("Magnesium (mg)", 0.0, 1000.0,
            float(d.get("magnesium_100g",0) or 0), 1.0, key=f"{prefix}_magnesium")
        omega3 = st.number_input("Omega-3 (g)", 0.0, 20.0,
            float(d.get("omega3_100g",0) or 0), 0.1, key=f"{prefix}_omega3")

    # GI
    gi_col, notitie_col = st.columns(2)
    with gi_col:
        gi = st.number_input("Glycemische index (GI)", 0, 100,
            int(d.get("gi",0) or 0), 1, key=f"{prefix}_gi",
            help="0 = onbekend | <55 laag | 55-69 matig | ≥70 hoog")
    with notitie_col:
        notitie = st.text_input("Notitie (optioneel)",
            value=d.get("notitie","") or "",
            key=f"{prefix}_notitie",
            placeholder="bijv. biologisch, glutenvrij...")

    # Live preview per portie
    if kcal > 0 or kh > 0 or eiwit > 0:
        f = portie_g / 100
        st.markdown(
            f'<div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin-top:8px;">'
            f'<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;">PREVIEW PER PORTIE ({portie_label})</div>'
            f'<div style="display:flex;gap:16px;flex-wrap:wrap;">'
            f'<span style="font-size:0.85rem;font-weight:700;color:#f97316;">{round(kcal*f)}kcal</span>'
            f'<span style="font-size:0.8rem;color:#22c55e;">{round(kh*f,1)}g KH</span>'
            f'<span style="font-size:0.8rem;color:#3b82f6;">{round(eiwit*f,1)}g eiwit</span>'
            f'<span style="font-size:0.8rem;color:#8b5cf6;">{round(vet*f,1)}g vet</span>'
            f'<span style="font-size:0.8rem;color:#64748b;">{round(vezels*f,1)}g vezels</span>'
            f'{"<span style=\"font-size:0.75rem;color:#fbbf24;\">GI " + str(gi) + "</span>" if gi > 0 else ""}'
            f'</div></div>',
            unsafe_allow_html=True)

    favoriet = st.checkbox("⭐ Toevoegen aan favorieten", key=f"{prefix}_fav",
        value=bool(d.get("favoriet",False)))

    return {
        "naam":           naam.strip() if naam else "",
        "categorie":      categorie,
        "portie_g":       portie_g,
        "portie_label":   portie_label,
        "kcal_100g":      kcal or None,
        "kh_100g":        kh or None,
        "suikers_100g":   suikers or None,
        "vezels_100g":    vezels or None,
        "eiwit_100g":     eiwit or None,
        "vet_100g":       vet or None,
        "verzadigd_100g": verz or None,
        "natrium_100g":   natrium or None,
        "kalium_100g":    kalium or None,
        "calcium_100g":   calcium or None,
        "ijzer_100g":     ijzer or None,
        "magnesium_100g": magnesium or None,
        "vitc_100g":      vitc or None,
        "vitd_100g":      vitd or None,
        "vitb12_100g":    vitb12 or None,
        "omega3_100g":    omega3 or None,
        "gi":             gi or None,
        "notitie":        notitie.strip() if notitie else None,
        "favoriet":       favoriet,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BIBLIOTHEEK SUPABASE FUNCTIES
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def _laad_bibliotheek_raw(user_id: str) -> list:
    try:
        r = _get_supabase().table("fuelc_bibliotheek").select("*")            .eq("user_id", user_id).order("naam").execute()
        return r.data or []
    except Exception as e:
        print(f"Fout bibliotheek: {e}")
        return []

def _laad_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    data = _laad_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        data = [p for p in data if zoek_l in (p.get("naam") or "").lower()]
    if categorie and categorie != "Alle":
        data = [p for p in data if p.get("categorie","") == categorie]
    return data

@st.cache_data(ttl=30)
def _laad_gecombineerde_bibliotheek_raw(user_id: str) -> list:
    eigen = _laad_bibliotheek_raw(user_id)
    eigen_namen = {p["naam"].lower() for p in eigen}
    databank = []
    for p in VOEDSEL_DB:
        if p["naam"].lower() not in eigen_namen:
            databank.append({
                "id": f"db_{p['naam']}", "naam": p["naam"],
                "categorie": p["cat"], "bron": "databank",
                "portie_g": p["portie"], "portie_label": p.get("portie_label", f"{p['portie']}g"),
                "kcal_100g": p["kcal"], "kh_100g": p["kh"],
                "suikers_100g": p["suikers"], "eiwit_100g": p["eiwit"],
                "vet_100g": p["vet"], "verzadigd_100g": p["verz"],
                "vezels_100g": p["vezels"], "natrium_100g": p["natrium"],
                "kalium_100g": p.get("kalium"), "calcium_100g": p.get("calcium"),
                "ijzer_100g": p.get("ijzer"), "magnesium_100g": p.get("magnesium"),
                "vitc_100g": p.get("vitc"), "vitd_100g": p.get("vitd"),
                "vitb12_100g": p.get("vitb12"), "omega3_100g": p.get("omega3"),
                "gi": p.get("gi"), "favoriet": False,
            })
    return eigen + databank

def _laad_gecombineerde_bibliotheek(user_id: str, zoek: str = "", categorie: str = "") -> list:
    data = _laad_gecombineerde_bibliotheek_raw(user_id)
    if zoek:
        zoek_l = zoek.lower()
        data = [p for p in data if zoek_l in p["naam"].lower()]
    if categorie and categorie != "Alle":
        data = [p for p in data if p.get("categorie","") == categorie]
    return data

def _sla_product_op(user_id: str, product: dict) -> bool:
    try:
        product["user_id"] = user_id
        if "bron" not in product:
            product["bron"] = "manueel"
        _get_supabase().table("fuelc_bibliotheek").insert(product).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False

def _update_product(product_id: str, data: dict) -> bool:
    try:
        _get_supabase().table("fuelc_bibliotheek").update(data).eq("id", product_id).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout updaten: {e}")
        return False

def _verwijder_product(product_id: str) -> bool:
    try:
        _get_supabase().table("fuelc_bibliotheek").delete().eq("id", product_id).execute()
        _laad_bibliotheek_raw.clear()
        _laad_gecombineerde_bibliotheek_raw.clear()
        return True
    except Exception as e:
        st.error(f"Fout verwijderen: {e}")
        return False


# ─── COMMUNITY FUNCTIES ───────────────────────────────────────────────────────


def _laad_community_recepten() -> list:
    """Laad alle gedeelde recepten met scores en reacties."""
    try:
        r = _get_supabase().table("fuelc_recepten_eigen").select("*")\
            .eq("is_globaal", True).order("naam").execute()
        recepten = r.data or []

        # Laad scores
        if recepten:
            rec_ids = [r["id"] for r in recepten]
            scores_r = _get_supabase().table("fuelc_recept_scores").select("*")\
                .in_("recept_id", rec_ids).execute()
            scores = scores_r.data or []

            reacties_r = _get_supabase().table("fuelc_recept_reacties").select("*")\
                .in_("recept_id", rec_ids).order("created_at", desc=True).execute()
            reacties = reacties_r.data or []

            for rec in recepten:
                rec_scores = [s["score"] for s in scores if s["recept_id"] == rec["id"]]
                rec["gem_score"]   = round(sum(rec_scores)/len(rec_scores), 1) if rec_scores else 0
                rec["n_scores"]    = len(rec_scores)
                rec["reacties"]    = [rt for rt in reacties if rt["recept_id"] == rec["id"]]
                rec["n_reacties"]  = len(rec["reacties"])

        return recepten
    except Exception as e:
        print(f"Fout laden community: {e}")
        return []

def _sla_score_op(recept_id: str, user_id: str, score: int) -> bool:
    try:
        _get_supabase().table("fuelc_recept_scores").upsert({
            "recept_id": recept_id,
            "user_id":   user_id,
            "score":     score,
        }, on_conflict="recept_id,user_id").execute()
        return True
    except Exception as e:
        st.error(f"Fout score: {e}")
        return False

def _sla_reactie_op(recept_id: str, user_id: str, naam: str, bericht: str) -> bool:
    try:
        if not bericht.strip(): return False
        _get_supabase().table("fuelc_recept_reacties").insert({
            "recept_id": recept_id,
            "user_id":   user_id,
            "naam":      naam,
            "bericht":   bericht[:200],
        }).execute()
        return True
    except Exception as e:
        st.error(f"Fout reactie: {e}")
        return False

def _verwijder_reactie(reactie_id: str) -> bool:
    try:
        _get_supabase().table("fuelc_recept_reacties").delete().eq("id", reactie_id).execute()
        return True
    except: return False

def _render_community_tab(user: dict):
    """Community tab in bibliotheek."""
    import json as _j
    user_id  = user.get("id","")
    user_naam = user.get("name","Gebruiker")
    is_admin  = user_id == "22019eac-30b9-471e-88f3-58c7e80a4876"

    st.markdown("<br>", unsafe_allow_html=True)
    _sectie("COMMUNITY RECEPTEN", "#22c55e")
    st.markdown(
        '<div style="font-size:0.8rem;color:#64748b;margin-bottom:16px;">'
        'Gedeelde recepten van de community — scoor en laat een reactie achter.</div>',
        unsafe_allow_html=True)

    recepten = _laad_community_recepten()

    if not recepten:
        st.markdown(
            '<div style="text-align:center;color:#64748b;padding:40px;">'
            '🌍 Nog geen gedeelde recepten. Deel jouw eerste recept via de tab "📋 Mijn recepten"!</div>',
            unsafe_allow_html=True)
        return

    # Sorteer op score
    recepten = sorted(recepten, key=lambda r: r.get("gem_score",0), reverse=True)

    TYPE_EMOJI = {"ontbijt":"🌅","tussendoor":"🍎","lunch":"🥗","avond":"🍽️"}

    for rec in recepten:
        gem   = rec.get("gem_score", 0)
        n_sc  = rec.get("n_scores", 0)
        n_rt  = rec.get("n_reacties", 0)
        sterren = "⭐" * round(gem) + "☆" * (5 - round(gem)) if gem > 0 else "☆☆☆☆☆"
        emoji = TYPE_EMOJI.get(rec.get("type",""), "🍴")

        with st.expander(
            f"{emoji} {rec['naam']}  {sterren}  "
            f"({gem}/5 · {n_sc} scores · {n_rt} reacties)",
            expanded=False):

            # Macro info
            mc1,mc2,mc3,mc4 = st.columns(4)
            for col, label, val, kleur in [
                (mc1,"KCAL",rec.get("kcal",0),"#f97316"),
                (mc2,"KH g",rec.get("kh",0),"#22c55e"),
                (mc3,"EIWIT g",rec.get("eiwit",0),"#3b82f6"),
                (mc4,"VET g",rec.get("vet",0),"#8b5cf6"),
            ]:
                with col:
                    st.markdown(
                        f'<div style="background:#1e293b;border-radius:6px;padding:8px;text-align:center;">'
                        f'<div style="font-size:0.6rem;color:#64748b;">{label}</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:{kleur};">{val}</div>'
                        f'</div>', unsafe_allow_html=True)

            # Ingrediënten
            ing = rec.get("ingredienten") or []
            if isinstance(ing, str):
                try: ing = _j.loads(ing)
                except: ing = []
            if ing:
                ing_txt = " · ".join([f"{i.get('naam','')} {i.get('gram',0)}g" for i in ing])
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#94a3b8;margin:8px 0 4px;">🥗 {ing_txt}</div>',
                    unsafe_allow_html=True)
            if rec.get("bereiding"):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:8px;">'
                    f'👨‍🍳 {rec["bereiding"]}</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border-color:#1e293b;margin:8px 0;">', unsafe_allow_html=True)

            # Score geven
            sc1, sc2 = st.columns([3,2])
            with sc1:
                st.markdown(
                    '<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin-bottom:4px;">'
                    '⭐ Jouw score</div>', unsafe_allow_html=True)
                mijn_score = st.select_slider(
                    "Score", options=[1,2,3,4,5],
                    key=f"score_{rec['id']}", label_visibility="collapsed")
            with sc2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Score opslaan", key=f"score_ops_{rec['id']}",
                             use_container_width=True):
                    if _sla_score_op(rec["id"], user_id, mijn_score):
                        st.success(f"✅ Score {mijn_score}/5 opgeslagen!")
                        st.rerun()

            # Reacties tonen
            reacties = rec.get("reacties", [])
            if reacties:
                st.markdown(
                    f'<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin:8px 0 6px;">'
                    f'💬 Reacties ({len(reacties)})</div>', unsafe_allow_html=True)
                for rt in reacties[-5:]:  # max 5 tonen
                    datum = rt.get("created_at","")[:10]
                    rt_naam = rt.get("naam","Gebruiker")
                    can_del = is_admin or rt.get("user_id") == user_id
                    rd1, rd2 = st.columns([5,0.5]) if can_del else st.columns([5,0.1])
                    with rd1:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:8px 12px;margin-bottom:4px;">'
                            f'<div style="font-size:0.65rem;color:#64748b;">{rt_naam} · {datum}</div>'
                            f'<div style="font-size:0.8rem;color:#f1f5f9;">{rt.get("bericht","")}</div>'
                            f'</div>', unsafe_allow_html=True)
                    if can_del:
                        with rd2:
                            if st.button("✕", key=f"del_rt_{rt['id']}"):
                                _verwijder_reactie(rt["id"])
                                st.rerun()

            # Reactie toevoegen
            st.markdown(
                '<div style="font-size:0.72rem;font-weight:700;color:#f8fafc;margin:8px 0 4px;">'
                '✍️ Reactie achterlaten</div>', unsafe_allow_html=True)
            ra1, ra2 = st.columns([4,1])
            with ra1:
                bericht = st.text_input("Bericht", max_chars=200,
                    placeholder="Wat vind je van dit recept? (max 200 tekens)",
                    key=f"bericht_{rec['id']}", label_visibility="collapsed")
            with ra2:
                if st.button("Stuur", key=f"reactie_ops_{rec['id']}",
                             use_container_width=True):
                    if bericht.strip():
                        if _sla_reactie_op(rec["id"], user_id, user_naam, bericht):
                            st.success("✅ Reactie geplaatst!")
                            st.session_state.pop(f"bericht_{rec['id']}", None)
                            st.rerun()
                    else:
                        st.warning("Typ een bericht.")

            # Admin: verwijder recept
            if is_admin:
                if st.button("🗑 Recept verwijderen (admin)", key=f"del_rec_{rec['id']}"):
                    _verwijder_eigen_recept(rec["id"])
                    st.rerun()






def _render_receptenbeheer(user_id: str):
    """Receptenbeheer — ingredienten opbouwen via universeel formulier."""
    import json as _j

    tab_nieuw, tab_lijst = st.tabs(["➕ Recept toevoegen", "📋 Mijn recepten"])

    with tab_nieuw:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("NIEUW RECEPT", "#22c55e")
        ri1, ri2 = st.columns(2)
        with ri1:
            r_naam = st.text_input("Naam recept *", key="r_naam",
                placeholder="bijv. Havermout met fruit en noten")
        with ri2:
            r_type = st.selectbox("Type *",
                ["ontbijt","tussendoor","lunch","avond"], key="r_type",
                format_func=lambda x: {"ontbijt":"🌅 Ontbijt","tussendoor":"🍎 Tussendoor",
                    "lunch":"🥗 Lunch","avond":"🍽️ Avond"}[x])
        r_globaal = st.checkbox("🌍 Deel met community", key="r_globaal")

        _sectie("INGREDIËNTEN", "#22c55e")

        # Ingrediënten in session state bewaren
        if "r_ingredienten" not in st.session_state:
            st.session_state["r_ingredienten"] = []
        ingredienten_data = st.session_state["r_ingredienten"]

        # Bereken totalen
        def _som(veld):
            return sum((i.get(veld,0) or 0)*(i.get("gram",100)/100) for i in ingredienten_data)
        totaal_kcal  = _som("kcal_100g")
        totaal_kh    = _som("kh_100g")
        totaal_eiwit = _som("eiwit_100g")
        totaal_vet   = _som("vet_100g")
        totaal_vezels= _som("vezels_100g")
        totaal_natrium=_som("natrium_100g")

        # Toon toegevoegde ingrediënten
        for ii, ing in enumerate(ingredienten_data):
            ic1, ic2, ic3, ic4 = st.columns([4, 1.5, 2, 0.5])
            with ic1:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#f1f5f9;padding:5px 0;">' +
                    f'<b>{ing["naam"]}</b></div>',
                    unsafe_allow_html=True)
            with ic2:
                nieuwe_gram = st.number_input("g", 1.0, 2000.0, float(ing["gram"]), 5.0,
                    key=f"r_gram_{ii}", label_visibility="collapsed")
                if nieuwe_gram != ing["gram"]:
                    st.session_state["r_ingredienten"][ii]["gram"] = nieuwe_gram
                    st.rerun()
            with ic3:
                kcal_ing = round((ing.get("kcal_100g",0) or 0)*ing["gram"]/100)
                kh_ing   = round((ing.get("kh_100g",0) or 0)*ing["gram"]/100,1)
                ei_ing   = round((ing.get("eiwit_100g",0) or 0)*ing["gram"]/100,1)
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#22c55e;padding-top:6px;">' +
                    f'{kcal_ing}kcal · {kh_ing}g KH · {ei_ing}g ei</div>',
                    unsafe_allow_html=True)
            with ic4:
                if st.button("✕", key=f"r_del_{ii}"):
                    st.session_state["r_ingredienten"].pop(ii)
                    st.rerun()

        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

        # Zoek en voeg toe
        z1, z2, z3 = st.columns([1.5, 2, 3])
        with z1:
            bron = st.selectbox("Bron",
                ["🔍 Voedselbank","📋 Mijn bibliotheek","✏️ Manueel"],
                key="r_bron", label_visibility="collapsed")

        if bron == "✏️ Manueel":
            with st.expander("Manueel invoeren", expanded=False):
                ing_man = _product_formulier("r_man")
                if ing_man["naam"]:
                    if st.button("➕ Toevoegen", key="r_man_add", use_container_width=True):
                        st.session_state["r_ingredienten"].append(ing_man)
                        st.rerun()

        elif bron == "🔍 Voedselbank":
            with z2:
                zoek_db = st.text_input("Zoeken", placeholder="zoek product...",
                    key="r_db_zoek", label_visibility="collapsed")
            resultaten = [p for p in VOEDSEL_DB
                         if not zoek_db or zoek_db.lower() in p["naam"].lower()][:30]
            with z3:
                keuze_db = st.selectbox("Product",
                    ["— kies —"] + [f"{p['naam']} ({p['kcal']}kcal/100g)" for p in resultaten],
                    key="r_db_keuze", label_visibility="collapsed")
            if keuze_db != "— kies —" and resultaten:
                idx_k = ["— kies —"] + [f"{p['naam']} ({p['kcal']}kcal/100g)" for p in resultaten]
                prod_sel = resultaten[idx_k.index(keuze_db)-1] if keuze_db in idx_k else None
                if prod_sel:
                    ga1, ga2 = st.columns([3,1])
                    with ga1:
                        gram_db = st.number_input(f"Hoeveelheid (g) — standaard {prod_sel['portie']}g",
                            1.0, 2000.0, float(prod_sel["portie"]), 5.0, key="r_db_gram")
                    with ga2:
                        if st.button("➕ Toevoegen", key="r_db_add", use_container_width=True):
                            st.session_state["r_ingredienten"].append({
                                "naam":prod_sel["naam"],"gram":gram_db,
                                "label":f"{gram_db}g",
                                "kcal_100g":prod_sel["kcal"],"kh_100g":prod_sel["kh"],
                                "eiwit_100g":prod_sel["eiwit"],"vet_100g":prod_sel["vet"],
                                "vezels_100g":prod_sel["vezels"],"natrium_100g":prod_sel["natrium"],
                            })
                            st.session_state.pop("r_db_keuze",None)
                            st.rerun()

        else:  # Mijn bibliotheek
            bib_alle = _laad_gecombineerde_bibliotheek(user_id)
            with z2:
                zoek_bib = st.text_input("Zoeken", placeholder="zoek product...",
                    key="r_bib_zoek", label_visibility="collapsed")
            bib_res = [p for p in bib_alle
                      if not zoek_bib or zoek_bib.lower() in p["naam"].lower()][:30]
            with z3:
                keuze_bib = st.selectbox("Product",
                    ["— kies —"] + [p["naam"] for p in bib_res],
                    key="r_bib_keuze", label_visibility="collapsed")
            if keuze_bib != "— kies —" and bib_res:
                prod_bib = next((p for p in bib_res if p["naam"]==keuze_bib), None)
                if prod_bib:
                    gb1, gb2 = st.columns([3,1])
                    with gb1:
                        portie_bib = float(prod_bib.get("portie_g",100) or 100)
                        gram_bib = st.number_input(
                            f"Hoeveelheid (g) — {prod_bib.get('portie_label','')}",
                            1.0, 2000.0, portie_bib, 5.0, key="r_bib_gram")
                    with gb2:
                        if st.button("➕ Toevoegen", key="r_bib_add", use_container_width=True):
                            st.session_state["r_ingredienten"].append({
                                "naam":prod_bib["naam"],"gram":gram_bib,
                                "label":f"{gram_bib}g",
                                "kcal_100g":prod_bib.get("kcal_100g",0) or 0,
                                "kh_100g":prod_bib.get("kh_100g",0) or 0,
                                "eiwit_100g":prod_bib.get("eiwit_100g",0) or 0,
                                "vet_100g":prod_bib.get("vet_100g",0) or 0,
                                "vezels_100g":prod_bib.get("vezels_100g",0) or 0,
                                "natrium_100g":prod_bib.get("natrium_100g",0) or 0,
                            })
                            st.session_state.pop("r_bib_keuze",None)
                            st.rerun()


        _sectie("BEREIDING", "#22c55e")
        r_bereiding = st.text_area("Bereidingswijze", key="r_bereiding", height=80,
            placeholder="1. Kook 3 min. 2. Voeg fruit toe. 3. Serveer.")

        if ingredienten_data and totaal_kcal > 0:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;padding:12px;margin:10px 0;">'
                f'<div style="font-size:0.7rem;color:#22c55e;margin-bottom:6px;">TOTAAL RECEPT</div>'
                f'<div style="display:flex;gap:16px;">'
                f'<span style="color:#f97316;font-weight:700;">{round(totaal_kcal)}kcal</span>'
                f'<span style="color:#22c55e;">{round(totaal_kh,1)}g KH</span>'
                f'<span style="color:#3b82f6;">{round(totaal_eiwit,1)}g eiwit</span>'
                f'<span style="color:#8b5cf6;">{round(totaal_vet,1)}g vet</span>'
                f'</div></div>',
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if r_naam and ingredienten_data:
            if st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True):
                recept = {
                    "naam":r_naam.strip(),"type":r_type,
                    "kcal":round(totaal_kcal),"kh":round(totaal_kh,1),
                    "eiwit":round(totaal_eiwit,1),"vet":round(totaal_vet,1),
                    "vezels":round(totaal_vezels,1),"natrium":round(totaal_natrium),
                    "ingredienten":_j.dumps(ingredienten_data),
                    "bereiding":r_bereiding.strip() if r_bereiding else "",
                    "is_globaal":st.session_state.get("r_globaal",False),
                    "user_id":user_id,
                }
                try:
                    _get_supabase().table("fuelc_recepten_eigen").insert(recept).execute()
                    st.success(f"✅ '{r_naam}' opgeslagen!")
                    for k in [k for k in st.session_state if k.startswith(("r_","ing_"))]:
                        st.session_state.pop(k,None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Fout: {e}")
        else:
            st.button("💾 Recept opslaan", key="r_opslaan", use_container_width=True, disabled=True)

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            r = _get_supabase().table("fuelc_recepten_eigen").select("*")                .or_(f"user_id.eq.{user_id},is_globaal.eq.true").order("naam").execute()
            eigen_recepten = r.data or []
        except: eigen_recepten = []
        TYPE_LABEL = {"ontbijt":"🌅","tussendoor":"🍎","lunch":"🥗","avond":"🍽️"}
        for rec in eigen_recepten:
            ing = rec.get("ingredienten") or []
            if isinstance(ing,str):
                try: ing = _j.loads(ing)
                except: ing = []
            globaal_badge = " 🌍" if rec.get("is_globaal") else ""
            with st.expander(
                f"{TYPE_LABEL.get(rec.get('type',''),'🍴')} {rec.get('naam','')}{globaal_badge} — "
                f"{rec.get('kcal',0)}kcal · {rec.get('kh',0)}g KH · {rec.get('eiwit',0)}g eiwit",
                expanded=False):
                for item in ing:
                    naam_i = item.get("naam","") if isinstance(item,dict) else ""
                    gram_i = item.get("gram",0) if isinstance(item,dict) else 0
                    label_i = item.get("label","") if isinstance(item,dict) else ""
                    st.markdown(f'<div style="font-size:0.78rem;color:#94a3b8;">· {naam_i} — {label_i or str(gram_i)+"g"}</div>', unsafe_allow_html=True)
                if rec.get("bereiding"):
                    st.markdown(f'<div style="font-size:0.75rem;color:#64748b;">👨‍🍳 {rec["bereiding"]}</div>', unsafe_allow_html=True)
                if rec.get("user_id") == user_id or user_id == "22019eac-30b9-471e-88f3-58c7e80a4876":
                    if st.button("🗑 Verwijderen", key=f"r_del_{rec['id']}"):
                        try:
                            _get_supabase().table("fuelc_recepten_eigen").delete().eq("id",rec["id"]).execute()
                            st.rerun()
                        except Exception as e: st.error(str(e))




def _stap_bibliotheek(user: dict):
    user_id = user.get("id", "")
    _sectie("VOEDSELBIBLIOTHEEK", "#22c55e")

    tab_add, tab_db, tab_scan, tab_lijst, tab_recepten, tab_community = st.tabs([
        "➕  Manueel toevoegen",
        "🔍  Voedselbank zoeken",
        "📷  Etiketscan",
        "📋  Mijn bibliotheek",
        "🍴  Recepten",
        "🌍  Community",
    ])

    with tab_add:
        st.markdown("<br>", unsafe_allow_html=True)
        product_data = _product_formulier("bib")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.pop("bib_saved", False):
            st.success("✅ Product opgeslagen in je bibliotheek!")

        if product_data["naam"]:
            if st.button("💾 Product opslaan", key="bib_opslaan", use_container_width=True):
                product_data["bron"] = "manueel"
                if _sla_product_op(user_id, product_data):
                    st.session_state["bib_saved"] = True
                    for k in [k for k in st.session_state if k.startswith("bib_") and k != "bib_saved"]:
                        st.session_state.pop(k, None)
                    st.rerun()
        else:
            st.button("💾 Product opslaan", key="bib_opslaan", use_container_width=True, disabled=True)

    with tab_db:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ZOEKEN IN VOEDSELBANK", "#22c55e")
        db_zoek = st.text_input("Zoeken", placeholder="bijv. havermout, banaan...",
            key="db_zoek", label_visibility="collapsed")
        db_cat  = st.selectbox("Categorie", ["Alle"]+CATEGORIE_OPTIES,
            key="db_cat_filter", label_visibility="collapsed")
        zoek_l  = db_zoek.lower().strip() if db_zoek else ""
        db_res  = [p for p in VOEDSEL_DB
                   if (not zoek_l or zoek_l in p["naam"].lower())
                   and (db_cat=="Alle" or p["cat"]==db_cat)]
        st.markdown(f'<div style="font-size:0.72rem;color:#64748b;margin:6px 0;">{len(db_res)} product(en)</div>', unsafe_allow_html=True)

        for i, p in enumerate(db_res[:50]):
            with st.expander(f"{p['naam']} — {p['portie_label']} · {p['kcal']}kcal/100g", expanded=False):
                mc1,mc2,mc3,mc4 = st.columns(4)
                for col,lbl,val,kl in [(mc1,"KCAL",p["kcal"],"#f97316"),(mc2,"KH",f'{p["kh"]}g',"#22c55e"),(mc3,"EIWIT",f'{p["eiwit"]}g',"#3b82f6"),(mc4,"VET",f'{p["vet"]}g',"#8b5cf6")]:
                    with col:
                        st.markdown(f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;"><div style="font-size:0.6rem;color:#64748b;">{lbl}</div><div style="font-size:0.9rem;font-weight:700;color:{kl};">{val}</div></div>', unsafe_allow_html=True)
                extra_db = [
                    f'Vezels: {p["vezels"]}g',
                    f'Natrium: {p["natrium"]}mg',
                ]
                if p.get("kalium"):    extra_db.append(f'Kalium: {p["kalium"]}mg')
                if p.get("calcium"):   extra_db.append(f'Calcium: {p["calcium"]}mg')
                if p.get("ijzer"):     extra_db.append(f'IJzer: {p["ijzer"]}mg')
                if p.get("magnesium"): extra_db.append(f'Magnesium: {p["magnesium"]}mg')
                if p.get("vitc"):      extra_db.append(f'Vit C: {p["vitc"]}mg')
                if p.get("vitd"):      extra_db.append(f'Vit D: {p["vitd"]}µg')
                if p.get("vitb12"):    extra_db.append(f'Vit B12: {p["vitb12"]}µg')
                if p.get("omega3"):    extra_db.append(f'Omega-3: {p["omega3"]}g')
                if p.get("gi"):        extra_db.append(f'GI: {p["gi"]}')
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#64748b;margin:6px 0;">' +
                    ' · '.join(extra_db) + '</div>',
                    unsafe_allow_html=True)
                eenheid_db = st.selectbox("Eenheid", ["gram (g)","stuk","snede","eetlepel (15ml)","kopje (150ml)","glas (200ml)","portie","ml"], key=f"db_e_{i}")
                EG = {"gram (g)":1.0,"stuk":1.0,"snede":1.0,"eetlepel (15ml)":15.0,"kopje (150ml)":150.0,"glas (200ml)":200.0,"portie":float(p["portie"]),"ml":1.0}
                hoev_db = st.number_input("Hoeveelheid", 0.1, 500.0, 1.0 if eenheid_db not in ("gram (g)","ml") else float(p["portie"]), 0.5, key=f"db_h_{i}")
                portie_g_db = round(hoev_db * EG.get(eenheid_db,1.0), 1)
                st.markdown(f'<div style="font-size:0.75rem;color:#22c55e;">= {portie_g_db}g · {round(p["kcal"]*portie_g_db/100)}kcal per portie</div>', unsafe_allow_html=True)
                if st.button("📥 Toevoegen aan bibliotheek", key=f"db_import_{i}", use_container_width=True):
                    prod = {
                        "naam":p["naam"],"categorie":p["cat"],"bron":"databank",
                        "portie_g":portie_g_db,"portie_label":f"{hoev_db} {eenheid_db}",
                        "kcal_100g":p["kcal"],"kh_100g":p["kh"],"suikers_100g":p["suikers"],
                        "eiwit_100g":p["eiwit"],"vet_100g":p["vet"],"verzadigd_100g":p["verz"],
                        "vezels_100g":p["vezels"],"natrium_100g":p["natrium"],
                        "kalium_100g":p.get("kalium"),"calcium_100g":p.get("calcium"),
                        "ijzer_100g":p.get("ijzer"),"magnesium_100g":p.get("magnesium"),
                        "vitc_100g":p.get("vitc"),"vitd_100g":p.get("vitd"),
                        "vitb12_100g":p.get("vitb12"),"omega3_100g":p.get("omega3"),
                        "gi":p.get("gi"),"favoriet":False,"user_id":user_id,
                    }
                    if _sla_product_op(user_id, prod):
                        st.success(f"✅ '{p['naam']}' toegevoegd!")
                        st.rerun()

    with tab_scan:
        st.markdown("<br>", unsafe_allow_html=True)
        _sectie("ETIKETSCAN VIA AI", "#22c55e")
        scan_foto = st.file_uploader("Foto van etiket (JPG/PNG)", type=["jpg","jpeg","png"], key="scan_foto")
        if scan_foto:
            import base64, requests as _req2, json as _json_s, os as _os
            foto_bytes = scan_foto.read()
            foto_b64   = base64.b64encode(foto_bytes).decode()
            foto_mime  = "image/jpeg" if scan_foto.name.lower().endswith((".jpg",".jpeg")) else "image/png"
            st.image(scan_foto, width=300)
            if st.button("🤖 Scan etiket", key="scan_btn", use_container_width=True):
                with st.spinner("AI leest het etiket..."):
                    try:
                        resp = _req2.post("https://api.anthropic.com/v1/messages",
                            json={"model":"claude-sonnet-4-5","max_tokens":1000,"messages":[{"role":"user","content":[
                                {"type":"image","source":{"type":"base64","media_type":foto_mime,"data":foto_b64}},
                                {"type":"text","text":"Lees de voedingswaarden per 100g uit dit etiket. Geef ENKEL JSON: {naam,kcal_100g,kh_100g,suikers_100g,vezels_100g,eiwit_100g,vet_100g,verzadigd_100g,natrium_100g,portie_g,gi}. Geen uitleg."}
                            ]}]},
                            headers={"x-api-key":_os.environ.get("ANTHROPIC_API_KEY",""),
                                     "anthropic-version":"2023-06-01","content-type":"application/json"},
                            timeout=30).json()
                        tekst = resp["content"][0]["text"].strip().strip("```json").strip("```").strip()
                        st.session_state["scan_result"] = _json_s.loads(tekst)
                        st.success("✅ Etiket uitgelezen!")
                    except Exception as e:
                        st.error(f"Scan mislukt: {e}")

        scan_result = st.session_state.get("scan_result",{})
        if scan_result:
            st.markdown("<br>", unsafe_allow_html=True)
            _sectie("GESCANDE WAARDEN — controleer en pas aan", "#86efac")
            scan_product = _product_formulier("scan", defaults=scan_result)
            if scan_product["naam"]:
                if st.button("💾 Opslaan", key="scan_opslaan", use_container_width=True):
                    scan_product["bron"] = "etiketscan"
                    if _sla_product_op(user_id, scan_product):
                        st.success(f"✅ Opgeslagen!")
                        for k in [k for k in st.session_state if k.startswith("scan_")]:
                            st.session_state.pop(k,None)
                        st.rerun()

    with tab_lijst:
        st.markdown("<br>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns([3,2,1])
        with f1: zoek = st.text_input("Zoeken", placeholder="bijv. havermout", key="bib_zoek", label_visibility="collapsed")
        with f2: filter_cat = st.selectbox("Categorie", ["Alle"]+CATEGORIE_OPTIES, key="bib_filter_cat", label_visibility="collapsed")
        with f3: fav_f = st.selectbox("Filter", ["Alle","⭐ Fav"], key="bib_fav_f", label_visibility="collapsed")
        producten = _laad_bibliotheek(user_id, zoek, filter_cat)
        if fav_f == "⭐ Fav": producten = [p for p in producten if p.get("favoriet")]
        st.markdown(f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">{len(producten)} product(en)</div>', unsafe_allow_html=True)
        for p in producten:
            portie  = p.get("portie_g") or 0
            kcal    = p.get("kcal_100g") or 0
            kh      = p.get("kh_100g") or 0
            eiwit   = p.get("eiwit_100g") or 0
            vet     = p.get("vet_100g") or 0
            fav_ster = "⭐ " if p.get("favoriet") else ""
            with st.expander(f"{fav_ster}{p.get('naam','')} — {p.get('categorie','')}", expanded=False):
                mc1,mc2,mc3,mc4 = st.columns(4)
                for col,lbl,val,kl in [(mc1,"KCAL",kcal,"#f97316"),(mc2,"KH",f"{kh}g","#22c55e"),(mc3,"EIWIT",f"{eiwit}g","#3b82f6"),(mc4,"VET",f"{vet}g","#8b5cf6")]:
                    with col:
                        st.markdown(f'<div style="background:#0f172a;border-radius:6px;padding:8px;text-align:center;"><div style="font-size:0.6rem;color:#64748b;">{lbl}</div><div style="font-size:0.9rem;font-weight:700;color:{kl};">{val}</div></div>', unsafe_allow_html=True)
                if portie > 0:
                    st.markdown(
                        f'<div style="font-size:0.72rem;color:#64748b;margin-top:6px;">' +
                        f'Per portie ({p.get("portie_label") or str(portie)+"g"}): ' +
                        f'{round(kcal*portie/100)}kcal · {round(kh*portie/100,1)}g KH · ' +
                        f'{round(eiwit*portie/100,1)}g eiwit · {round(vet*portie/100,1)}g vet</div>',
                        unsafe_allow_html=True)

                # Extra voedingsstoffen
                extra = []
                if p.get("vezels_100g"):    extra.append(f'Vezels: {p["vezels_100g"]}g')
                if p.get("natrium_100g"):   extra.append(f'Natrium: {round(p["natrium_100g"])}mg')
                if p.get("kalium_100g"):    extra.append(f'Kalium: {round(p["kalium_100g"])}mg')
                if p.get("calcium_100g"):   extra.append(f'Calcium: {round(p["calcium_100g"])}mg')
                if p.get("ijzer_100g"):     extra.append(f'IJzer: {p["ijzer_100g"]}mg')
                if p.get("magnesium_100g"): extra.append(f'Magnesium: {round(p["magnesium_100g"])}mg')
                if p.get("vitc_100g"):      extra.append(f'Vit C: {p["vitc_100g"]}mg')
                if p.get("vitd_100g"):      extra.append(f'Vit D: {p["vitd_100g"]}µg')
                if p.get("vitb12_100g"):    extra.append(f'Vit B12: {p["vitb12_100g"]}µg')
                if p.get("omega3_100g"):    extra.append(f'Omega-3: {p["omega3_100g"]}g')
                if p.get("gi"):             extra.append(f'GI: {p["gi"]}')
                if extra:
                    st.markdown(
                        f'<div style="font-size:0.7rem;color:#64748b;margin-top:4px;">' +
                        ' · '.join(extra) + '</div>',
                        unsafe_allow_html=True)
                ba1, ba2 = st.columns(2)
                with ba1:
                    fav_lbl = "★ Verwijder favoriet" if p.get("favoriet") else "☆ Favoriet"
                    if st.button(fav_lbl, key=f"bib_fav_{p['id']}", use_container_width=True):
                        if _update_product(p["id"], {"favoriet": not p.get("favoriet")}):
                            _laad_bibliotheek_raw.clear()
                            _laad_gecombineerde_bibliotheek_raw.clear()
                            st.rerun()
                with ba2:
                    if st.button("🗑 Verwijderen", key=f"bib_del_{p['id']}", use_container_width=True):
                        if _verwijder_product(p["id"]):
                            st.success("Verwijderd.")
                            st.rerun()

    with tab_recepten:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_receptenbeheer(user_id)

    with tab_community:
        _render_community_tab(user)



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
# BLOK 4 — WEEKSCHEMA v8
# ═══════════════════════════════════════════════════════════════════════════════

DAGEN_NL = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

MAALTIJD_TEMPLATES = {
    "Klassiek (3 maaltijden)": [
        {"naam":"Ontbijt",   "tijdstip":"07:30","type":"ontbijt"},
        {"naam":"Lunch",     "tijdstip":"12:30","type":"lunch"},
        {"naam":"Avondmaal", "tijdstip":"18:30","type":"avond"},
    ],
    "Intermittent 16:8": [
        {"naam":"Eerste maaltijd","tijdstip":"12:00","type":"ontbijt"},
        {"naam":"Tweede maaltijd","tijdstip":"16:00","type":"lunch"},
        {"naam":"Derde maaltijd", "tijdstip":"19:30","type":"avond"},
    ],
    "Intermittent 18:6": [
        {"naam":"Eerste maaltijd","tijdstip":"13:00","type":"ontbijt"},
        {"naam":"Tweede maaltijd","tijdstip":"18:30","type":"avond"},
    ],
}

TUSSENDOOR_OPTIES = [
    {"naam":"Tussendoor voormiddag","tijdstip":"10:00","type":"tussendoor"},
    {"naam":"Tussendoor namiddag",  "tijdstip":"15:00","type":"tussendoor"},
    {"naam":"Avondsnack",           "tijdstip":"21:00","type":"tussendoor"},
]

HERSTEL_MACROS = {"kh_pct":52,"eiwit_pct":33,"vet_pct":15}


def _kies_recept(moment_type, energie_doel, alle_recepten=None, gebruikte_ids=None):
    """Kies recept — vermijd al gebruikte recepten voor variatie."""
    pool = alle_recepten if alle_recepten else RECEPT_DB
    kandidaten = [r for r in pool if r.get("type") == moment_type]
    if not kandidaten: kandidaten = pool
    # Filter gebruikte recepten voor variatie
    if gebruikte_ids:
        vers = [r for r in kandidaten if r.get("id","") not in gebruikte_ids and r.get("naam","") not in gebruikte_ids]
        if vers: kandidaten = vers
    return min(kandidaten, key=lambda r: abs((r.get("kcal") or 0) - energie_doel))


def _bereken_moment_doelen(energie_basis, momenten, training_timing, profiel, training_kcal=0, verdeling_pct=None):
    """Bereken energie per moment met custom verdeling."""
    energie_dag = energie_basis + int(training_kcal or 0)
    kh_pct    = profiel.get("kh_doel_pct", 50) or 50
    eiwit_pct = profiel.get("eiwit_doel_pct", 25) or 25
    vet_pct   = profiel.get("vet_doel_pct", 25) or 25

    # Gebruik custom verdeling als opgegeven, anders standaard
    if verdeling_pct and len(verdeling_pct) == len(momenten):
        # Normaliseer naar 100%
        totaal = sum(verdeling_pct.values()) or 100
        pcts_per_moment = {i: round(v/totaal*100) for i,v in verdeling_pct.items()}
    else:
        # Standaard verdeling
        vaste   = [m for m in momenten if m["type"] != "tussendoor"]
        n_td    = len([m for m in momenten if m["type"] == "tussendoor"])
        pct_td  = 8  # per tussendoor
        rest    = 100 - n_td * pct_td
        if len(vaste) == 3:   base = {"ontbijt":30,"lunch":35,"avond":35}
        elif len(vaste) == 2:
            types = [m["type"] for m in vaste]
            base  = {"ontbijt":45,"avond":55} if "lunch" not in types else {"ontbijt":40,"lunch":60}
        else: base = {"ontbijt":100}
        # Schaal naar rest%
        factor = rest/100
        base   = {k: round(v*factor) for k,v in base.items()}
        pcts_per_moment = {}
        for i, m in enumerate(momenten):
            if m["type"] == "tussendoor":
                pcts_per_moment[i] = pct_td
            else:
                pcts_per_moment[i] = base.get(m["type"], 20)

    # Herstelmoment na training
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
        e = round(energie_dag * pcts_per_moment.get(i, 20) / 100)
        if i == herstel_idx:
            kh_m  = round(e * HERSTEL_MACROS["kh_pct"] / 100 / 4)
            ei_m  = round(e * HERSTEL_MACROS["eiwit_pct"] / 100 / 4)
            vt_m  = round(e * HERSTEL_MACROS["vet_pct"] / 100 / 9)
        else:
            kh_m  = round(e * kh_pct / 100 / 4)
            ei_m  = round(e * eiwit_pct / 100 / 4)
            vt_m  = round(e * vet_pct / 100 / 9)
        result.append({**m, "energie_doel":e, "kh_doel_g":kh_m, "eiwit_doel_g":ei_m, "vet_doel_g":vt_m, "pct":pcts_per_moment.get(i,20)})
    return result


def _laad_dagschema(user_id, datum):
    try:
        r = _get_supabase().table("fuelc_dagschema").select("*").eq("user_id",user_id).eq("datum",datum).execute()
        return r.data[0] if r.data else {}
    except: return {}


def _sla_dagschema_op(user_id, datum, schema):
    try:
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
        st.error(f"Fout schema: {e}")
        return None


def _laad_dagboek_items(user_id, datum, moment):
    try:
        cache_key = f"dagboek_cache_{datum}"
        if cache_key not in st.session_state:
            r = _get_supabase().table("fuelc_dagboek")\
                .select("id,datum,moment,naam,hoeveelheid_g,kcal,kh_g,eiwit_g,vet_g,vezels_g,product_id")\
                .eq("user_id",user_id).eq("datum",datum).execute()
            st.session_state[cache_key] = r.data or []
        return [i for i in st.session_state[cache_key] if i.get("moment") == moment]
    except: return []


def _invalideer_dagboek_cache(datum):
    st.session_state.pop(f"dagboek_cache_{datum}", None)


def _verwijder_dagboek_item(item_id, datum=None):
    try:
        _get_supabase().table("fuelc_dagboek").delete().eq("id",item_id).execute()
        if datum: _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _verwijder_alle_items_moment(user_id, datum, moment_idx):
    try:
        items = _laad_dagboek_items(user_id, datum, moment_idx)
        for item in items:
            _get_supabase().table("fuelc_dagboek").delete().eq("id",item["id"]).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _sla_dagboek_item(user_id, datum, moment, product, hoeveelheid):
    try:
        f = hoeveelheid / 100
        prod_id = product.get("id","")
        if not prod_id or str(prod_id).startswith("db_"):
            prod_id = None
        _get_supabase().table("fuelc_dagboek").insert({
            "user_id":user_id,"datum":datum,"moment":moment,
            "product_id":prod_id,"naam":product["naam"],
            "hoeveelheid_g":hoeveelheid,
            "kcal":    round((product.get("kcal_100g") or 0)*f, 1),
            "kh_g":    round((product.get("kh_100g") or 0)*f, 1),
            "eiwit_g": round((product.get("eiwit_100g") or 0)*f, 1),
            "vet_g":   round((product.get("vet_100g") or 0)*f, 1),
            "vezels_g":round((product.get("vezels_100g") or 0)*f, 1),
        }).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except Exception as e:
        st.error(f"Fout opslaan: {e}")
        return False


def _update_dagboek_item(item_id, datum, hoeveelheid, kcal_100, kh_100, ei_100, vt_100):
    try:
        f = hoeveelheid / 100
        _get_supabase().table("fuelc_dagboek").update({
            "hoeveelheid_g":hoeveelheid,
            "kcal":    round((kcal_100 or 0)*f, 1),
            "kh_g":    round((kh_100 or 0)*f, 1),
            "eiwit_g": round((ei_100 or 0)*f, 1),
            "vet_g":   round((vt_100 or 0)*f, 1),
        }).eq("id", item_id).execute()
        _invalideer_dagboek_cache(datum)
        return True
    except: return False


def _sla_recept_items(user_id, datum, moment_idx, recept, bibliotheek):
    """Sla ingrediënten van recept op als dagboek items."""
    n = max(len(recept.get("ingredienten",[])), 1)
    for naam, gram in recept.get("ingredienten", []):
        prod = next((p for p in bibliotheek if p["naam"].lower() == naam.lower()), None)
        if prod is None:
            prod = {
                "naam":naam,"id":f"db_{naam}",
                "kcal_100g": round((recept.get("kcal",0)/n)/(gram/100)) if gram>0 else 0,
                "kh_100g":   round((recept.get("kh",0)/n)/(gram/100)) if gram>0 else 0,
                "eiwit_100g":round((recept.get("eiwit",0)/n)/(gram/100)) if gram>0 else 0,
                "vet_100g":  round((recept.get("vet",0)/n)/(gram/100)) if gram>0 else 0,
                "vezels_100g":0,
            }
        _sla_dagboek_item(user_id, datum, moment_idx, prod, float(gram))


def _stap_dagschema(user: dict):
    import json as _json
    from datetime import date as _date, timedelta as _td

    user_id     = user.get("id","")
    profiel     = st.session_state.get("fc_profiel", {})
    energie_dag = int(profiel.get("energie_doel", 2000) or 2000)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTIE 1 — EETPATROON INSTELLINGEN
    # ══════════════════════════════════════════════════════════════════════════
    _sectie("EETPATROON & VERDELING", "#22c55e")
    st.markdown(
        '<div style="font-size:0.78rem;color:#64748b;margin-bottom:12px;">'
        'Stel je eetpatroon in — wordt opgeslagen en toegepast op alle dagen.</div>',
        unsafe_allow_html=True)

    ep1, ep2 = st.columns(2)
    with ep1:
        patroon = st.selectbox("Eetpatroon",
            list(MAALTIJD_TEMPLATES.keys()),
            index=list(MAALTIJD_TEMPLATES.keys()).index(profiel.get("eet_patroon","Klassiek (3 maaltijden)"))
                  if profiel.get("eet_patroon") in MAALTIJD_TEMPLATES else 0,
            key="ep_patroon")
    with ep2:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;padding-top:28px;">Tussendoor momenten:</div>', unsafe_allow_html=True)

    td_cols = st.columns(3)
    tussendoor_aan = []
    for ti, td in enumerate(TUSSENDOOR_OPTIES):
        with td_cols[ti]:
            aan = st.checkbox(td["naam"], key=f"ep_td_{ti}",
                value=bool(profiel.get(f"td_{ti}", False)))
            if aan: tussendoor_aan.append(ti)

    # Bouw momenten
    def _bouw_momenten(patroon_naam, td_aan):
        basis = [m.copy() for m in MAALTIJD_TEMPLATES.get(patroon_naam, MAALTIJD_TEMPLATES["Klassiek (3 maaltijden)"])]
        for ti in td_aan:
            basis.append(TUSSENDOOR_OPTIES[ti].copy())
        return sorted(basis, key=lambda x: x.get("tijdstip","00:00"))

    momenten_basis = _bouw_momenten(patroon, tussendoor_aan)

    # Energieverdeling per moment
    _sectie("ENERGIEVERDELING", "#22c55e")
    st.markdown(
        '<div style="font-size:0.75rem;color:#64748b;margin-bottom:10px;">'
        'Pas de energieverdeling per maaltijdmoment aan. Totaal moet 100% zijn.</div>',
        unsafe_allow_html=True)

    verdeling_pct = {}
    vd_cols = st.columns(len(momenten_basis))
    totaal_v = 0
    for i, m in enumerate(momenten_basis):
        with vd_cols[i]:
            standaard = 8 if m["type"] == "tussendoor" else (
                30 if m["type"]=="ontbijt" and len([x for x in momenten_basis if x["type"]!="tussendoor"])==3 else
                35 if m["type"] in ("lunch","avond") else 40
            )
            opgeslagen = profiel.get(f"vd_{i}", standaard)
            v = st.number_input(
                f"{m['naam']}\n{m['tijdstip']}",
                1, 60, int(opgeslagen), 1,
                key=f"ep_vd_{i}")
            verdeling_pct[i] = v
            totaal_v += v

    # Toon totaal
    kleur_tot = "#22c55e" if totaal_v == 100 else "#ef4444"
    st.markdown(
        f'<div style="font-size:0.8rem;font-weight:700;color:{kleur_tot};margin-bottom:8px;">'
        f'Totaal: {totaal_v}% {"✓" if totaal_v==100 else f"(moet 100% zijn, nu {totaal_v-100:+d}%)"}'
        f'</div>',
        unsafe_allow_html=True)

    # Opslaan eetpatroon
    if st.button("💾 Eetpatroon opslaan", key="ep_opslaan"):
        updates = {
            "eet_patroon": patroon,
        }
        for ti in range(3):
            updates[f"td_{ti}"] = ti in tussendoor_aan
        for i, v in verdeling_pct.items():
            updates[f"vd_{i}"] = v
        if _sla_profiel_op(user_id, updates):
            st.session_state.fc_profiel.update(updates)
            st.success("✅ Eetpatroon opgeslagen!")
            st.rerun()

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTIE 2 — WEEKSCHEMA
    # ══════════════════════════════════════════════════════════════════════════
    _sectie("WEEKSCHEMA", "#22c55e")

    wk1, wk2 = st.columns([2,4])
    with wk1:
        week_start = st.date_input("Week van", value=_date.today(), key="week_start")
        maandag    = week_start - _td(days=week_start.weekday())
    with wk2:
        st.markdown(
            f'<div style="padding-top:28px;font-size:0.8rem;color:#64748b;">'
            f'{maandag.strftime("%d/%m/%Y")} — {(maandag+_td(days=6)).strftime("%d/%m/%Y")}</div>',
            unsafe_allow_html=True)

    # Data laden
    bibliotheek      = _laad_gecombineerde_bibliotheek(user_id)
    alle_trainingen  = _laad_trainingen(user_id)
    alle_recepten    = _laad_alle_recepten(user_id)

    # Recepten per type voor snelle lookup
    recepten_per_type = {}
    for r in alle_recepten:
        t = r.get("type","")
        recepten_per_type.setdefault(t, []).append(r)

    @st.cache_data(ttl=60)
    def _laad_week_schemas(uid, ma, zo):
        try:
            r = _get_supabase().table("fuelc_dagschema").select("*")\
                .eq("user_id",uid).gte("datum",ma).lte("datum",zo).execute()
            return {row["datum"]: row for row in (r.data or [])}
        except: return {}

    week_schemas = _laad_week_schemas(user_id, str(maandag), str(maandag+_td(days=6)))

    # Bijhoud gebruikte recepten voor variatie per week
    gebruikte_recept_namen = set()

    # ── 7 dagen ───────────────────────────────────────────────────────────────
    for dag_idx in range(7):
        dag_datum  = maandag + _td(days=dag_idx)
        dag_str    = str(dag_datum)
        dag_label  = f"{DAGEN_NL[dag_idx]} {dag_datum.strftime('%d/%m')}"
        is_vandaag = dag_datum == _date.today()
        dag_open   = f"dag_open_{dag_str}"

        # Training
        training_kcal_dag = sum(t.get("kcal_verbranding",0) or 0
                                for t in alle_trainingen
                                if t.get("datum","")[:10] == dag_str)
        energie_totaal    = energie_dag + training_kcal_dag

        # Momenten met opgeslagen verdeling
        training_dag = st.session_state.get(f"tr_{dag_str}", "Geen training")
        momenten     = _bereken_moment_doelen(
            energie_dag, momenten_basis, training_dag, profiel,
            training_kcal_dag, verdeling_pct)

        schema_dag = week_schemas.get(dag_str, {})
        if schema_dag.get("momenten_json"):
            try: momenten = _json.loads(schema_dag["momenten_json"])
            except: pass

        # Dag totaal
        alle_items = []
        for _mi in range(len(momenten) + 1):
            alle_items += _laad_dagboek_items(user_id, dag_str, _mi)
        tot_kcal  = sum(i.get("kcal",0) or 0 for i in alle_items)
        pct_dag   = min(100, round(tot_kcal/energie_totaal*100)) if energie_totaal > 0 else 0
        k_dag     = "#22c55e" if pct_dag >= 80 else ("#fbbf24" if pct_dag >= 40 else "#334155")

        # ── Dag header ────────────────────────────────────────────────────────
        h1, h2, h3, h4 = st.columns([3,2,1,1])
        with h1:
            tr_b = f'<span style="font-size:0.65rem;color:#22c55e;margin-left:6px;">🏃 +{training_kcal_dag}kcal</span>' if training_kcal_dag > 0 else ""
            vd_b = '<span style="background:#f97316;color:white;border-radius:4px;font-size:0.6rem;padding:1px 6px;margin-left:6px;">VANDAAG</span>' if is_vandaag else ""
            st.markdown(
                f'<div style="padding:8px 0;font-size:0.95rem;font-weight:800;color:#f8fafc;">'
                f'{dag_label}{vd_b}{tr_b}</div>', unsafe_allow_html=True)
        with h2:
            training_dag = st.selectbox("Training",
                ["Geen training","Ochtend (voor 11u)","Middag (11u-15u)","Avond (na 15u)"],
                key=f"tr_{dag_str}", label_visibility="collapsed")
        with h3:
            if st.button("📋 Dagplan", key=f"gen_{dag_str}", use_container_width=True):
                mom = _bereken_moment_doelen(
                    energie_dag, momenten_basis, training_dag, profiel,
                    training_kcal_dag, verdeling_pct)
                for mi, m in enumerate(mom):
                    bestaande = _laad_dagboek_items(user_id, dag_str, mi)
                    if not bestaande:
                        recept = _kies_recept(m["type"], m["energie_doel"],
                                              alle_recepten, gebruikte_recept_namen)
                        gebruikte_recept_namen.add(recept.get("naam",""))
                        _sla_recept_items(user_id, dag_str, mi, recept, bibliotheek)
                _sla_dagschema_op(user_id, dag_str, {
                    "energie_doel":    energie_totaal,
                    "kh_doel_g":       round(energie_totaal*(profiel.get("kh_doel_pct",50) or 50)/100/4),
                    "eiwit_doel_g":    round(energie_totaal*(profiel.get("eiwit_doel_pct",25) or 25)/100/4),
                    "vet_doel_g":      round(energie_totaal*(profiel.get("vet_doel_pct",25) or 25)/100/9),
                    "aantal_maaltijden": len(mom),
                    "momenten_json":   _json.dumps(mom),
                    "training_timing": training_dag,
                    "eet_patroon":     patroon,
                })
                st.session_state[dag_open] = True
                _laad_week_schemas.clear()
                st.rerun()
        with h4:
            lbl = "▲" if st.session_state.get(dag_open) else "▼"
            if st.button(lbl, key=f"tog_{dag_str}", use_container_width=True):
                st.session_state[dag_open] = not st.session_state.get(dag_open, False)
                st.rerun()

        # Progressiebalk
        tr_info = f" · 🏃 +{training_kcal_dag}kcal" if training_kcal_dag > 0 else ""
        st.markdown(
            f'<div style="background:#1e293b;border-radius:3px;height:5px;margin-bottom:3px;">'
            f'<div style="width:{pct_dag}%;height:100%;background:{k_dag};border-radius:3px;"></div></div>'
            f'<div style="font-size:0.65rem;color:#64748b;margin-bottom:8px;">'
            f'{round(tot_kcal)} / {energie_totaal} kcal{tr_info}</div>',
            unsafe_allow_html=True)

        # ── Dag detail ────────────────────────────────────────────────────────
        if st.session_state.get(dag_open, False):

            for mi, moment in enumerate(momenten):
                m_naam  = moment.get("naam","")
                m_tijd  = moment.get("tijdstip","")
                e_doel  = moment.get("energie_doel", 0)
                kh_doel = moment.get("kh_doel_g", 0)
                ei_doel = moment.get("eiwit_doel_g", 0)
                vt_doel = moment.get("vet_doel_g", 0)
                m_type  = moment.get("type","")
                m_pct   = moment.get("pct", 0)

                items   = _laad_dagboek_items(user_id, dag_str, mi)
                m_kcal  = sum(i.get("kcal",0) or 0 for i in items)
                m_kh    = sum(i.get("kh_g",0) or 0 for i in items)
                m_eiwit = sum(i.get("eiwit_g",0) or 0 for i in items)
                m_vet   = sum(i.get("vet_g",0) or 0 for i in items)
                pct_m   = min(100, round(m_kcal/e_doel*100)) if e_doel > 0 else 0
                k_m     = "#22c55e" if pct_m>=80 else ("#fbbf24" if pct_m>=40 else "#475569")
                if m_kcal > e_doel*1.1: k_m = "#ef4444"

                # Moment header
                pct_label = f'<span style="font-size:0.65rem;color:#475569;margin-left:6px;">{m_pct}%</span>' if m_pct else ""
                st.markdown(
                    f'<div style="border-left:3px solid {k_m};padding:8px 12px;margin:6px 0 4px;background:#1e293b;border-radius:0 8px 8px 0;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><span style="font-size:0.7rem;color:#64748b;">{m_tijd}</span>'
                    f'<span style="font-size:0.88rem;font-weight:700;color:#f8fafc;margin-left:8px;">{m_naam}</span>'
                    f'{pct_label}</div>'
                    f'<span style="font-size:0.78rem;font-weight:700;color:{k_m};">{round(m_kcal)}/{e_doel} kcal</span></div>'
                    f'<div style="background:#0f172a;border-radius:3px;height:3px;margin:5px 0;">'
                    f'<div style="width:{pct_m}%;height:100%;background:{k_m};border-radius:3px;"></div></div>'
                    f'<div style="font-size:0.67rem;color:#64748b;">'
                    f'KH {round(m_kh)}/{kh_doel}g · Eiwit {round(m_eiwit)}/{ei_doel}g · Vet {round(m_vet)}/{vt_doel}g'
                    f'</div></div>',
                    unsafe_allow_html=True)

                # Ingevoerde items — inline aanpasbaar
                for item in items:
                    hg       = float(item.get("hoeveelheid_g",100))
                    kcal_100 = round(item.get("kcal",0)*100/max(hg,1), 1)
                    kh_100   = round(item.get("kh_g",0)*100/max(hg,1), 1)
                    ei_100   = round(item.get("eiwit_g",0)*100/max(hg,1), 1)
                    vt_100   = round(item.get("vet_g",0)*100/max(hg,1), 1)

                    c1,c2,c3,c4 = st.columns([4,1.5,0.7,0.5])
                    with c1:
                        st.markdown(
                            f'<div style="font-size:0.82rem;color:#f1f5f9;padding:5px 0;">'
                            f'<b>{item.get("naam","")}</b>'
                            f'<span style="color:#64748b;font-size:0.7rem;"> · {round(item.get("kcal",0))}kcal</span>'
                            f'</div>', unsafe_allow_html=True)
                    with c2:
                        nieuwe_g = st.number_input("g",1.0,2000.0,hg,5.0,
                            key=f"g_{item['id']}", label_visibility="collapsed")
                    with c3:
                        if st.button("💾", key=f"upd_{item['id']}", help="Opslaan"):
                            _update_dagboek_item(item["id"],dag_str,nieuwe_g,kcal_100,kh_100,ei_100,vt_100)
                            st.rerun()
                    with c4:
                        if st.button("✕", key=f"del_{item['id']}"):
                            _verwijder_dagboek_item(item["id"],dag_str)
                            st.rerun()

                if items:
                    st.markdown(
                        f'<div style="font-size:0.72rem;font-weight:700;color:#f97316;padding:2px 0 4px;">'
                        f'▸ {round(m_kcal)}kcal · {round(m_kh)}g KH · {round(m_eiwit)}g eiwit · {round(m_vet)}g vet'
                        f'</div>', unsafe_allow_html=True)

                # ── Toevoegen: product OF recept ──────────────────────────────
                add_tab_key = f"add_mode_{dag_str}_{mi}"
                if add_tab_key not in st.session_state:
                    st.session_state[add_tab_key] = "product"

                mode_cols = st.columns([1,1,4])
                with mode_cols[0]:
                    if st.button("🥦 Product", key=f"mode_prod_{dag_str}_{mi}",
                                 type="primary" if st.session_state[add_tab_key]=="product" else "secondary"):
                        st.session_state[add_tab_key] = "product"
                        st.rerun()
                with mode_cols[1]:
                    if st.button("🍴 Recept", key=f"mode_rec_{dag_str}_{mi}",
                                 type="primary" if st.session_state[add_tab_key]=="recept" else "secondary"):
                        st.session_state[add_tab_key] = "recept"
                        st.rerun()

                if st.session_state[add_tab_key] == "product":
                    # Product toevoegen
                    az1, az2, az3 = st.columns([3,2,1])
                    with az1:
                        zoek = st.text_input("Zoek product", placeholder="typ om te zoeken...",
                            key=f"z_{dag_str}_{mi}", label_visibility="collapsed")
                    with az2:
                        cat_f = st.selectbox("Cat", ["Alle"]+CATEGORIE_OPTIES,
                            key=f"c_{dag_str}_{mi}", label_visibility="collapsed")
                    with az3:
                        fav_f = st.checkbox("⭐", key=f"f_{dag_str}_{mi}", help="Favorieten")

                    gefilterd = [p for p in bibliotheek
                                 if (not zoek or zoek.lower() in p["naam"].lower())
                                 and (cat_f=="Alle" or p.get("categorie","")==cat_f)
                                 and (not fav_f or p.get("favoriet",False))]

                    if gefilterd:
                        pz1,pz2,pz3 = st.columns([4,1.5,0.8])
                        with pz1:
                            keuze = st.selectbox("Product", ["— kies —"]+[p["naam"] for p in gefilterd],
                                key=f"pk_{dag_str}_{mi}", label_visibility="collapsed")
                        if keuze != "— kies —":
                            gekozen = next((p for p in gefilterd if p["naam"]==keuze), None)
                            if gekozen:
                                portie = float(gekozen.get("portie_g") or 100)
                                with pz2:
                                    hoev = st.number_input("g",1.0,2000.0,portie,5.0,
                                        key=f"h_{dag_str}_{mi}", label_visibility="collapsed")
                                with pz3:
                                    if st.button("➕", key=f"add_{dag_str}_{mi}", use_container_width=True):
                                        _sla_dagboek_item(user_id,dag_str,mi,gekozen,hoev)
                                        st.session_state.pop(f"pk_{dag_str}_{mi}",None)
                                        st.rerun()

                else:
                    # Recept toevoegen
                    recepten_type = recepten_per_type.get(m_type, []) + recepten_per_type.get("", [])
                    if not recepten_type:
                        recepten_type = alle_recepten

                    rz1, rz2 = st.columns([4,1])
                    with rz1:
                        rec_namen = [f"{r['naam']} ({r.get('kcal',0)}kcal)" for r in recepten_type]
                        rec_keuze = st.selectbox("Recept",
                            ["— kies recept —"] + rec_namen,
                            key=f"rk_{dag_str}_{mi}", label_visibility="collapsed")
                    with rz2:
                        if rec_keuze != "— kies recept —":
                            gekozen_rec = recepten_type[rec_namen.index(rec_keuze)] if rec_keuze in rec_namen else None
                            if gekozen_rec:
                                # Preview macro's
                                st.markdown(
                                    f'<div style="font-size:0.7rem;color:#22c55e;padding-top:6px;">'
                                    f'{gekozen_rec.get("kcal",0)}kcal<br>'
                                    f'{gekozen_rec.get("kh",0)}g KH</div>',
                                    unsafe_allow_html=True)

                    if rec_keuze != "— kies recept —":
                        gekozen_rec = recepten_type[rec_namen.index(rec_keuze)] if rec_keuze in rec_namen else None
                        if gekozen_rec:
                            # Toon ingrediënten van recept
                            if gekozen_rec.get("ingredienten"):
                                ing_txt = " · ".join([f"{n} {g}g" for n,g in gekozen_rec["ingredienten"]])
                                st.markdown(
                                    f'<div style="font-size:0.72rem;color:#64748b;margin:4px 0;">'
                                    f'🥗 {ing_txt}</div>', unsafe_allow_html=True)
                            if st.button(f"➕ {gekozen_rec['naam']} toevoegen",
                                         key=f"radd_{dag_str}_{mi}", use_container_width=True):
                                _sla_recept_items(user_id,dag_str,mi,gekozen_rec,bibliotheek)
                                st.session_state.pop(f"rk_{dag_str}_{mi}",None)
                                st.rerun()

                # Maaltijd wissen
                if items:
                    if st.button(f"🗑 {m_naam} wissen", key=f"wis_{dag_str}_{mi}"):
                        _verwijder_alle_items_moment(user_id,dag_str,mi)
                        st.rerun()

                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e293b;margin:4px 0 10px;">', unsafe_allow_html=True)



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

def _stap_dashboard(user: dict):
    from datetime import date as _date, timedelta as _td

    user_id = user.get("id", "")
    profiel = st.session_state.get("fc_profiel", {})

    _sectie("VOEDINGSDAGBOEK", "#22c55e")

    # Week selectie
    wi1, wi2 = st.columns([2,3])
    with wi1:
        week_ref = st.date_input("Week van", value=_date.today(), key="db_week_start")
        maandag  = week_ref - _td(days=week_ref.weekday())
    with wi2:
        st.markdown(
            f'<div style="padding-top:26px;font-size:0.8rem;color:#64748b;">'
            f'{maandag.strftime("%d/%m")} — {(maandag+_td(days=6)).strftime("%d/%m/%Y")}</div>',
            unsafe_allow_html=True)

    # Laad alle welzijn data voor deze week in één keer
    welzijn_week = _laad_welzijn_week(user_id, maandag)
    # Laad weekschema's voor training info
    schema_week = {}
    for d in range(7):
        dag_datum = str(maandag + _td(days=d))
        schema    = _laad_dagschema(user_id, dag_datum)
        if schema:
            schema_week[dag_datum] = schema

    # Week overzicht chips
    st.markdown('<div style="display:flex;gap:6px;margin:8px 0 16px;flex-wrap:wrap;">', unsafe_allow_html=True)
    for d in range(7):
        dag_datum = str(maandag + _td(days=d))
        dag_naam  = DAGEN_NL_DB[d][:2]
        dag_num   = (maandag + _td(days=d)).strftime("%d")
        welzijn   = welzijn_week.get(dag_datum, {})
        vg        = welzijn.get("voeding_gevolgd","")
        kleur_dag = KLEUR_MAP.get(vg, "#334155")
        is_vandaag = dag_datum == str(_date.today())
        st.markdown(
            f'<div style="text-align:center;background:#1e293b;border-radius:8px;'
            f'padding:6px 10px;border:2px solid {kleur_dag};">'
            f'<div style="font-size:0.65rem;color:#64748b;">{dag_naam}</div>'
            f'<div style="font-size:0.85rem;font-weight:800;color:#f8fafc;">{dag_num}</div>'
            f'{"<div style=\"font-size:0.55rem;color:#f97316;font-weight:700;\">VANDAAG</div>" if is_vandaag else ""}'
            f'</div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Is het maandag? Dan gewicht vragen
    is_maandag = (_date.today().weekday() == 0)
    vandaag_str = str(_date.today())

    # Per dag
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

        # Status kleur
        if is_toekomst:
            border = "#1e293b"
        elif ingevuld:
            border = "#22c55e"
        else:
            border = "#f97316" if is_vandaag else "#334155"

        # Dag header
        dh1, dh2 = st.columns([4,1])
        with dh1:
            chips_html = ""
            if welzijn.get("voeding_gevolgd"):
                chips_html += _chip(welzijn["voeding_gevolgd"], KLEUR_MAP.get(welzijn["voeding_gevolgd"],"#64748b")) + " "
            if welzijn.get("training_gevoel") and heeft_training:
                chips_html += _chip(welzijn["training_gevoel"], KLEUR_MAP.get(welzijn["training_gevoel"],"#64748b")) + " "
            if welzijn.get("hrv"):
                chips_html += _chip(f"HRV {welzijn['hrv']}", KLEUR_MAP.get(welzijn["hrv"],"#64748b"))
            st.markdown(
                f'<div style="padding:6px 0;">'
                f'<span style="font-size:0.9rem;font-weight:800;color:#f8fafc;">{dag_label}</span>'
                f'{"<span style=\"background:#f97316;color:white;border-radius:4px;font-size:0.6rem;font-weight:700;padding:1px 6px;margin-left:8px;\">VANDAAG</span>" if is_vandaag else ""}'
                f'{"<span style=\"color:#475569;font-size:0.75rem;margin-left:8px;\">— nog niet beschikbaar</span>" if is_toekomst else ""}'
                f'</div>'
                f'<div style="margin-top:2px;">{chips_html}</div>',
                unsafe_allow_html=True)
        with dh2:
            if not is_toekomst:
                dag_open_key = f"db_open_{dag_str}"
                label = "▲ Dicht" if st.session_state.get(dag_open_key) else "▼ Invullen"
                if st.button(label, key=f"db_toggle_{dag_str}", use_container_width=True):
                    st.session_state[dag_open_key] = not st.session_state.get(dag_open_key, False)
                    st.rerun()

        # Dag detail
        if not is_toekomst and st.session_state.get(f"db_open_{dag_str}", False):
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;'
                f'border-left:3px solid {border};padding:14px;margin-bottom:4px;">',
                unsafe_allow_html=True)

            # ── VOEDING ───────────────────────────────────────────────────────
            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin-bottom:8px;">🥦 VOEDING</div>', unsafe_allow_html=True)
            vg_val = _radio_kleur("Voedingsschema gevolgd",
                VOEDING_OPTIES, f"db_vg_{dag_str}",
                welzijn.get("voeding_gevolgd"))

            # ── TRAINING ──────────────────────────────────────────────────────
            tr_val = None
            if heeft_training:
                st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">🏃 TRAINING</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:6px;">'
                    f'{schema_dag.get("training_timing","")}</div>',
                    unsafe_allow_html=True)
                tr_val = _radio_kleur("Hoe verliep de training",
                    TRAINING_OPTIES, f"db_tr_{dag_str}",
                    welzijn.get("training_gevoel"))

            # ── HERSTEL ───────────────────────────────────────────────────────
            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">💚 HERSTEL & WELZIJN</div>', unsafe_allow_html=True)

            rc1, rc2 = st.columns(2)
            with rc1:
                hrv_val = _radio_kleur("HRV", HRV_OPTIES, f"db_hrv_{dag_str}", welzijn.get("hrv"))
                fris_val = _radio_kleur("Frisheid", KWALITEIT_OPTIES, f"db_fris_{dag_str}", welzijn.get("frisheid"))
                spierpijn_val = _radio_kleur("Spierpijn", SPIERPIJN_OPTIES, f"db_sp_{dag_str}", welzijn.get("spierpijn"))
            with rc2:
                slaap_kwal_val = _radio_kleur("Slaapkwaliteit", KWALITEIT_OPTIES, f"db_sk_{dag_str}", welzijn.get("slaap_kwaliteit"))
                stress_val = _radio_kleur("Stress", STRESS_OPTIES, f"db_stress_{dag_str}", welzijn.get("stress"))

            # ── METINGEN ─────────────────────────────────────────────────────
            st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">📊 METINGEN</div>', unsafe_allow_html=True)

            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                slaap_val = st.number_input("Slaap (uur)",
                    0.0, 14.0, float(welzijn.get("slaap_uur") or 7.5), 0.5,
                    key=f"db_slaap_{dag_str}")
            with mc2:
                rhr_val = st.number_input("Rusthartslag (bpm)",
                    0, 120, int(welzijn.get("rusthartslag") or 0), 1,
                    key=f"db_rhr_{dag_str}")
            with mc3:
                water_val = st.number_input("Water (liter)",
                    0.0, 8.0, float(welzijn.get("waterinname_l") or 0.0), 0.25,
                    key=f"db_water_{dag_str}")

            # ── GEWICHT (enkel maandag) ───────────────────────────────────────
            gewicht_val = welzijn.get("gewicht_kg")
            if dag_datum.weekday() == 0:
                st.markdown('<div style="font-size:0.7rem;font-weight:700;color:#22c55e;letter-spacing:1px;margin:10px 0 8px;">⚖️ GEWICHT (wekelijks)</div>', unsafe_allow_html=True)
                gw1, _ = st.columns([1,2])
                with gw1:
                    gewicht_val = st.number_input("Gewicht (kg)",
                        30.0, 200.0,
                        float(welzijn.get("gewicht_kg") or float(profiel.get("gewicht_kg") or 70)),
                        0.1, key=f"db_gew_{dag_str}")

            # ── NOTITIE ───────────────────────────────────────────────────────
            notitie_val = st.text_input("Notitie (optioneel)",
                value=welzijn.get("notitie",""),
                placeholder="bijv. zware benen, slecht geslapen...",
                key=f"db_notitie_{dag_str}",
                label_visibility="collapsed")

            # ── OPSLAAN ───────────────────────────────────────────────────────
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
                    # Update lokale cache
                    welzijn_week[dag_str] = {**data, "datum": dag_str}
                    st.success("✅ Opgeslagen!")
                    st.session_state[f"db_open_{dag_str}"] = False
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e293b;margin:4px 0 10px;">', unsafe_allow_html=True)



def _stap_dashboard(user: dict):
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
    def _laad_gewicht_all(uid):
        """Laad alle gewichtsmetingen ongeacht periode."""
        try:
            r = _get_supabase().table("fuelc_dagboek_welzijn")                .select("datum,gewicht_kg")                .eq("user_id",uid)                .order("datum").execute()
            return [(row["datum"][:10], float(row["gewicht_kg"]))
                    for row in (r.data or []) if row.get("gewicht_kg")]
        except: return []

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

    dagen_lijst = sorted(dag_dict.values(), key=lambda x: x["datum"])
    dagen_met_data = [d for d in dagen_lijst if d["kcal"] > 0]

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
        score_voeding = round(sum(1 for d in dagen_met_data if d.get("voeding_gev")=="Volledig") / len(dagen_met_data) * 100)
        slaap_ok      = [d for d in dagen_met_data if d.get("slaap",0) >= 7]
        score_slaap   = round(len(slaap_ok) / max(len(dagen_met_data),1) * 100)
        hrv_ok        = [d for d in dagen_met_data if d.get("hrv") in ("Hoog","Gemiddeld")]
        score_hrv     = round(len(hrv_ok) / max(len(dagen_met_data),1) * 100)
        stress_ok     = [d for d in dagen_met_data if d.get("stress") in ("Laag","Matig")]
        score_stress  = round(len(stress_ok) / max(len(dagen_met_data),1) * 100)
        kcal_ok       = [d for d in dagen_met_data if abs(d["kcal"] - energie_doel) / energie_doel < 0.15]
        score_kcal    = round(len(kcal_ok) / max(len(dagen_met_data),1) * 100)
        totaal_score  = round((score_voeding*0.3 + score_slaap*0.2 + score_hrv*0.2 + score_stress*0.15 + score_kcal*0.15))
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

    gew_col1, gew_col2 = st.columns([3,1])
    with gew_col2:
        nieuw_gewicht = st.number_input("Gewicht vandaag (kg)", 30.0, 200.0,
            gewicht_prof, 0.1, key="dash_gewicht")
        if st.button("💾 Opslaan", key="dash_gew_ops"):
            try:
                _get_supabase().table("fuelc_dagboek_welzijn").upsert({
                    "user_id":user_id,"datum":str(vandaag),
                    "gewicht_kg":nieuw_gewicht
                }, on_conflict="user_id,datum").execute()
                st.success("✅")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Laad alle gewichtsdata ongeacht periode
    gewicht_punten = _laad_gewicht_all(user_id)
    if not gewicht_punten:
        # Fallback: uit dagen_lijst
        gewicht_punten = [(d["datum"], d["gewicht"]) for d in dagen_lijst if d.get("gewicht",0) > 0]
    with gew_col1:
        if len(gewicht_punten) >= 1:
            data_gew = {"Datum":[p[0] for p in gewicht_punten],
                        "Gewicht":[p[1] for p in gewicht_punten]}
            gem_gew = sum(p[1] for p in gewicht_punten) / len(gewicht_punten)
            bmi     = round(gem_gew / ((lengte_prof/100)**2), 1) if lengte_prof > 0 else 0
            bmi_cat = "Ondergewicht" if bmi < 18.5 else ("Normaal" if bmi < 25 else ("Overgewicht" if bmi < 30 else "Obesitas"))
            bmi_kleur = "#22c55e" if bmi < 25 else ("#fbbf24" if bmi < 30 else "#ef4444")
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;padding:12px;margin-bottom:8px;">'
                f'<div style="display:flex;gap:20px;">'
                f'<div><div style="font-size:0.65rem;color:#64748b;">GEMIDDELD</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:#f8fafc;">{round(gem_gew,1)} kg</div></div>'
                f'<div><div style="font-size:0.65rem;color:#64748b;">BMI</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{bmi_kleur};">{bmi}</div></div>'
                f'<div><div style="font-size:0.65rem;color:#64748b;">CATEGORIE</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{bmi_kleur};">{bmi_cat}</div></div>'
                f'</div></div>',
                unsafe_allow_html=True)
            # Gewicht grafiek als ASCII-stijl balken
            max_gew = max(p[1] for p in gewicht_punten)
            min_gew = min(p[1] for p in gewicht_punten)
            trend   = gewicht_punten[-1][1] - gewicht_punten[0][1] if len(gewicht_punten) > 1 else 0
            trend_tekst = "→ Eerste meting" if len(gewicht_punten) == 1 else (f"▲ +{round(trend,1)}kg" if trend > 0.1 else (f"▼ {round(trend,1)}kg" if trend < -0.1 else "→ Stabiel"))
            trend_kleur = "#64748b" if len(gewicht_punten) == 1 else ("#ef4444" if trend > 0.5 else ("#22c55e" if trend < -0.5 else "#fbbf24"))
            st.markdown(
                f'<div style="font-size:0.75rem;color:{trend_kleur};margin-bottom:8px;">'
                f'Trend: {trend_tekst} over {len(gewicht_punten)} metingen</div>',
                unsafe_allow_html=True)
            grafiek_html = '<div style="display:flex;align-items:flex-end;gap:4px;height:80px;margin-bottom:4px;">'
            for datum, gew in gewicht_punten[-14:]:
                hoogte = round(((gew - min_gew + 0.5) / (max_gew - min_gew + 1)) * 70) + 10
                grafiek_html += (f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;">'
                                 f'<div style="width:100%;background:#22c55e;border-radius:3px 3px 0 0;height:{hoogte}px;"></div>'
                                 f'<div style="font-size:0.55rem;color:#475569;margin-top:2px;">{datum[8:]}</div></div>')
            grafiek_html += '</div>'
            st.markdown(grafiek_html, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#64748b;font-size:0.8rem;">Voer gewicht in via het Dagboek (maandag) of hier rechts.</div>', unsafe_allow_html=True)

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

    stap   = st.session_state.get("fc_stap", 1)
    namen  = ["Profiel","Trainingen","Bibliotheek","Weekschema","Analyses"]
    emojis = ["👤","🏃","🥦","📅","📊"]

    nav_cols = st.columns(5)
    for i, (col, naam_stap, emoji) in enumerate(zip(nav_cols, namen, emojis)):
        with col:
            actief = (i+1) == stap
            if st.button(f"{emoji}  {naam_stap}", key=f"nav_stap_{i+1}",
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
        else: _stap_trainingen(user)
    elif stap == 3: _stap_bibliotheek(user)
    elif stap == 4: _stap_dagschema(user)
    elif stap == 5: _stap_dashboard(user)

    if profiel_ingevuld and stap > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        c_terug, c_next = st.columns([1,2])
        with c_terug:
            if st.button("← Vorige", key="fc_vorige", use_container_width=True):
                st.session_state.fc_stap = max(1, stap-1)
                st.rerun()
        with c_next:
            if stap < len(namen):
                if st.button("Volgende →", key="fc_volgende", use_container_width=True):
                    st.session_state.fc_stap = stap+1
                    st.rerun()
