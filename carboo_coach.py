import streamlit as st
import math
from datetime import datetime, timedelta

# ─── MASCOT AVATAR ────────────────────────────────────────────────────────────
from carboo_assets import MASCOT_B64


# ─── COACH STAPPEN ────────────────────────────────────────────────────────────
STAPPEN = [
    "welkom",
    "atleet_profiel",
    "wedstrijd_info",
    "carboloading",
    "racedag_voeding",
    "raceplan",
    "samenvatting",
]

SPORT_ICONS = {
    "Fietsen":      "🚴",
    "Lopen":        "🏃",
    "Duatlon":      "🏃🚴",
    "Crossduatlon": "🚵🏃",
    "Triatlon":     "🏊🚴🏃",
    "Crosstriatlon":"🚵🏊",
}

KH_TARGETS = {
    "Fietsen":      {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":        {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":      {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":     {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}


def _get_kh_range(sport, minuten):
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= minuten < hi:
            return mn, mx
    return 60, 90


def _progress_bar(stap_idx: int):
    total = len(STAPPEN) - 1
    pct = int((stap_idx / total) * 100)
    labels = ["👋 Welkom", "🏃 Profiel", "🏁 Wedstrijd", "🍝 Carboloading", "🥗 Racedag", "📋 Raceplan", "✅ Samenvatting"]
    
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#94a3b8; font-size:0.72rem; font-weight:700; letter-spacing:1px;">STAP {stap_idx + 1} VAN {total + 1}</span>
            <span style="color:#f97316; font-size:0.72rem; font-weight:700;">{pct}% VOLTOOID</span>
        </div>
        <div style="background:#1e293b; border-radius:8px; height:8px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:linear-gradient(90deg,#f97316,#fb923c); border-radius:8px; transition:width 0.3s;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:8px; flex-wrap:wrap; gap:4px;">
            {"".join(f'<span style="font-size:0.62rem; color:{"#f97316" if i == stap_idx else "#334155" if i > stap_idx else "#22c55e"}; font-weight:700;">{lbl}</span>' for i, lbl in enumerate(labels))}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _coach_bubble(tekst: str, icon: str = "🤖"):
    html = (
        '<div style="display:flex;gap:14px;margin-bottom:20px;align-items:flex-end;">' +
        '<div style="flex-shrink:0;width:70px;height:70px;display:flex;align-items:flex-end;justify-content:center;">' +
        '<img src="' + MASCOT_B64 + '" style="height:70px;width:auto;object-fit:contain;filter:drop-shadow(0 2px 8px rgba(249,115,22,0.5));" alt="Carboo">' +
        '</div>' +
        '<div style="background:#1e293b;border:1px solid #334155;border-radius:0 14px 14px 14px;padding:14px 18px;color:#f8fafc;font-size:0.9rem;line-height:1.6;max-width:680px;">' +
        tekst +
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _info_card(titel: str, waarde: str, kleur: str = "#f97316", icon: str = ""):
    st.markdown(f"""
    <div style="background:#1e293b; border-left:4px solid {kleur}; border-radius:10px; 
         padding:14px 16px; margin-bottom:10px;">
        <div style="font-size:0.68rem; color:#64748b; font-weight:700; letter-spacing:1px; margin-bottom:2px;">{icon} {titel.upper()}</div>
        <div style="font-size:1.05rem; font-weight:800; color:#f8fafc;">{waarde}</div>
    </div>
    """, unsafe_allow_html=True)


def _stap_welkom(naam: str):
    _coach_bubble(f"""
    Hoi <b>{naam}</b>! 👋 Ik ben <b>Carboo</b>, jouw persoonlijke race nutrition coach.<br><br>
    Ik ga je stap voor stap begeleiden om jouw voeding optimaal af te stemmen op je komende wedstrijd. 
    We bouwen samen een <b>volledig voedingsplan</b> op dat bestaat uit:<br><br>
    🍝 <b>Carbohydrate loading</b> — de 2 dagen vóór de race<br>
    🏁 <b>Racedag voeding</b> — ontbijt en pre-race strategie<br>
    ⏱️ <b>Slim raceplan</b> — uur per uur wat je eet en drinkt<br><br>
    Dit duurt slechts <b>5-7 minuten</b>. Ben je er klaar voor?
    """, "🤖")

    if st.button("🚀  JA, LET'S GO!", key="welkom_ja", use_container_width=True):
        st.session_state.coach_stap = 1
        st.rerun()


def _stap_profiel(naam: str):
    _coach_bubble(f"""
    Laten we starten met jouw <b>atleetprofiel</b>. Dit helpt me om je koolhydraatbehoeften 
    nauwkeurig te berekenen. Vul de gegevens zo nauwkeurig mogelijk in.
    """)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            atleet_naam = st.text_input("👤 Naam atleet",
                value=st.session_state.get("coach_data", {}).get("atleet_naam", ""),
                key="p_atleet_naam", placeholder="Voornaam en naam atleet")
        with col2:
            wedstrijd_naam = st.text_input("🏆 Naam wedstrijd",
                value=st.session_state.get("coach_data", {}).get("wedstrijd_naam", ""),
                key="p_wedstrijd_naam", placeholder="bv. Ironman Frankfurt")

        col3, col4 = st.columns(2)
        with col3:
            gewicht = st.number_input("⚖️ Lichaamsgewicht (kg)", 30.0, 150.0,
                st.session_state.get("coach_data", {}).get("gewicht", 70.0), 0.5, key="p_gewicht")
        with col4:
            sport_list = list(SPORT_ICONS.keys())
            sport_default = st.session_state.get("coach_data", {}).get("sport", "Fietsen")
            sport_idx = sport_list.index(sport_default) if sport_default in sport_list else 0
            sport = st.selectbox("🏅 Discipline",
                [f"{SPORT_ICONS[s]} {s}" for s in sport_list],
                index=sport_idx, key="p_sport")
            sport_clean = sport.split(" ", 1)[1] if " " in sport else sport

        niveau_list = ["Recreatief", "Competitief", "Elite / Semi-pro"]
        niveau_default = st.session_state.get("coach_data", {}).get("niveau", "Recreatief")
        niveau_idx = niveau_list.index(niveau_default) if niveau_default in niveau_list else 0
        nc1, nc2 = st.columns([11, 1])
        with nc1:
            niveau = st.selectbox("📊 Sportniveau", niveau_list, index=niveau_idx, key="p_niveau")
        with nc2:
            st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
            with st.popover("ℹ️"):
                st.markdown("""
**Sportniveau — legende**

🟢 **Recreatief**
Meedoen is belangrijker dan winnen. Je sport voor plezier en gezondheid.

🟡 **Competitief**
Je hebt een (tijds)doel. Je traint gericht.

🔴 **Elite / Semi-pro**
Je verdient (geld)prijzen met je sport. Prestatie staat centraal.
""")

        erv_list = ["Eerste wedstrijd", "1-3 wedstrijden", "4-10 wedstrijden", "10+ wedstrijden"]
        erv_default = st.session_state.get("coach_data", {}).get("ervaring", "Eerste wedstrijd")
        erv_idx = erv_list.index(erv_default) if erv_default in erv_list else 0
        ervaring = st.selectbox("🎯 Ervaring met wedstrijdvoeding", erv_list, index=erv_idx, key="p_erv")

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="prof_prev"):
            st.session_state.coach_stap = 0
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="prof_next", use_container_width=True):
            if "coach_data" not in st.session_state:
                st.session_state.coach_data = {}
            st.session_state.coach_data.update({
                "atleet_naam":    atleet_naam,
                "wedstrijd_naam": wedstrijd_naam,
                "gewicht":        gewicht,
                "sport":          sport_clean,
                "niveau":         niveau,
                "ervaring":       ervaring,
            })
            st.session_state.coach_stap = 2
            st.rerun()


def _stap_wedstrijd():
    data = st.session_state.get("coach_data", {})
    _coach_bubble(f"""
    Nu de <b>wedstrijddetails</b>. Op basis van de duur en het type wedstrijd bereken ik hoeveel 
    koolhydraten je nodig hebt en stel ik een tijdlijn op.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        wedstrijd_datum = st.date_input("📅 Wedstrijddatum",
            value=datetime.now().date() + timedelta(days=14), key="w_datum")
    with col2:
        start_time = st.time_input("⏰ Starttijd",
            value=datetime.strptime(data.get("start_time", "09:00"), "%H:%M").time(),
            step=60, key="w_start")
    with col3:
        eind_time = st.time_input("🏁 Geschatte eindtijd",
            value=datetime.strptime(data.get("eind_time", "12:00"), "%H:%M").time(),
            step=60, key="w_eind")

    col4, col5 = st.columns(2)
    with col4:
        temp = st.number_input("🌡️ Verwachte temperatuur (°C)", -10, 50,
            data.get("temp", 18), key="w_temp")
    with col5:
        vochtigheid = st.number_input("💧 Vochtigheid (%)", 0, 100,
            data.get("vochtigheid", 50), key="w_vocht")

    hoogte = st.number_input("⛰️ Hoogte boven zeeniveau (m)", 0, 5000,
        data.get("hoogte", 0), key="w_hoogte")

    start_dt = datetime.combine(datetime.today(), start_time)
    eind_dt = datetime.combine(datetime.today(), eind_time)
    if eind_dt <= start_dt:
        eind_dt += timedelta(days=1)
    totale_min = int((eind_dt - start_dt).total_seconds() / 60)
    sport = data.get("sport", "Fietsen")
    min_kh, max_kh = _get_kh_range(sport, totale_min)

    st.markdown(f"""
    <div style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; padding:14px; 
         border-radius:10px; margin:16px 0; text-align:center; color:#93c5fd; font-weight:700;">
        ⏱️ Duur: {totale_min // 60}u{totale_min % 60:02d}m &nbsp;|&nbsp;
        📊 {math.ceil(totale_min/60)} uur te plannen
    </div>
    """, unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="wed_prev"):
            st.session_state.coach_stap = 1
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="wed_next", use_container_width=True):
            st.session_state.coach_data.update({
                "wedstrijd_datum": str(wedstrijd_datum),
                "start_time": start_time.strftime("%H:%M"),
                "eind_time": eind_time.strftime("%H:%M"),
                "totale_min": totale_min,
                "temp": temp,
                "vochtigheid": vochtigheid,
                "hoogte": hoogte,
                "min_kh": min_kh,
                "max_kh": max_kh,
            })
            st.session_state.coach_stap = 3
            st.rerun()


def _stap_carboloading():
    data       = st.session_state.get("coach_data", {})
    gewicht    = data.get("gewicht", 70)
    totale_min = data.get("totale_min", 180)

    # Herstel groene status bij terugkeren
    for k, v in data.get("cl_status", {}).items():
        if k not in st.session_state:
            st.session_state[k] = v

    if totale_min > 300:   factor = 12
    elif totale_min > 180: factor = 10
    elif totale_min > 90:  factor = 8
    else:                  factor = 6

    dag_target = round(gewicht * factor)

    _coach_bubble(f"""
    Vul per maaltijd in wat je plant te eten. Ik bereken automatisch of je je doel haalt.<br><br>
    Wanneer het balkje groen kleurt, bevestig je onderaan met <b>Dagdeel opslaan</b>. Er zal een groen bolletje verschijnen.
    """)

    st.markdown("""
    <style>
    div[data-testid="stNumberInput"] input { background-color:#1e293b !important; color:#f8fafc !important; border:1px solid #334155 !important; }
    div[data-testid="stNumberInput"] button { background-color:#334155 !important; color:#f8fafc !important; border:none !important; }
    div[data-testid="stTextInput"] input { background-color:#1e293b !important; color:#f8fafc !important; border:1px solid #334155 !important; }
    /* Expander header: lichtgrijze achtergrond + donkere tekst — altijd leesbaar */
    div[data-testid="stExpander"] > details > summary {
        background-color: #1e293b !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary p {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover p {
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary svg {
        fill: #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    MOMENT_FOODS = {
        "Ontbijt": [
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",          "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",          "kh_portie": 14},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Ontbijtgranen",       "portie": "1 kom (30g)",            "kh_portie": 25},
            {"naam": "Muesli",              "portie": "1 kom (40g)",            "kh_portie": 30},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Melk (dierlijk)",     "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Plantaardige melk",   "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Kiwi",                "portie": "1 stuk middel (75g)",    "kh_portie": 11},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Koffie met suiker",   "portie": "1 tas + 1 klontje",      "kh_portie": 5},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
        ],
        "Tussendoor VM": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
        ],
        "Lunch": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar","kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",   "kh_portie": 30},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",         "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",         "kh_portie": 8},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",         "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",         "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",         "kh_portie": 14},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",  "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",  "kh_portie": 15},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",        "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",       "kh_portie": 35},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",  "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
        ],
        "Tussendoor NM": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Peer",                "portie": "1 stuk middel (135g)",   "kh_portie": 19},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
        ],
        "Avondmaal": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar","kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",  "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",   "kh_portie": 30},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",         "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",         "kh_portie": 8},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",         "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",         "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",         "kh_portie": 14},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",  "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",        "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",       "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",    "kh_portie": 27},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",  "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",  "kh_portie": 4},
        ],
        "Avond snack": [
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Dadels gedroogd",     "portie": "1 stuk (9g netto)",      "kh_portie": 6},
            {"naam": "Rozijnen",            "portie": "1 handje (20g)",         "kh_portie": 15},
            {"naam": "Muesli/granenreep",   "portie": "1 reep (40g)",           "kh_portie": 26},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Plattekaas",          "portie": "4 eetlpl (100g)",        "kh_portie": 4},
            {"naam": "Speculoos",           "portie": "1 stuk (7g)",            "kh_portie": 5},
            {"naam": "Snoep/winegums",      "portie": "1 zakje (30g)",          "kh_portie": 26},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
            {"naam": "Pannenkoek",          "portie": "1 stuk (60g)",           "kh_portie": 27},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
        ],
    }

    MAALTIJD_CONFIG = {
        "Ontbijt":       {"pct": 0.25,  "icon": ""},
        "Tussendoor VM": {"pct": 0.083, "icon": ""},
        "Lunch":         {"pct": 0.25,  "icon": ""},
        "Tussendoor NM": {"pct": 0.083, "icon": ""},
        "Avondmaal":     {"pct": 0.25,  "icon": ""},
        "Avond snack":   {"pct": 0.083, "icon": ""},
    }

    tab1, tab2 = st.tabs(["  DAG 1 (2 dagen voor race)", "  DAG 2 (1 dag voor race)"])
    dag_totalen = {}

    for dag_idx, tab in enumerate([tab1, tab2], start=1):
        with tab:
            dag_kh = 0
            left_col, right_col = st.columns([1, 1])
            maaltijd_list = list(MAALTIJD_CONFIG.items())

            for col_obj, moment_slice in [
                (left_col,  maaltijd_list[:3]),
                (right_col, maaltijd_list[3:]),
            ]:
                with col_obj:
                    for m_name, m_cfg in moment_slice:
                        m_target  = round(dag_target * m_cfg["pct"])
                        status_key = f"cl_status_d{dag_idx}_{m_name}"
                        is_groen  = st.session_state.get(status_key, False)

                        # Bereken preview KH (huidige waarden uit session_state)
                        # Standaard producten
                        preview_kh = sum(
                            st.session_state.get(f"cl_d{dag_idx}_{m_name}_{p['naam']}", 0.0)
                            * p["kh_portie"]
                            for p in MOMENT_FOODS.get(m_name, [])
                        )
                        # Eigen producten meetellen
                        _eigen_base_prev = f"eigen_d{dag_idx}_{m_name}"
                        _n_eigen_prev = st.session_state.get(f"{_eigen_base_prev}_n", 0)
                        for _ei in range(_n_eigen_prev):
                            _ekh   = st.session_state.get(f"{_eigen_base_prev}_{_ei}_kh",   0.0)
                            _eport = st.session_state.get(f"{_eigen_base_prev}_{_ei}_port", 0.0)
                            preview_kh += _ekh * _eport
                        over_limiet = preview_kh > m_target

                        # Groene dot verdwijnt automatisch bij overschrijding
                        if over_limiet and is_groen:
                            st.session_state[status_key] = False
                            is_groen = False

                        # Label met groene dot
                        dot       = "🟢 " if is_groen else ""
                        exp_label = f"{dot}**{m_name}**"

                        with st.expander(exp_label, expanded=False):

                            # Progress balk bovenaan
                            pct_bar = min(100, round((preview_kh / m_target) * 100)) if m_target > 0 else 0
                            if over_limiet:
                                bar_kleur = "#ef4444"
                            elif pct_bar >= 80:
                                bar_kleur = "#22c55e"
                            elif pct_bar >= 50:
                                bar_kleur = "#fbbf24"
                            else:
                                bar_kleur = "#f97316"

                            # Avatar bij overschrijding VOOR de balk
                            if over_limiet:
                                st.markdown(
                                    '<div style="display:flex;gap:10px;align-items:center;'
                                    'margin-bottom:8px;background:rgba(239,68,68,0.1);'
                                    'border:1px solid #ef4444;border-radius:10px;padding:8px 12px;">' +
                                    '<img src="' + MASCOT_B64 + '" style="height:36px;width:auto;flex-shrink:0;">' +
                                    '<span style="color:#fca5a5;font-size:0.80rem;">'
                                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van dit dagdeel!</span>'
                                    '</div>',
                                    unsafe_allow_html=True
                                )

                            st.markdown(
                                f'<div style="background:#1e293b;border-radius:6px;height:8px;margin-bottom:10px;">'
                                f'<div style="width:{pct_bar}%;height:100%;background:{bar_kleur};border-radius:6px;"></div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                            # Producten header
                            st.markdown(
                                '<div style="font-size:0.7rem;color:#64748b;font-weight:700;'
                                'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">'
                                'Voedingsmiddel · portiegrootte · KH/portie · aantal porties</div>',
                                unsafe_allow_html=True
                            )

                            moment_kh = 0.0

                            # Standaard producten
                            for product in MOMENT_FOODS.get(m_name, []):
                                ss_key = f"cl_d{dag_idx}_{m_name}_{product['naam']}"
                                if ss_key not in st.session_state:
                                    saved = data.get("cl_waarden", {})
                                    st.session_state[ss_key] = float(saved.get(ss_key, 0.0))
                                if not isinstance(st.session_state.get(ss_key), (int, float)):
                                    st.session_state[ss_key] = 0.0

                                pc1, pc2 = st.columns([5, 1])
                                with pc1:
                                    st.markdown(
                                        f'<div style="padding:6px 0 2px;color:#f1f5f9;font-size:0.88rem;font-weight:600;line-height:1.4;">'
                                        f'{product["naam"]} '
                                        f'<span style="color:#64748b;font-size:0.78rem;font-weight:400;">'
                                        f'— {product["portie"]} · {product["kh_portie"]}g KH/portie</span></div>',
                                        unsafe_allow_html=True
                                    )
                                with pc2:
                                    val = st.number_input("p", min_value=0.0, max_value=20.0,
                                                          step=0.5, key=ss_key,
                                                          label_visibility="collapsed")
                                kh = val * product["kh_portie"]
                                moment_kh += kh
                                if val > 0:
                                    val_str = str(int(val)) if val == int(val) else str(val)
                                    st.markdown(
                                        f'<div style="font-size:0.72rem;color:#f97316;'
                                        f'margin:-4px 0 6px 0;text-align:right;">→ {val_str}× {product["kh_portie"]}g = <b>{round(kh)}g KH</b></div>',
                                        unsafe_allow_html=True
                                    )

                            # Eigen producten
                            eigen_key_base = f"eigen_d{dag_idx}_{m_name}"
                            n_eigen = st.session_state.get(f"{eigen_key_base}_n", 0)

                            st.markdown('<hr style="border-color:#1e293b;margin:8px 0 10px 0;">', unsafe_allow_html=True)
                            st.caption("Noteer bij eigen producten het aantal koolhydraten per portie (zie verpakking)")

                            for i in range(n_eigen):
                                e_naam = st.session_state.get(f"{eigen_key_base}_{i}_naam", "")
                                e_kh   = st.session_state.get(f"{eigen_key_base}_{i}_kh",   0.0)
                                e_port = st.session_state.get(f"{eigen_key_base}_{i}_port", 0.0)

                                if i == 0:
                                    lc1, lc2, lc3, lc4 = st.columns([4, 2, 2, 0.6])
                                    with lc1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PRODUCTNAAM</div>', unsafe_allow_html=True)
                                    with lc2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH/PORTIE (g)</div>', unsafe_allow_html=True)
                                    with lc3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PORTIES</div>', unsafe_allow_html=True)

                                ec1, ec2, ec3, ec4 = st.columns([4, 2, 2, 0.6])
                                with ec1:
                                    new_naam = st.text_input("Naam", value=e_naam,
                                        key=f"{eigen_key_base}_{i}_naam_inp",
                                        placeholder="bv. Cruesli extra", label_visibility="collapsed")
                                    st.session_state[f"{eigen_key_base}_{i}_naam"] = new_naam
                                with ec2:
                                    new_kh = st.number_input("KH/portie", value=float(e_kh),
                                        min_value=0.0, step=1.0,
                                        key=f"{eigen_key_base}_{i}_kh_inp",
                                        label_visibility="collapsed", help="KH per portie — zie verpakking")
                                    st.session_state[f"{eigen_key_base}_{i}_kh"] = new_kh
                                with ec3:
                                    new_port = st.number_input("Porties", value=float(e_port),
                                        min_value=0.0, step=1.0,
                                        key=f"{eigen_key_base}_{i}_port_inp",
                                        label_visibility="collapsed")
                                    st.session_state[f"{eigen_key_base}_{i}_port"] = new_port
                                with ec4:
                                    if st.button("🗑", key=f"{eigen_key_base}_{i}_del",
                                                 help="Verwijder", use_container_width=True):
                                        for j in range(i, n_eigen - 1):
                                            for field in ["naam", "kh", "port"]:
                                                st.session_state[f"{eigen_key_base}_{j}_{field}"] = \
                                                    st.session_state.get(f"{eigen_key_base}_{j+1}_{field}", 0 if field != "naam" else "")
                                        for field in ["naam", "kh", "port"]:
                                            st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}", None)
                                            st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}_inp", None)
                                        st.session_state[f"{eigen_key_base}_n"] = n_eigen - 1
                                        st.rerun()

                                eigen_kh_i = new_kh * new_port
                                moment_kh += eigen_kh_i
                                if new_port > 0 and new_kh > 0:
                                    st.markdown(
                                        f'<div style="font-size:0.72rem;color:#3b82f6;'
                                        f'margin:-4px 0 4px 0;text-align:right;">'
                                        f'→ {new_port:.0f}× {new_kh:.0f}g = <b>{round(eigen_kh_i)}g KH</b></div>',
                                        unsafe_allow_html=True
                                    )

                            if st.button("➕  Voeg eigen product toe", key=f"{eigen_key_base}_add",
                                         use_container_width=True):
                                st.session_state[f"{eigen_key_base}_n"] = n_eigen + 1
                                st.rerun()

                            # Toggle knop: opslaan ↔ aanpassen
                            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                            pct_nu      = min(100, round((moment_kh / m_target) * 100)) if m_target > 0 else 0
                            reeds_groen = st.session_state.get(status_key, False)
                            if reeds_groen:
                                btn_lbl  = "🔓  Wijzigen"
                                btn_type = "secondary"
                            else:
                                btn_lbl  = "Dagdeel opslaan"
                                btn_type = "primary"
                            if st.button(btn_lbl, key=f"save_{dag_idx}_{m_name}",
                                         use_container_width=True, type=btn_type):
                                if reeds_groen:
                                    st.session_state[status_key] = False
                                else:
                                    st.session_state[status_key] = (pct_nu >= 80 and moment_kh <= m_target)
                                st.rerun()

                        dag_kh += moment_kh

            # Dag totaal balk
            dag_pct   = round((dag_kh / dag_target) * 100) if dag_target > 0 else 0
            dag_over  = dag_kh > dag_target
            if dag_over:        bar_color = "#ef4444"
            elif dag_pct >= 80: bar_color = "#22c55e"
            elif dag_pct >= 50: bar_color = "#fbbf24"
            else:               bar_color = "#f97316"

            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;'
                f'padding:16px;text-align:center;margin-top:12px;">'
                f'<div style="font-weight:900;font-size:1rem;color:#f8fafc;margin-bottom:10px;">TOTAAL DAG {dag_idx}</div>'
                f'<div style="background:#1e293b;border-radius:8px;height:14px;overflow:hidden;">'
                f'<div style="width:{min(dag_pct,100)}%;height:100%;background:{bar_color};border-radius:8px;"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

            if dag_over:
                st.markdown(
                    '<div style="display:flex;gap:10px;align-items:center;margin-top:8px;'
                    'background:rgba(239,68,68,0.1);border:1px solid #ef4444;'
                    'border-radius:10px;padding:12px 16px;">' +
                    '<img src="' + MASCOT_B64 + '" style="height:48px;width:auto;flex-shrink:0;">' +
                    '<span style="color:#fca5a5;font-size:0.88rem;">'
                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van deze dag!</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

            dag_totalen[f"dag{dag_idx}"] = {"totaal": round(dag_kh), "target": dag_target, "pct": dag_pct}

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)

    def _save_cl():
        cl_waarden = {}
        for d in [1, 2]:
            for m_name in MAALTIJD_CONFIG:
                for product in MOMENT_FOODS.get(m_name, []):
                    k = f"cl_d{d}_{m_name}_{product['naam']}"
                    cl_waarden[k] = st.session_state.get(k, 0)
        if "coach_data" not in st.session_state:
            st.session_state.coach_data = {}
        cl_status = {k: v for k, v in st.session_state.items() if k.startswith("cl_status_")}
        st.session_state.coach_data.update({
            "cl_waarden":  cl_waarden,
            "carboloading": dag_totalen,
            "dag_target":  dag_target,
            "factor":      factor,
            "cl_status":   cl_status,
        })

    with col_prev:
        if st.button("← Vorige", key="cl_prev"):
            _save_cl()
            st.session_state.coach_stap = 2
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="cl_next", use_container_width=True):
            _save_cl()
            st.session_state.coach_stap = 4
            st.rerun()



def _stap_racedag():
    data           = st.session_state.get("coach_data", {})
    start_time_str = data.get("start_time", "09:00")
    gewicht        = data.get("gewicht", 70)
    # KH richtlijn afhankelijk van timing (wetenschappelijk: g/kg/uur voor de start)
    # Wordt pas correct berekend na timing keuze — hier als fallback
    kh_min = round(gewicht * 1)
    kh_max = round(gewicht * 4)

    # Herstel status en waarden bij terugkeren
    if "rd_status_bevestigd" not in st.session_state:
        st.session_state["rd_status_bevestigd"] = data.get("rd_status", False)
    # Herstel rd_ waarden
    saved_rd_waarden = data.get("rd_waarden", {})
    for k, v in saved_rd_waarden.items():
        if k not in st.session_state:
            st.session_state[k] = v

    start_dt  = datetime.strptime(start_time_str, "%H:%M")
    start_uur = start_dt.hour

    # Automatisch maaltijdmoment bepalen op basis van starttijdstip
    if start_uur < 13:
        maaltijd_naam = "Ontbijt"
        maaltijd_icon = "🍳"
    elif start_uur < 17:
        maaltijd_naam = "Lunch"
        maaltijd_icon = "🥗"
    else:
        maaltijd_naam = "Avondmaal"
        maaltijd_icon = "🍽️"

    _coach_bubble(f"""
    Perfect! Nu plannen we jouw <b>laatste maaltijd voor de wedstrijd</b>!<br><br>
    Het doel is om met volle glycogeenvoorraden aan de start te staan, maar zonder een volle of zwaar gevoel in de maag.<br><br>
    ✅ Kies <b>licht verteerbare</b> producten: laag in vezels en vetten.<br>
    🎯 Kies producten die je maag goed verdraagt en die je al kent uit training.<br><br>
    Wanneer het balkje groen kleurt, bevestig je met <b>Dagdeel opslaan</b>.
    """)

    # Expander CSS voor leesbaarheid
    st.markdown("""
    <style>
    div[data-testid="stExpander"] > details > summary {
        background-color: #1e293b !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary p {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] > details > summary:hover p {
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] > details > summary svg {
        fill: #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Timing dropdown
    onbijt_tips = {
        "3-4 uur voor start (aanbevolen)": -210,
        "2-3 uur voor start": -150,
        "1-2 uur voor start (licht)": -90,
    }
    ontbijt_keuze = st.selectbox("⏰ Wanneer eet je jouw laatste maaltijd?",
                                  list(onbijt_tips.keys()), key="rd_ontbijt_timing")
    offset       = onbijt_tips[ontbijt_keuze]
    ontbijt_tijd = (start_dt + timedelta(minutes=offset)).strftime("%H:%M")

    # KH richtlijn: 1-4g per kg lichaamsgewicht voor alle tijden
    kh_min = round(gewicht * 1)
    kh_max = round(gewicht * 4)









    # Productenlijsten per maaltijdmoment
    RACEDAG_FOODS = {
        "Ontbijt": [
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Bruin brood",         "portie": "1 snede (35g)",          "kh_portie": 16},
            {"naam": "Volkorenbrood",       "portie": "1 snede (35g)",          "kh_portie": 14},
            {"naam": "Havermout",           "portie": "1 kom (45g droog)",      "kh_portie": 27},
            {"naam": "Ontbijtgranen",       "portie": "1 kom (30g)",            "kh_portie": 25},
            {"naam": "Muesli",              "portie": "1 kom (40g)",            "kh_portie": 30},
            {"naam": "Granola (krokant)",   "portie": "1 kom (40g)",            "kh_portie": 26},
            {"naam": "Melk (dierlijk)",     "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Plantaardige melk",   "portie": "1 glas (200ml)",         "kh_portie": 9},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Appel",               "portie": "1 stuk middel (125g)",   "kh_portie": 15},
            {"naam": "Yoghurt natuur",      "portie": "1 potje (125g)",         "kh_portie": 6},
            {"naam": "Confituur",           "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Honing",              "portie": "1 koffielepel (4.5g)",   "kh_portie": 4},
            {"naam": "Chocopasta",          "portie": "1 koffielepel (4.5g)",   "kh_portie": 3},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
        ],
        "Lunch": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar", "kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",    "kh_portie": 30},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",          "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",          "kh_portie": 8},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
        ],
        "Avondmaal": [
            {"naam": "Pasta (hoofdmaaltijd)","portie": "120g rauw / 300g gaar", "kh_portie": 75},
            {"naam": "Pasta (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 37},
            {"naam": "Rijst (hoofdmaaltijd)","portie": "115g rauw / 290g gaar", "kh_portie": 81},
            {"naam": "Rijst (bijgerecht)",  "portie": "60g rauw / 150g gaar",   "kh_portie": 42},
            {"naam": "Aardappelen gekookt", "portie": "1 bord (175g netto)",    "kh_portie": 30},
            {"naam": "Wit brood",           "portie": "1 snede (35g)",          "kh_portie": 17},
            {"naam": "Groentenmix rauw",    "portie": "1 bord (150g)",          "kh_portie": 5},
            {"naam": "Groentenmix warm",    "portie": "1 bord (150g)",          "kh_portie": 8},
            {"naam": "Banaan",              "portie": "1 stuk middel (130g)",   "kh_portie": 30},
            {"naam": "Vruchtensap sinaas",  "portie": "1 glas (200ml)",         "kh_portie": 20},
            {"naam": "Sportdrank",          "portie": "1 bidon (500ml)",        "kh_portie": 35},
            {"naam": "Appelmoes",           "portie": "1 schaaltje (150g)",     "kh_portie": 27},
        ],
    }

    # Alle producten tonen als keuze
    seen = set()
    producten = []
    for foods in RACEDAG_FOODS.values():
        for p in foods:
            if p["naam"] not in seen:
                seen.add(p["naam"])
                producten.append(p)
    saved_rd  = data.get("rd_waarden", {})

    # ── Voortgangsbalk + avatar bij overschrijding ──────────────────────────
    # Standaard producten
    _kh_balk = sum(
        st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0) * p["kh_portie"]
        for p in producten
    )
    # Eigen producten meetellen in de balk
    _eigen_rd_n = st.session_state.get(f"rd_eigen_{maaltijd_naam}_n", 0)
    for _ei in range(_eigen_rd_n):
        _ekh_rd   = st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei}_kh",   0.0)
        _eport_rd = st.session_state.get(f"rd_eigen_{maaltijd_naam}_{_ei}_port", 0.0)
        _kh_balk += _ekh_rd * _eport_rd
    _pct_balk  = min(100, round((_kh_balk / kh_max) * 100)) if kh_max > 0 else 0
    _over_balk = _kh_balk > kh_max
    if _over_balk:        _kleur_balk = "#ef4444"
    elif _pct_balk >= 25: _kleur_balk = "#22c55e"
    elif _pct_balk >= 15: _kleur_balk = "#fbbf24"
    else:                 _kleur_balk = "#f97316"
    st.markdown(
        f'<div style="background:#1e293b;border-radius:8px;height:10px;margin:0 0 8px 0;">' +
        f'<div style="width:{_pct_balk}%;height:100%;background:{_kleur_balk};border-radius:8px;"></div>' +
        f'</div>',
        unsafe_allow_html=True
    )
    if _over_balk:
        st.markdown(
            '<div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;' +
            'background:rgba(239,68,68,0.1);border:1px solid #ef4444;' +
            'border-radius:10px;padding:8px 12px;">' +
            '<img src="' + MASCOT_B64 + '" style="height:36px;width:auto;flex-shrink:0;">' +
            '<span style="color:#fca5a5;font-size:0.80rem;">' +
            '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van deze maaltijd!</span>' +
            '</div>',
            unsafe_allow_html=True
        )

        # Expander met label + groen bolletje
    rd_is_groen = st.session_state.get("rd_status_bevestigd", False)
    rd_dot      = "🟢 " if rd_is_groen else ""
    rd_exp_label = f"{rd_dot}**Voedingsmiddelen laatste maaltijd voor de race**"

    with st.expander(rd_exp_label, expanded=False):
        # Header
        st.markdown(
            f'<div style="font-size:0.7rem;color:#64748b;font-weight:700;letter-spacing:0.1em;'
            f'text-transform:uppercase;margin-bottom:8px;">'
            f'Voedingsmiddel · portiegrootte · KH/portie · aantal porties</div>',
            unsafe_allow_html=True
        )

        ontbijt_kh = 0

        # Standaard producten
        for product in producten:
            ss_key = f"rd_{maaltijd_naam}_{product['naam']}"
            if ss_key not in st.session_state:
                st.session_state[ss_key] = int(saved_rd.get(ss_key, 0))
            if not isinstance(st.session_state.get(ss_key), int):
                st.session_state[ss_key] = 0

            pc1, pc2 = st.columns([5, 1])
            with pc1:
                st.markdown(
                    f'<div style="padding:6px 0 2px;color:#f1f5f9;font-size:0.88rem;font-weight:600;line-height:1.4;">'
                    f'{product["naam"]} '
                    f'<span style="color:#64748b;font-size:0.78rem;font-weight:400;">'
                    f'— {product["portie"]} · {product["kh_portie"]}g KH/portie</span></div>',
                    unsafe_allow_html=True
                )
            with pc2:
                val = st.number_input("p", min_value=0, max_value=20, step=1,
                                      key=ss_key, label_visibility="collapsed")
            kh = val * product["kh_portie"]
            ontbijt_kh += kh
            if val > 0:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#f97316;margin:-4px 0 6px 0;text-align:right;">'
                    f'→ {val}× {product["kh_portie"]}g = <b>{round(kh)}g KH</b></div>',
                    unsafe_allow_html=True
                )

        # Eigen producten
        st.markdown('<hr style="border-color:#1e293b;margin:10px 0;">', unsafe_allow_html=True)
        eigen_key_base = f"rd_eigen_{maaltijd_naam}"
        n_eigen = st.session_state.get(f"{eigen_key_base}_n", 0)

        eigen_kh_total = 0
        for i in range(n_eigen):
            e_naam = st.session_state.get(f"{eigen_key_base}_{i}_naam", "")
            e_kh   = st.session_state.get(f"{eigen_key_base}_{i}_kh",   0.0)
            e_port = st.session_state.get(f"{eigen_key_base}_{i}_port", 0.0)

            if i == 0:
                lc1, lc2, lc3, lc4 = st.columns([4, 2, 2, 0.6])
                with lc1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PRODUCTNAAM</div>', unsafe_allow_html=True)
                with lc2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH/PORTIE (g)</div>', unsafe_allow_html=True)
                with lc3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">PORTIES</div>', unsafe_allow_html=True)

            ec1, ec2, ec3, ec4 = st.columns([4, 2, 2, 0.6])
            with ec1:
                new_naam = st.text_input("Naam", value=e_naam, key=f"{eigen_key_base}_{i}_naam_inp",
                                         placeholder="bv. Rijstwafel", label_visibility="collapsed")
                st.session_state[f"{eigen_key_base}_{i}_naam"] = new_naam
            with ec2:
                new_kh = st.number_input("KH/portie", value=float(e_kh), min_value=0.0, step=1.0,
                                         key=f"{eigen_key_base}_{i}_kh_inp",
                                         label_visibility="collapsed", help="KH per portie — zie verpakking")
                st.session_state[f"{eigen_key_base}_{i}_kh"] = new_kh
            with ec3:
                new_port = st.number_input("Porties", value=float(e_port), min_value=0.0, step=1.0,
                                           key=f"{eigen_key_base}_{i}_port_inp",
                                           label_visibility="collapsed")
                st.session_state[f"{eigen_key_base}_{i}_port"] = new_port
            with ec4:
                if st.button("🗑", key=f"{eigen_key_base}_{i}_del", help="Verwijder", use_container_width=True):
                    for j in range(i, n_eigen - 1):
                        for field in ["naam", "kh", "port"]:
                            st.session_state[f"{eigen_key_base}_{j}_{field}"] = \
                                st.session_state.get(f"{eigen_key_base}_{j+1}_{field}", 0 if field != "naam" else "")
                    for field in ["naam", "kh", "port"]:
                        st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}", None)
                        st.session_state.pop(f"{eigen_key_base}_{n_eigen-1}_{field}_inp", None)
                    st.session_state[f"{eigen_key_base}_n"] = n_eigen - 1
                    st.rerun()

            eigen_kh_i = new_kh * new_port
            eigen_kh_total += eigen_kh_i
            if new_port > 0 and new_kh > 0:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#3b82f6;margin:-4px 0 4px 0;text-align:right;">'
                    f'→ {new_port:.0f}× {new_kh:.0f}g = <b>{round(eigen_kh_i)}g KH</b></div>',
                    unsafe_allow_html=True
                )

        st.caption("Noteer bij eigen producten het aantal koolhydraten per portie (zie verpakking)")
        if st.button("➕  Voeg eigen product toe", key=f"{eigen_key_base}_add", use_container_width=True):
            st.session_state[f"{eigen_key_base}_n"] = n_eigen + 1
            st.rerun()

        ontbijt_kh = round(ontbijt_kh + eigen_kh_total)

        # Toggle knop: opslaan ↔ aanpassen
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _pct_knop    = min(100, round((ontbijt_kh / kh_max) * 100)) if kh_max > 0 else 0
        _over_knop   = ontbijt_kh > kh_max
        _reeds_groen = st.session_state.get("rd_status_bevestigd", False)
        if _reeds_groen:
            _btn_lbl  = "🔓  Wijzigen"
            _btn_type = "secondary"
        else:
            _btn_lbl  = "Dagdeel opslaan"
            _btn_type = "primary"
        if st.button(_btn_lbl, key="rd_save", use_container_width=True, type=_btn_type):
            if _reeds_groen:
                st.session_state["rd_status_bevestigd"] = False
            else:
                st.session_state["rd_status_bevestigd"] = (_pct_knop >= 25 and not _over_knop)
            # Bewaar rd_waarden bij klikken zodat ze behouden blijven bij navigatie
            _rd_waarden_save = {
                f"rd_{maaltijd_naam}_{p['naam']}": st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0)
                for p in producten
            }
            if "coach_data" not in st.session_state:
                st.session_state.coach_data = {}
            st.session_state.coach_data["rd_waarden"]    = _rd_waarden_save
            st.session_state.coach_data["rd_status"]     = st.session_state.get("rd_status_bevestigd", False)
            st.session_state.coach_data["ontbijt_kh"]    = ontbijt_kh
            st.session_state.coach_data["ontbijt_timing"] = ontbijt_keuze
            st.session_state.coach_data["ontbijt_tijd"]  = ontbijt_tijd
            st.session_state.coach_data["maaltijd_moment"] = maaltijd_naam
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="rd_prev"):
            st.session_state.coach_stap = 3
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="rd_next", use_container_width=True):
            rd_waarden = {f"rd_{maaltijd_naam}_{p['naam']}": st.session_state.get(f"rd_{maaltijd_naam}_{p['naam']}", 0)
                          for p in producten}
            st.session_state.coach_data.update({
                "ontbijt_kh":      ontbijt_kh,
                "ontbijt_timing":  ontbijt_keuze,
                "ontbijt_tijd":    ontbijt_tijd,
                "maaltijd_moment": maaltijd_naam,
                "pre_totaal_kh":   ontbijt_kh,
                "rd_waarden":      rd_waarden,
                "rd_status":       st.session_state.get("rd_status_bevestigd", False),
            })
            st.session_state.coach_stap = 5
            st.rerun()



def _stap_raceplan():
    data = st.session_state.get("coach_data", {})
    # Sport + duur balk + wetenschappelijke adviezen (geen KH grammen)
    _sport     = data.get("sport", "")
    _tot_min   = data.get("totale_min", 0)
    _sport_icon = SPORT_ICONS.get(_sport, "🏅")

    # Adviezen per sport per tijdsduur
    RACE_ADVIEZEN = {
        "Fietsen": {
            (0,   75):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (75,  120):  ["Kies voor een mix van vloeibare en vaste koolhydraatbronnen",
                          "Sportdrank + rijstwafel of reep: combineer gel met vast voedsel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 181):  ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Wissel regelmatig af tussen vloeibaar en vast",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (181, 9999): ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Kies producten die je al gebruikt hebt tijdens training",
                          "Geen nieuwe producten op racedag - alleen vertrouwde keuzes"],
        },
        "Lopen": {
            (0,   60):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (60,  120):  ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 181):  ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (181, 9999): ["Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank of gel",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Triatlon": {
            (0,   60):   ["Zwemmen: niet mogelijk om in te nemen — start optimaal gevoed",
                          "Fiets: vloeibare koolhydraatbronnen (sportdrank)",
                          "Loop: water of sportdrank volstaat bij sprint",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (60,  120):  ["Fiets is het hoofdtankmoment — start onmiddellijk na T1",
                          "Kies bij voorkeur vloeibare koolhydraatbronnen: sportdrank + gel",
                          "Loop: gel of sportdrank, kies voor vloeibare bronnen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (120, 240):  ["Fiets: kies voor een mix van gels, vaste voeding en sportdrank",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Loop: bij voorkeur vloeibaar (gel + water), GI-gevoeliger na fietsen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (240, 9999): ["Fiets: mix van gels, repen, sportdrank en vast voedsel",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Loop: vloeibaar + cola in het laatste deel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Duatlon": {
            (0,   75):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (75,  150):  ["Fiets = hoofdtankmoment: kies bij voorkeur vloeibare koolhydraatbronnen",
                          "Gel aan start 2e loop is essentieel",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (150, 210):  ["Kies voor een mix van gels, vaste voeding en sportdrank op de fiets",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "2e loop: gel + water, kies voor vloeibare bronnen",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (210, 9999): ["Kies voor een mix van gels, vaste voeding en sportdrank",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "Meer GI-stress dan triatlon — plan innametiming op rustige segmenten",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
        "Crossduatlon": {
            (0,   90):   ["Water of mondspoeling met sportdrank volstaat",
                          "Geen extra koolhydraten nodig",
                          "Druk door naar rapport opmaken!"],
            (90,  150):  ["MTB: kies bij voorkeur vloeibare koolhydraatbronnen — trillingen verhogen GI-stress",
                          "Neem in op vlakke/rechte stukken, nooit op technisch terrein",
                          "Kies producten die je al gebruikt hebt tijdens training"],
            (150, 9999): ["Kies voor een mix van gels en sportdrank",
                          "Kijk op de productinformatie: kies voor gels met verhouding 2:1 of 1:0.8 (glucose:fructose)",
                          "MTB: enkel vloeibaar, geen vast voedsel op technisch terrein",
                          "Kies producten die je al gebruikt hebt tijdens training"],
        },
    }

    # Zoek de juiste adviezen op basis van sport en duur
    sport_key = _sport if _sport in RACE_ADVIEZEN else "Fietsen"
    tips = []
    for (dmin, dmax), advies in RACE_ADVIEZEN[sport_key].items():
        if dmin <= _tot_min < dmax:
            tips = advies
            break
    if not tips and _tot_min >= 240:
        tips = list(RACE_ADVIEZEN[sport_key].values())[-1]

    # Balk: sport + duur
    sport_html = (
        '<div style="background:rgba(59,130,246,0.08);border:1px solid #3b82f6;'
        'border-radius:12px;padding:14px 18px;margin-bottom:16px;">' +
        f'<div style="color:#60a5fa;font-weight:800;font-size:0.85rem;margin-bottom:10px;">' +
        f'{_sport_icon} {_sport} &nbsp;·&nbsp; ⏱️ {_tot_min//60}u{_tot_min%60:02d}m</div>' +
        '<div style="color:#94a3b8;font-size:0.78rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-bottom:8px;">💡 Advies voor jouw race</div>'
    )
    for tip in tips:
        sport_html += (
            f'<div style="display:flex;gap:8px;margin-bottom:6px;align-items:flex-start;">' +
            f'<span style="color:#f97316;flex-shrink:0;">→</span>' +
            f'<span style="color:#e2e8f0;font-size:0.85rem;">{tip}</span></div>'
        )
    # Voeg oproep toe onderaan, behalve bij protocollen zonder KH inname
    geen_kh = any("Geen extra koolhydraten nodig" in tip for tip in tips)
    if not geen_kh:
        sport_html += (
            '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #1e3a5f;">' +
            '<span style="color:#60a5fa;font-size:0.85rem;">'
            '📝 Kies hieronder de producten die je wenst te gebruiken in je race ' +
            'en ik giet ze in een voorlopig schema dat je zelf nog kan aanvullen of wijzigen.</span></div>'
        )
    sport_html += '</div>'
    # Avatar naast de blauwe kader
    avatar_html = (
        '<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px;">' +
        f'<img src="{MASCOT_B64}" style="height:80px;width:auto;flex-shrink:0;margin-top:4px;">' +
        '<div style="flex:1;">' + sport_html + '</div>' +
        '</div>'
    )
    st.markdown(avatar_html, unsafe_allow_html=True)

    def _prod_blok(label, kleur, emoji, key_n, key_naam, key_kh,
                       default_n, placeholder, default_kh, eenheid="KH/stuk"):
        n = st.number_input(f"Aantal {label.lower()}", 0, 8, default_n,
                            key=key_n, label_visibility="collapsed")
        pool_items = []
        for i in range(int(n)):
            c1, c2, c3 = st.columns([3, 1.5, 0.8])
            with c1:
                naam = st.text_input("naam", key=f"{key_naam}_{i}",
                                     placeholder=placeholder, label_visibility="collapsed")
            with c2:
                kh = st.number_input(eenheid, key=f"{key_kh}_{i}",
                                     min_value=0, value=default_kh, label_visibility="collapsed")
            with c3:
                st.markdown(
                    f'<div style="padding:8px 4px;font-size:0.85rem;font-weight:700;' +
                    f'color:#f97316;text-align:center;">{kh}g</div>',
                    unsafe_allow_html=True)
            if naam:
                pool_items.append({"naam": naam, "kh": kh})
        return pool_items

    def _sectie_header(label, kleur, emoji):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:14px 0 6px 0;">' +
            f'<span style="font-size:1.1rem;">{emoji}</span>' +
            f'<span style="color:{kleur};font-weight:800;font-size:0.88rem;'
            f'letter-spacing:0.08em;">{label}</span></div>',
            unsafe_allow_html=True)

    # ── 1. Sportdrank ────────────────────────────────────────────────────────
    _sectie_header("SPORTDRANK", "#3b82f6", "🥤")
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Naam &nbsp;·&nbsp; KH per 500ml &nbsp;·&nbsp; Totaal</div>', unsafe_allow_html=True)
    drank_pool = _prod_blok("Sportdrank", "#3b82f6", "🥤",
                            "rp_n_drank", "rp_drank", "rp_dkh",
                            1, "bijv. Maurten 320", 70, "KH/500ml")

    # ── 2. Energy gels ───────────────────────────────────────────────────────
    _sectie_header("ENERGY GELS", "#60a5fa", "⚡")
    gel_col1, gel_col2 = st.columns(2)
    with gel_col1:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Gewone gels &nbsp;·&nbsp; KH/gel</div>', unsafe_allow_html=True)
        gels_pool = _prod_blok("Gel", "#60a5fa", "⚡",
                               "rp_n_gels", "rp_gel", "rp_gkh",
                               1, "bijv. SIS Go Gel", 22, "KH/gel")
    with gel_col2:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Gels met cafeïne &nbsp;·&nbsp; KH/gel</div>', unsafe_allow_html=True)
        cafe_pool = _prod_blok("Cafeïne gel", "#f59e0b", "☕",
                               "rp_n_cafe", "rp_cafe", "rp_ckh",
                               0, "bijv. SIS Caffeine Gel", 22, "KH/gel")

    # ── 3. Vaste voeding ─────────────────────────────────────────────────────
    _sectie_header("VASTE VOEDING", "#10b981", "🍌")
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Naam &nbsp;·&nbsp; KH per portie &nbsp;·&nbsp; Totaal</div>', unsafe_allow_html=True)
    vast_pool = _prod_blok("Vast voedsel", "#10b981", "🍌",
                           "rp_n_vast", "rp_vast", "rp_vkh",
                           0, "bijv. Rijstwafel, banaan", 25, "KH/portie")

    # ── 4. Supplementen ───────────────────────────────────────────────────────
    _sectie_header("SUPPLEMENTEN", "#8b5cf6", "💊")
    supp_col1, supp_col2 = st.columns(2)
    with supp_col1:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">ORS tabletten</div>', unsafe_allow_html=True)
        ors_naam  = st.text_input("ORS", placeholder="bijv. SIS Hydro, Precision ORS",
                                  key="rp_ors_naam", label_visibility="collapsed")
        ors_dosis = st.number_input("per uur", 0, 10, 0, key="rp_ors_dosis",
                                    label_visibility="collapsed", help="Aantal ORS tabletten per uur")
        st.caption("Tabletten per uur")
    with supp_col2:
        st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Cafeïne gum</div>', unsafe_allow_html=True)
        gum_naam = st.text_input("Gum", placeholder="bijv. Run Gum, Athlete Gum",
                                 key="rp_gum_naam", label_visibility="collapsed")
        gum_mg   = st.number_input("mg cafeïne/stuk", 0, 200, 0, 25, key="rp_gum_mg",
                                   label_visibility="collapsed", help="mg cafeïne per stuk")
        st.caption("mg cafeïne per stuk")

    st.markdown("<br>", unsafe_allow_html=True)

    pool = {
        "drank": drank_pool,
        "gels":  gels_pool,
        "cafe":  cafe_pool,
        "vast":  vast_pool,
        "supplementen": {
            "ors_naam":  ors_naam,
            "ors_dosis": ors_dosis,
            "gum_naam":  gum_naam,
            "gum_mg":    gum_mg,
        },
    }

    # ── Knoppen: Vorige boven Preview, breedte = vaste voeding sectie ─────────
    if st.button("← Vorige", key="rp_prev"):
        st.session_state.coach_data["pool"] = pool
        st.session_state.coach_stap = 4
        st.rerun()
    if st.button("👁  Preview schema", key="rp_preview", use_container_width=True):
        st.session_state.coach_data["pool"] = pool
        st.session_state["rp_show_preview"] = True
        st.rerun()

    # ── Preview schema ─────────────────────────────────────────────────────────    if st.session_state.get("rp_show_preview", False):
        import math
        from datetime import datetime, timedelta

        data       = st.session_state.get("coach_data", {})
        sport      = data.get("sport", "Fietsen")
        totale_min = data.get("totale_min", 180)
        temp       = data.get("temp", 18)
        vochtigheid = data.get("vochtigheid", 50)
        hoogte     = data.get("hoogte", 0)
        start_str  = data.get("start_time", "09:00")
        gewicht    = data.get("gewicht", 70)
        niveau     = data.get("niveau", "Recreatief")
        ervaring   = data.get("ervaring", "Eerste wedstrijd")
        min_kh     = data.get("min_kh", 60)
        max_kh     = data.get("max_kh", 90)
        start_dt   = datetime.strptime(start_str, "%H:%M")
        aantal_uren = math.ceil(totale_min / 60)

        # ── Sport-fase labels ──────────────────────────────────────────────────
        FASE_LABELS = {
            "Triatlon": {
                1: ("🏊", "Zwemmen", "Geen inname mogelijk — start gevoed"),
                2: ("🚴", "Fietsen", "Hoofdtankmoment — start direct bij T1"),
                3: ("🚴", "Fietsen", ""),
                4: ("🚴", "Fietsen", ""),
                5: ("🏃", "Lopen", "Vloeibaar only, GI-gevoeliger na fietsen"),
                6: ("🏃", "Lopen", ""),
                7: ("🏃", "Lopen", ""),
            },
            "Duatlon": {
                1: ("🏃", "Loop 1", "Hoge intensiteit — geen inname mogelijk"),
                2: ("🚴", "Fietsen", "Hoofdtankmoment — start direct"),
                3: ("🚴", "Fietsen", ""),
                4: ("🏃", "Loop 2", "Gel mee vanuit T2"),
                5: ("🏃", "Loop 2", ""),
            },
            "Crossduatlon": {
                1: ("🏃", "Trail 1", "Technisch terrein — geen inname"),
                2: ("🚵", "MTB", "Neem in op vlakke stukken, vloeibaar only"),
                3: ("🚵", "MTB", ""),
                4: ("🏃", "Trail 2", "Gel mee vanuit T2"),
            },
        }

        def get_fase(sport, uur_num, totale_min):
            if sport not in FASE_LABELS:
                return None
            fasen = FASE_LABELS[sport]
            # Schaal uren naar fases op basis van totale duur
            if sport == "Triatlon":
                zwem_uren = 1
                loop_start = max(3, aantal_uren - max(1, aantal_uren // 3))
                if uur_num <= zwem_uren:
                    return fasen.get(1)
                elif uur_num < loop_start:
                    return fasen.get(2)
                else:
                    return fasen.get(5)
            return fasen.get(uur_num)

        # ── Geen KH drempel ───────────────────────────────────────────────────
        geen_kh_drempel = {"Fietsen": 75, "Lopen": 60, "Duatlon": 75, "Crossduatlon": 90}
        geen_kh = totale_min < geen_kh_drempel.get(sport, 75)

        # ── Globale instellingen ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        # CSS voor uitlijning preview met rest van pagina
        st.markdown("""
        <style>
        div[data-testid="stExpander"] > details { background-color: #0f172a !important; }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(
            '<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:12px;">' +
            f'<img src="{MASCOT_B64}" style="height:72px;width:auto;flex-shrink:0;margin-top:4px;">' +
            '<div style="flex:1;background:#0f172a;border:2px solid #3b82f6;border-radius:14px;padding:14px 18px;">' +
            '<div style="color:#60a5fa;font-weight:800;font-size:0.9rem;margin-bottom:4px;">👁  PREVIEW RACEPLAN — aanpasbaar</div>' +
            '<div style="color:#64748b;font-size:0.78rem;">Pas de globale instellingen aan of wijzig producten per uur. Klik daarna op Genereer plan om door te gaan.</div>' +
            '</div></div>',
            unsafe_allow_html=True
        )

        # Vocht berekening
        basis_vocht = 800 if temp > 25 else (600 if temp > 15 else 400)
        f_factor    = (hoogte / 1000) * 0.15 + (0.15 if vochtigheid > 70 else 0)
        # Sport-correctie: lopen/triatlon-lopen zweet meer
        sport_factor = 1.15 if sport in ["Lopen", "Duatlon", "Crossduatlon"] else 1.0
        if sport == "Triatlon": sport_factor = 1.1  # gemiddeld over zwem+fiets+loop
        vocht_uur   = round(basis_vocht * (1 + f_factor) * sport_factor / 10) * 10
        vocht_pm    = round(vocht_uur / 3 / 10) * 10  # per innamemoment
        gel_interval = 40   # minuten tussen gels
        vast_vanaf   = 1    # vast voedsel vanaf uur 1
        cafe_vanaf   = 2    # cafeïne vanaf uur 2

                # ── Bouw lijst van alle producten ─────────────────────────────────────
        alle_opties = []
        kh_map      = {}
        emoji_map   = {}

        if pool.get("drank"):
            for p in pool["drank"]:
                naam  = p.get("naam", p.get("name", "Sportdrank"))
                kh_pm = round((p["kh"] / 500) * vocht_pm)
                lbl   = f"🥤 {naam} ({vocht_pm}ml)"
                alle_opties.append(lbl)
                kh_map[lbl]    = kh_pm
                emoji_map[lbl] = "🥤"

        if pool.get("gels"):
            for p in pool["gels"]:
                naam = p.get("naam", p.get("name", "Gel"))
                lbl  = f"⚡ {naam}"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = "⚡"

        if pool.get("vast"):
            for p in pool["vast"]:
                naam = p.get("naam", p.get("name", "Vast"))
                lbl  = f"🍌 {naam}"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = "🍌"

        if pool.get("cafe"):
            for p in pool["cafe"]:
                naam = p.get("naam", p.get("name", "Cafeïne gel"))
                lbl  = f"☕ {naam}"
                alle_opties.append(lbl)
                kh_map[lbl]    = p["kh"]
                emoji_map[lbl] = "☕"

        alle_opties += ["— leeg —"]
        kh_map["— leeg —"] = 0

        # Drank label (eerste optie indien beschikbaar)
        drank_lbl = next((l for l in alle_opties if l.startswith("🥤")), "— leeg —")
        gel_lbl   = next((l for l in alle_opties if l.startswith("⚡")), None)
        vast_lbl  = next((l for l in alle_opties if l.startswith("🍌")), None)
        cafe_lbl  = next((l for l in alle_opties if l.startswith("☕")), None)

        # ── Per uur schema ────────────────────────────────────────────────────
        totaal_kh_race    = 0
        totaal_vocht_race = 0


        # Sport-specifieke tips per uur
        UUR_TIPS = {
            "Fietsen":      "Kies per intervalmoment één product: sportdrank, gel of vast voedsel. Voeg water toe bij gels.",
            "Lopen":        "Kies per intervalmoment één product: gel of sportdrank. Neem altijd water bij een gel.",
            "Triatlon":     "Fietsgedeelte = hoofdtankmoment. Loopgedeelte: kies gels met water, vermijd vast voedsel.",
            "Duatlon":      "Fiets = hoofdtankmoment. Neem bij T2 een gel mee voor de tweede loopfase.",
            "Crossduatlon": "Neem in op vlakke MTB-stukken. Kies gels met water, geen vast voedsel op technisch terrein.",
        }
        uur_tip = UUR_TIPS.get(sport, "")

        # Kolomtitels
        t1, t2, t3, tplus, t4, t5, t6 = st.columns([1.1, 2.2, 0.8, 0.25, 1.8, 0.7, 0.35])
        with t1: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">TIJDSTIP</div>', unsafe_allow_html=True)
        with t2: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KOOLHYDRAATBRON</div>', unsafe_allow_html=True)
        with t3: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">AANTAL</div>', unsafe_allow_html=True)
        with t4: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">WATER</div>', unsafe_allow_html=True)
        with t5: st.markdown('<div style="font-size:0.68rem;color:#64748b;font-weight:700;">KH</div>', unsafe_allow_html=True)

        for u in range(aantal_uren):
            u_num    = u + 1
            is_last  = (u == aantal_uren - 1)
            uur_start = start_dt + timedelta(hours=u)
            cur_min  = round(min_kh * 0.6) if is_last else min_kh
            cur_max  = round(max_kh * 0.6) if is_last else max_kh
            fase     = get_fase(sport, u_num, totale_min)

            # Fase label
            fase_html = ""
            if fase:
                fase_icon, fase_naam, fase_tip = fase
                fase_html = f' &nbsp;<span style="color:#cbd5e1;font-size:0.75rem;">{fase_icon} {fase_naam}'
                if fase_tip:
                    fase_html += f' — {fase_tip}'
                fase_html += '</span>'

            # Tip per uur
            if geen_kh or (fase and "Geen inname" in fase[2]):
                _uur_tip = "💧 Enkel water of mondspoeling"
            elif is_last:
                _uur_tip = "🏁 Laatste uur — kleine slokjes, geen vast voedsel meer"
            elif u_num == 1:
                _uur_tip = "⚡ Start vroeg met innemen — wacht niet op honger of dorst"
            elif fase and "Zwemmen" in fase[1]:
                _uur_tip = "🏊 Geen inname mogelijk — start gevoed aan het fietsen"
            elif fase and "Loop" in fase[1]:
                _uur_tip = "Kies per rij één product. Neem bij een gel altijd water via de waterkolom."
            elif sport == "Lopen":
                _uur_tip = "Kies vloeibare bronnen. Voeg water toe via de waterkolom bij elke gel."
            else:
                _uur_tip = "Kies per rij één product. Voeg water toe bij gels via de waterkolom."

            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px 10px 0 0;padding:9px 14px;margin-top:12px;">'
                f'<span style="color:#f8fafc;font-weight:800;font-size:0.9rem;">'
                f'UUR {u_num} — {uur_start.strftime("%H:%M")}</span>'
                + (fase_html if fase_html else '')
                + (f'<div style="color:#94a3b8;font-size:0.72rem;margin-top:4px;">{uur_tip}</div>' if uur_tip and not geen_kh else "")
                + f'<div style="color:#93c5fd;font-size:0.73rem;margin-top:5px;">{_uur_tip}</div>' +
                f'</div>',
                unsafe_allow_html=True
            )

            # Notitie veld per uur
            notitie = st.text_input("Notitie", value="",
                placeholder="Notitie (bv. T2 — wisseling, cola station, ...)",
                key=f"prev_notitie_{u_num}",
                label_visibility="collapsed"
            )

            # Bouw standaard items voor dit uur
            # Laatste uur: 2 momenten (20-40), anders 3 (20-40-60)
            default_items = []
            if is_last:
                default_items = [
                    ("20min", drank_lbl if not geen_kh else "— leeg —"),
                    ("40min", "— leeg —"),
                ]
            else:
                default_items = [
                    ("20min", drank_lbl if not geen_kh else "— leeg —"),
                    ("40min", drank_lbl if not geen_kh else "— leeg —"),
                    ("60min", "— leeg —"),
                ]

            n_items_key = f"prev_n_items_{u_num}"
            if n_items_key not in st.session_state:
                # Na reset: lege rijen, anders defaults
                if st.session_state.get("rp_preview_leeg", False):
                    st.session_state[n_items_key] = 0
                else:
                    st.session_state[n_items_key] = len(default_items)

            n_items = st.session_state[n_items_key]

            uur_kh    = 0
            uur_vocht = 0
            # Wis leeg-flag na verwerking van eerste uur
            if u == aantal_uren - 1:
                st.session_state.pop("rp_preview_leeg", None)
            timing_opties = ["20min", "25min", "30min", "35min", "40min", "45min", "50min", "55min", "60min"]

            for i_idx in range(n_items):
                def_timing = default_items[i_idx][0] if i_idx < len(default_items) else "20min"
                def_prod   = default_items[i_idx][1] if i_idx < len(default_items) else "— leeg —"
                if def_prod not in alle_opties:
                    def_prod = "— leeg —"

                t_key = f"prev_t_{u_num}_{i_idx}"
                p_key = f"prev_p_{u_num}_{i_idx}"

                if t_key not in st.session_state:
                    st.session_state[t_key] = def_timing
                if p_key not in st.session_state:
                    st.session_state[p_key] = def_prod

                w_key = f"prev_w_{u_num}_{i_idx}"
                if w_key not in st.session_state:
                    # Standaard water bij gel/cafeïne
                    st.session_state[w_key] = "💧 water 150ml" if ("⚡" in st.session_state.get(p_key,"") or "☕" in st.session_state.get(p_key,"")) else "—"

                water_opties = ["—", "💧 water 100ml", "💧 water 150ml", "💧 water 200ml", "💧 water 250ml", "💧 water 500ml"]

                # Aantal key
                a_key = f"prev_a_{u_num}_{i_idx}"
                if a_key not in st.session_state:
                    st.session_state[a_key] = 1.0

                # Kolommen: timing | product | aantal | + | water | KH | 🗑
                c1, c2, c3, cplus, c4, c5, c6 = st.columns([1.1, 2.2, 0.8, 0.25, 1.8, 0.7, 0.35])
                with c1:
                    t_idx = timing_opties.index(st.session_state[t_key]) if st.session_state[t_key] in timing_opties else 0
                    gekozen_t = st.selectbox("", timing_opties, index=t_idx,
                        key=t_key, label_visibility="collapsed")
                with c2:
                    p_idx = alle_opties.index(st.session_state[p_key]) if st.session_state[p_key] in alle_opties else len(alle_opties)-1
                    gekozen_p = st.selectbox("", alle_opties, index=p_idx,
                        key=p_key, label_visibility="collapsed")
                with c3:
                    gekozen_a = st.number_input("", min_value=0.5, max_value=10.0,
                        value=float(st.session_state[a_key]),
                        step=0.5, key=a_key, label_visibility="collapsed")
                with cplus:
                    st.markdown('<div style="padding:8px 2px;text-align:center;color:#64748b;font-size:0.9rem;">+</div>', unsafe_allow_html=True)
                with c4:
                    w_idx = water_opties.index(st.session_state[w_key]) if st.session_state[w_key] in water_opties else 0
                    gekozen_w = st.selectbox("", water_opties, index=w_idx,
                        key=w_key, label_visibility="collapsed")
                with c5:
                    kh_val = round(kh_map.get(gekozen_p, 0) * gekozen_a)
                    st.markdown(
                        f'<div style="padding:8px 4px;font-size:0.82rem;font-weight:700;' +
                        f'color:{"#f97316" if kh_val > 0 else "#475569"};text-align:center;">' +
                        f'{kh_val}g KH</div>',
                        unsafe_allow_html=True
                    )
                with c6:
                    if st.button("🗑", key=f"prev_del_{u_num}_{i_idx}", help="Verwijder rij"):
                        for j in range(i_idx, n_items - 1):
                            st.session_state[f"prev_t_{u_num}_{j}"] = st.session_state.get(f"prev_t_{u_num}_{j+1}", "20min")
                            st.session_state[f"prev_p_{u_num}_{j}"] = st.session_state.get(f"prev_p_{u_num}_{j+1}", "— leeg —")
                            st.session_state[f"prev_a_{u_num}_{j}"] = st.session_state.get(f"prev_a_{u_num}_{j+1}", 1.0)
                            st.session_state[f"prev_w_{u_num}_{j}"] = st.session_state.get(f"prev_w_{u_num}_{j+1}", "—")
                        st.session_state[n_items_key] = max(0, n_items - 1)
                        st.rerun()
                # Vocht berekening
                vocht_water = 0
                if gekozen_w and gekozen_w != "—":
                    try:
                        vocht_water = int(gekozen_w.split()[-1].replace("ml","")) * gekozen_a
                    except: pass
                vocht_drank = 0
                if "🥤" in gekozen_p and vocht_pm:
                    vocht_drank = vocht_pm * gekozen_a
                uur_vocht += round(vocht_water + vocht_drank)
                uur_kh += kh_val

            # Rij toevoegen knop
            ca1, ca2 = st.columns([4, 1])
            with ca2:
                if st.button("➕ Rij", key=f"prev_add_{u_num}", help="Voeg rij toe"):
                    st.session_state[n_items_key] = n_items + 1
                    st.rerun()

            # Avatar bij overschrijding
            if not geen_kh and uur_kh > cur_max:
                st.markdown(
                    '<div style="display:flex;gap:10px;align-items:center;margin-top:6px;' +
                    'background:rgba(239,68,68,0.1);border:1px solid #ef4444;' +
                    'border-radius:10px;padding:8px 12px;">' +
                    f'<img src="{MASCOT_B64}" style="height:36px;width:auto;flex-shrink:0;">' +
                    '<span style="color:#fca5a5;font-size:0.80rem;">' +
                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van dit uur!</span>' +
                    '</div>',
                    unsafe_allow_html=True
                )

            # Totaal per uur
            if geen_kh:
                totaal_kleur = "#3b82f6"
                totaal_label = "Geen KH nodig"
            else:
                if uur_kh > cur_max:
                    totaal_kleur = "#ef4444"
                elif uur_kh >= cur_min:
                    totaal_kleur = "#22c55e"
                elif uur_kh >= cur_min * 0.7:
                    totaal_kleur = "#fbbf24"
                else:
                    totaal_kleur = "#ef4444"
                totaal_label = f"{uur_kh}g KH  {'✅' if cur_min <= uur_kh <= cur_max else ('⚠️' if uur_kh > cur_max else '❌')}"

            totaal_kh_race    += uur_kh
            totaal_vocht_race += uur_vocht

            # ── KH balk kleur ─────────────────────────────────────────────────
            if geen_kh:
                kh_pct   = 100
                kh_kleur = "#3b82f6"
            else:
                kh_pct   = min(100, round((uur_kh / cur_max) * 100)) if cur_max > 0 else 0
                kh_over  = uur_kh > cur_max
                if kh_over:              kh_kleur = "#ef4444"
                elif uur_kh >= cur_min:  kh_kleur = "#22c55e"
                elif kh_pct >= 50:       kh_kleur = "#fbbf24"
                elif kh_pct >= 30:       kh_kleur = "#f97316"
                else:                    kh_kleur = "#334155"

            # ── Vocht balk kleur ──────────────────────────────────────────────
            # Laatste uur: vochttarget op 40 min (2/3 van uur)
            vocht_target_uur = round(vocht_uur * 2/3) if is_last else vocht_uur
            vocht_pct   = min(100, round((uur_vocht / vocht_target_uur) * 100)) if vocht_target_uur > 0 else 0
            vocht_over  = uur_vocht > vocht_target_uur * 1.3
            if vocht_over:          vocht_kleur = "#ef4444"
            elif vocht_pct >= 80:   vocht_kleur = "#22c55e"
            elif vocht_pct >= 50:   vocht_kleur = "#fbbf24"
            else:                   vocht_kleur = "#f97316"

            # Avatar bij KH overschrijding
            if not geen_kh and uur_kh > cur_max:
                st.markdown(
                    '<div style="display:flex;gap:10px;align-items:center;margin:6px 0;' +
                    'background:rgba(239,68,68,0.1);border:1px solid #ef4444;' +
                    'border-radius:10px;padding:8px 12px;">' +
                    f'<img src="{MASCOT_B64}" style="height:36px;width:auto;flex-shrink:0;">' +
                    '<span style="color:#fca5a5;font-size:0.80rem;">' +
                    '<b>Hoe lekker ik koolhydraten ook vind</b> — we zitten over de limiet van dit uur!</span>' +
                    '</div>',
                    unsafe_allow_html=True
                )

            notitie_html = (
                f'<div style="color:#64748b;font-size:0.72rem;font-style:italic;'
                f'padding:4px 0 6px 0;">{notitie}</div>'
            ) if notitie else ""

            st.markdown(
                f'<div style="background:#0f172a;border-radius:0 0 10px 10px;padding:10px 14px 10px 14px;">' +
                notitie_html +
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">' +
                f'<span style="color:#94a3b8;font-size:0.7rem;font-weight:700;width:44px;flex-shrink:0;">KH</span>' +
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;">' +
                f'<div style="width:{kh_pct}%;height:100%;background:{kh_kleur};border-radius:4px;"></div></div>' +
                '</div>' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                f'<span style="color:#94a3b8;font-size:0.7rem;font-weight:700;width:44px;flex-shrink:0;">💧</span>' +
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;">' +
                f'<div style="width:{vocht_pct}%;height:100%;background:{vocht_kleur};border-radius:4px;"></div></div>' +
                '</div>' +
                f'</div>',
                unsafe_allow_html=True
            )

        # ── Race totaal ───────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:#1e293b;border-radius:12px;padding:14px 18px;'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="color:#94a3b8;font-size:0.85rem;font-weight:700;">TOTAAL RACE</span>'
            f'<div style="display:flex;gap:20px;align-items:center;">'
            f'<span style="color:#3b82f6;font-size:0.9rem;font-weight:700;">💧 {totaal_vocht_race}ml vocht</span>'
            f'<span style="color:#f8fafc;font-size:1rem;font-weight:900;">{totaal_kh_race}g KH</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Preview resetten", key="rp_reset_preview", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("prev_"):
                    del st.session_state[k]
            st.session_state["rp_preview_leeg"] = True
            st.session_state["rp_show_preview"] = True
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅  GENEREER PLAN", key="rp_gen", use_container_width=True):
            st.session_state.coach_data["pool"] = pool
            st.session_state.coach_stap = 6
            st.rerun()




def _portie_omschrijving(naam: str, portie: str, aantal: int) -> str:
    """Maak een leesbare portie omschrijving: '3 sneden wit brood'"""
    p = portie.lower()
    # Bepaal de maat-eenheid
    if "snede" in p:
        eenheid = "snede" if aantal == 1 else "sneden"
    elif "stuk" in p:
        eenheid = "stuk" if aantal == 1 else "stuks"
    elif "kom" in p:
        eenheid = "kom" if aantal == 1 else "kommen"
    elif "glas" in p:
        eenheid = "glas" if aantal == 1 else "glazen"
    elif "potje" in p:
        eenheid = "potje" if aantal == 1 else "potjes"
    elif "eetlpl" in p or "eetlepel" in p:
        eenheid = "eetlepel" if aantal == 1 else "eetlepels"
    elif "koffielepel" in p:
        eenheid = "koffielepel" if aantal == 1 else "koffielepels"
    elif "schaaltje" in p:
        eenheid = "schaaltje" if aantal == 1 else "schaaltjes"
    elif "reep" in p:
        eenheid = "reep" if aantal == 1 else "repen"
    elif "tas" in p:
        eenheid = "tas" if aantal == 1 else "tassen"
    elif "bidon" in p or "500ml" in p or "ml" in p:
        eenheid = "bidon" if aantal == 1 else "bidons"
    elif "bord" in p:
        eenheid = "bord" if aantal == 1 else "borden"
    else:
        eenheid = "portie" if aantal == 1 else "porties"
    return f"{aantal} {eenheid} {naam.lower()}"


def _bereken_raceplan(data: dict) -> list:
    """Bereken het uur-per-uur raceplan."""
    import math
    from datetime import datetime, timedelta

    pool        = data.get("pool", {})
    totale_min  = data.get("totale_min", 180)
    min_kh      = data.get("min_kh", 60)
    max_kh      = data.get("max_kh", 90)
    temp        = data.get("temp", 18)
    hoogte      = data.get("hoogte", 0)
    vochtigheid = data.get("vochtigheid", 50)
    start_str   = data.get("start_time", "09:00")
    sport       = data.get("sport", "Fietsen")
    start_dt    = datetime.strptime(start_str, "%H:%M")
    aantal_uren = math.ceil(totale_min / 60)

    geen_kh_drempel = {"Fietsen": 75, "Lopen": 60, "Duatlon": 75, "Crossduatlon": 90}
    geen_kh = totale_min < geen_kh_drempel.get(sport, 75)

    basis_vocht = 800 if temp > 25 else (600 if temp > 15 else 500)
    f_factor    = (hoogte / 1000) * 0.15 + (0.15 if vochtigheid > 70 else 0)
    vocht_per_m = round(((basis_vocht * (1 + f_factor)) / 3) / 10) * 10

    uren = []
    vast_idx   = 0
    cafe_strat = data.get("cafeine_strategie", "")

    for u in range(aantal_uren):
        is_last  = (u == aantal_uren - 1)
        cur_min  = round(min_kh * 0.6) if is_last else min_kh
        cur_max  = round(max_kh * 0.6) if is_last else max_kh
        uur_kh   = 0
        uur_start = start_dt + timedelta(hours=u)
        items    = []

        if geen_kh:
            items.append({"min": "20min", "emoji": "💧", "naam": "Water / mondspoeling", "kh": 0})
            items.append({"min": "40min", "emoji": "💧", "naam": "Water / mondspoeling", "kh": 0})
        else:
            if pool.get("drank"):
                d = pool["drank"][0]
                naam_d = d.get("naam", d.get("name", "Sportdrank"))
                kh_per_m = round((d["kh"] / 500) * vocht_per_m)
                for label in ["20min", "40min", "60min"]:
                    items.append({"min": label, "emoji": "🥤",
                                  "naam": f"{naam_d} ({vocht_per_m}ml)", "kh": kh_per_m})
                    uur_kh += kh_per_m

            if u == 1 and not is_last and pool.get("cafe") and "uur 2" in cafe_strat:
                c = pool["cafe"][0]
                naam_c = c.get("naam", c.get("name", "Cafeïne gel"))
                items.append({"min": "20min", "emoji": "☕", "naam": naam_c, "kh": c["kh"]})
                uur_kh += c["kh"]

            if "verspreid" in cafe_strat and not is_last and pool.get("cafe") and u % 2 == 1:
                c = pool["cafe"][0]
                naam_c = c.get("naam", c.get("name", "Cafeïne gel"))
                items.append({"min": "40min", "emoji": "☕", "naam": naam_c, "kh": c["kh"]})
                uur_kh += c["kh"]

            if pool.get("vast") and uur_kh < cur_min:
                item = pool["vast"][vast_idx % len(pool["vast"])]
                naam_v = item.get("naam", item.get("name", "Vast voedsel"))
                items.append({"min": "30min", "emoji": "🍌", "naam": naam_v, "kh": item["kh"]})
                uur_kh += item["kh"]
                vast_idx += 1

            if pool.get("gels") and uur_kh < cur_min:
                g = pool["gels"][0]
                naam_g = g.get("naam", g.get("name", "Gel"))
                items.append({"min": "45min", "emoji": "⚡", "naam": naam_g, "kh": g["kh"]})
                uur_kh += g["kh"]

            if is_last:
                items = [i for i in items if i["min"] == "20min"]
                items.append({"min": "40min", "emoji": "💧", "naam": "Water / spoelen", "kh": 0})

        uren.append({
            "uur": u + 1, "uur_start": uur_start.strftime("%H:%M"),
            "items": items, "uur_kh": round(uur_kh),
            "min_kh": cur_min, "max_kh": cur_max,
            "is_last": is_last, "geen_kh": geen_kh,
        })

    return uren, vocht_per_m


def _genereer_pdf(data: dict, gebruiker_naam: str) -> bytes:
    """Volledig PDF rapport: info + carboloading + racedag + uur-per-uur + snelkaart."""
    import io, math, base64
    from datetime import datetime, timedelta
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    KeepTogether, PageBreak, Image)
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.6*cm, leftMargin=1.6*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm)

    ORANJE  = colors.HexColor("#f97316")
    DONKER  = colors.HexColor("#0f172a")
    MIDDEL  = colors.HexColor("#1e293b")
    BLAUW   = colors.HexColor("#3b82f6")
    GRIJS   = colors.HexColor("#64748b")
    WIT     = colors.white
    LGRIJS  = colors.HexColor("#f1f5f9")
    GROEN   = colors.HexColor("#22c55e")
    GEEL    = colors.HexColor("#fbbf24")
    ROOD    = colors.HexColor("#ef4444")
    LORANJE = colors.HexColor("#fff7ed")
    LBLAUW  = colors.HexColor("#eff6ff")

    W, H  = A4
    breed = W - 3.2*cm

    def S(naam, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=DONKER, leading=13)
        base.update(kw)
        return ParagraphStyle(naam, **base)

    s_titel  = S("TT", fontSize=18, fontName="Helvetica-Bold", textColor=WIT,
                 alignment=TA_CENTER, leading=24)
    s_sub    = S("ST", fontSize=9.5, textColor=colors.HexColor("#fb923c"), alignment=TA_CENTER)
    s_sectie = S("SE", fontSize=11, fontName="Helvetica-Bold", textColor=ORANJE,
                 leading=16, spaceBefore=8, spaceAfter=3)
    s_label  = S("LA", fontSize=7.5, fontName="Helvetica-Bold", textColor=GRIJS, leading=11)
    s_waarde = S("WA", fontSize=10, fontName="Helvetica-Bold", textColor=DONKER, leading=14)
    s_kop    = S("KW", fontSize=8.5, fontName="Helvetica-Bold", textColor=WIT, leading=12)
    s_body   = S("BO", fontSize=8.5, textColor=colors.HexColor("#334155"), leading=12)
    s_tip    = S("TI", fontSize=8, textColor=DONKER, leading=12, leftIndent=6)
    s_footer = S("FO", fontSize=7, textColor=GRIJS, alignment=TA_CENTER, leading=10)
    s_uur_kop = S("UK", fontSize=9, fontName="Helvetica-Bold", textColor=WIT, leading=13)

    story = []

    # ── Mascot afbeelding laden ───────────────────────────────────────────────
    try:
        mascot_b64 = MASCOT_B64.split(",", 1)[1]
        mascot_bytes = base64.b64decode(mascot_b64)
        mascot_io = io.BytesIO(mascot_bytes)
        mascot_img = Image(mascot_io, width=1.2*cm, height=1.4*cm)
    except Exception:
        mascot_img = None

    def maak_header(titel_tekst, subtitel_tekst=""):
        """Bouw header met mascot logo."""
        if mascot_img:
            hdr_data = [[mascot_img,
                         Paragraph(titel_tekst, s_titel),
                         Paragraph("", s_body)]]
            hdr_t = Table(hdr_data, colWidths=[1.6*cm, breed-3.2*cm, 1.6*cm])
        else:
            hdr_data = [[Paragraph(titel_tekst, s_titel)]]
            hdr_t = Table(hdr_data, colWidths=[breed])
        hdr_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), DONKER),
            ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0),(-1,-1), 12),
            ("BOTTOMPADDING",(0,0),(-1,-1), 8),
            ("LEFTPADDING",(0,0),(-1,-1), 10),
            ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ]))
        blokken = [hdr_t]
        if subtitel_tekst:
            sub_t = Table([[Paragraph(subtitel_tekst, s_sub)]], colWidths=[breed])
            sub_t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), MIDDEL),
                ("TOPPADDING",(0,0),(-1,-1),5),
                ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ]))
            blokken.append(sub_t)
        return blokken

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINA 1 — ALGEMEEN + CARBOLOADING + RACEDAG
    # ══════════════════════════════════════════════════════════════════════════
    wedstrijd_naam = data.get("wedstrijd_naam", "")
    for blok in maak_header("CARBOO RACE NUTRITION PLAN", wedstrijd_naam.upper()):
        story.append(blok)
    story.append(Spacer(1, 10))

    # Atleet & wedstrijd
    story.append(Paragraph("ATLEET & WEDSTRIJD", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))
    atleet   = data.get("atleet_naam", gebruiker_naam)
    sport    = data.get("sport", "—")
    niveau   = data.get("niveau", "—")
    gewicht  = data.get("gewicht", "—")
    datum    = data.get("wedstrijd_datum", "—")
    start    = data.get("start_time", "—")
    eind     = data.get("eind_time", "—")
    totmin   = data.get("totale_min", 0)
    duur_str = f"{totmin//60}u{totmin%60:02d}m" if totmin else "—"
    temp     = data.get("temp", "—")
    vocht    = data.get("vochtigheid", "—")
    hoogte   = data.get("hoogte", "—")
    ervaring = data.get("ervaring", "—")

    info_rows = [
        [Paragraph("NAAM ATLEET",  s_label), Paragraph(atleet,  s_waarde),
         Paragraph("DISCIPLINE",   s_label), Paragraph(sport,   s_waarde)],
        [Paragraph("GEWICHT",      s_label), Paragraph(f"{gewicht} kg", s_waarde),
         Paragraph("SPORTNIVEAU",  s_label), Paragraph(niveau,  s_waarde)],
        [Paragraph("DATUM",        s_label), Paragraph(str(datum), s_waarde),
         Paragraph("START / EIND", s_label), Paragraph(f"{start} — {eind}", s_waarde)],
        [Paragraph("DUUR",         s_label), Paragraph(duur_str, s_waarde),
         Paragraph("TEMP / VOCHTIGHEID", s_label), Paragraph(f"{temp}°C  |  {vocht}%", s_waarde)],
        [Paragraph("HOOGTE",       s_label), Paragraph(f"{hoogte} m", s_waarde),
         Paragraph("ERVARING",     s_label), Paragraph(ervaring, s_waarde)],
    ]
    it = Table(info_rows, colWidths=[breed*0.18, breed*0.32, breed*0.22, breed*0.28])
    it.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT,LGRIJS,WIT,LGRIJS]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
    ]))
    story.append(it)
    story.append(Spacer(1, 10))

    # ── Carboloading ──────────────────────────────────────────────────────────
    dag_target = data.get("dag_target", 0)
    cl_data    = data.get("carboloading", {})
    cl_waarden = data.get("cl_waarden", {})

    story.append(Paragraph("CARBOLOADING — LAATSTE 48 UUR", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))

    if dag_target:
        doel = Table([[Paragraph("DAGDOELSTELLING", s_label),
                       Paragraph(f"{dag_target}g koolhydraten per dag", s_waarde)]],
                     colWidths=[breed*0.35, breed*0.65])
        doel.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),LORANJE),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),10),
            ("BOX",(0,0),(-1,-1),1,ORANJE),
        ]))
        story.append(doel)
        story.append(Spacer(1, 5))

    # KH_PORTIE map voor carboloading producten
    CL_KH_MAP = {
        "Wit brood":17,"Bruin brood":16,"Volkorenbrood":14,"Havermout":27,
        "Ontbijtgranen":25,"Muesli":30,"Granola (krokant)":26,
        "Melk (dierlijk)":9,"Plantaardige melk":9,"Banaan":30,"Appel":15,
        "Peer":19,"Kiwi":11,"Yoghurt natuur":6,"Plattekaas":4,
        "Confituur":3,"Honing":4,"Chocopasta":3,"Koffie met suiker":5,
        "Vruchtensap sinaas":20,"Sportdrank":35,
        "Rijstwafels":7,"Energiereep":40,"Rozijnen":15,"Dadelstroop":18,
        "Appel":20,"Dadels gedroogd":6,"Muesli/granenreep":26,
        "Speculoos":5,"Snoep/winegums":26,"Appelmoes":27,"Pannenkoek":27,
        "Pasta (hoofdmaaltijd)":75,"Pasta (bijgerecht)":37,
        "Rijst (hoofdmaaltijd)":81,"Rijst (bijgerecht)":42,
        "Aardappelen gekookt":30,"Groentenmix rauw":5,"Groentenmix warm":8,
    }
    CL_PORTIE_MAP = {
        "Wit brood":"1 snede","Bruin brood":"1 snede","Volkorenbrood":"1 snede",
        "Havermout":"1 kom","Ontbijtgranen":"1 kom","Muesli":"1 kom",
        "Granola (krokant)":"1 kom","Melk (dierlijk)":"1 glas",
        "Plantaardige melk":"1 glas","Banaan":"1 stuk","Appel":"1 stuk",
        "Peer":"1 stuk","Kiwi":"1 stuk","Yoghurt natuur":"1 potje",
        "Plattekaas":"4 eetlepels","Confituur":"1 koffielepel","Honing":"1 koffielepel",
        "Chocopasta":"1 koffielepel","Koffie met suiker":"1 tas","Vruchtensap sinaas":"1 glas",
        "Sportdrank":"1 bidon","Rijstwafels":"1 stuk","Energiereep":"1 reep",
        "Rozijnen":"1 handje","Muesli/granenreep":"1 reep","Appelmoes":"1 schaaltje",
        "Pannenkoek":"1 stuk","Dadels gedroogd":"1 stuk","Speculoos":"1 stuk",
        "Snoep/winegums":"1 zakje",
        "Pasta (hoofdmaaltijd)":"1 bord","Pasta (bijgerecht)":"1 bord",
        "Rijst (hoofdmaaltijd)":"1 bord","Rijst (bijgerecht)":"1 bord",
        "Aardappelen gekookt":"1 bord","Groentenmix rauw":"1 bord",
        "Groentenmix warm":"1 bord",
    }

    MAALTIJDEN_VOLGORDE = ["Ontbijt","Tussendoor VM","Lunch","Tussendoor NM","Avondmaal","Avond snack"]

    for dag_num in [1, 2]:
        dag_label = f"DAG {dag_num} — {'2 dagen voor race' if dag_num == 1 else '1 dag voor race'}"
        dag_vals  = cl_data.get(f"dag{dag_num}", {})
        totaal    = dag_vals.get("totaal", 0)
        target    = dag_vals.get("target", dag_target)
        pct       = dag_vals.get("pct", 0)
        bar_c     = GROEN if pct >= 90 else (GEEL if pct >= 70 else ROOD)

        # Dag header
        dag_hdr = Table([[
            Paragraph(dag_label, S("DH", fontSize=9, fontName="Helvetica-Bold",
                                   textColor=WIT, leading=13)),
            Paragraph(f"{totaal}g / {target}g  ({pct}%)",
                      S("DT", fontSize=9, fontName="Helvetica-Bold",
                        textColor=bar_c, alignment=TA_RIGHT, leading=13)),
        ]], colWidths=[breed*0.6, breed*0.4])
        dag_hdr.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),MIDDEL),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))
        story.append(dag_hdr)

        # Per maaltijdmoment: gekozen producten
        maaltijd_rows = [[
            Paragraph("MAALTIJDMOMENT", s_kop),
            Paragraph("GEKOZEN VOEDINGSMIDDELEN", s_kop),
            Paragraph("KH", s_kop),
        ]]
        for m_naam in MAALTIJDEN_VOLGORDE:
            moment_items = []
            for prod_naam, kh_pp in CL_KH_MAP.items():
                key = f"cl_d{dag_num}_{m_naam}_{prod_naam}"
                val = cl_waarden.get(key, 0)
                if val and val > 0:
                    portie_eenheid = CL_PORTIE_MAP.get(prod_naam, "portie")
                    # Maak leesbare beschrijving
                    omschr = _portie_omschrijving(prod_naam, portie_eenheid + " (x)", int(val))
                    kh_tot = round(val * kh_pp)
                    moment_items.append(f"{omschr}  →  {kh_tot}g KH")

            # Eigen producten
            eigen_key = f"eigen_d{dag_num}_{m_naam}"
            n_eigen = 0
            for k, v in cl_waarden.items():
                if k.startswith(eigen_key) and "_naam" in k:
                    n_eigen += 1
            for i in range(n_eigen):
                e_naam = cl_waarden.get(f"{eigen_key}_{i}_naam", "")
                e_kh   = cl_waarden.get(f"{eigen_key}_{i}_kh", 0)
                e_port = cl_waarden.get(f"{eigen_key}_{i}_port", 0)
                if e_naam and e_port > 0:
                    moment_items.append(f"{e_port:.0f}× {e_naam}  →  {round(e_kh*e_port)}g KH")

            if moment_items:
                m_target = round(dag_target * {"Ontbijt":0.25,"Tussendoor VM":0.083,
                    "Lunch":0.25,"Tussendoor NM":0.083,"Avondmaal":0.25,"Avond snack":0.083
                }.get(m_naam, 0.15))
                maaltijd_rows.append([
                    Paragraph(m_naam, s_body),
                    Paragraph("<br/>".join(moment_items), s_body),
                    Paragraph(f"doel: {m_target}g", S("MT", fontSize=7.5, textColor=GRIJS, leading=11)),
                ])

        if len(maaltijd_rows) > 1:
            ml_t = Table(maaltijd_rows, colWidths=[breed*0.22, breed*0.6, breed*0.18])
            ml_t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),DONKER),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
                ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ]))
            story.append(ml_t)
        else:
            story.append(Table([[Paragraph("Geen voedingsmiddelen ingevoerd voor deze dag.", s_body)]],
                               colWidths=[breed]))
        story.append(Spacer(1, 6))

    # Carboloading tips
    cl_tips = [
        "Kies licht verteerbare producten: pasta, rijst, wit brood, banaan, havermout.",
        "Beperk vezels, vetten en rauwe groenten in de 24u voor de race.",
        "Drink voldoende water maar vermijd overhydratie.",
        "Sla geen maaltijden over — verdeel je koolhydraten over 5-6 momenten per dag.",
    ]
    cl_tip_rows = [[Paragraph("ALGEMENE TIPS CARBOLOADING", s_kop)]]
    for tip in cl_tips:
        cl_tip_rows.append([Paragraph(f"  →  {tip}", s_tip)])
    cl_tip_t = Table(cl_tip_rows, colWidths=[breed])
    cl_tip_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),MIDDEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
    ]))
    story.append(cl_tip_t)
    story.append(Spacer(1, 10))

    # ── Laatste maaltijd ──────────────────────────────────────────────────────
    maaltijd_mom = data.get("maaltijd_moment", "Ontbijt")
    ont_timing   = data.get("ontbijt_timing", "—")
    ont_tijd     = data.get("ontbijt_tijd", "—")
    ont_kh       = data.get("ontbijt_kh", 0)
    rd_waarden   = data.get("rd_waarden", {})

    # Vocht richtlijn tijdens laatste maaltijd
    temp_val = data.get("temp", 18)
    if temp_val > 25:
        vocht_advies = "600–800ml in de 2-3u voor de start (warm weer)"
    elif temp_val > 15:
        vocht_advies = "400–600ml in de 2-3u voor de start"
    else:
        vocht_advies = "300–500ml in de 2-3u voor de start (koel weer)"

    story.append(Paragraph(f"LAATSTE MAALTIJD — {maaltijd_mom.upper()}", s_sectie))
    story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))

    rd_info_rows = [
        [Paragraph("TIMING", s_label), Paragraph(ont_timing, s_waarde),
         Paragraph("MAALTIJD OM", s_label), Paragraph(ont_tijd, s_waarde)],
        [Paragraph("TOTAAL KH", s_label), Paragraph(f"{ont_kh}g", s_waarde),
         Paragraph("AANBEVOLEN VOCHT", s_label), Paragraph(vocht_advies, s_body)],
    ]
    rd_t = Table(rd_info_rows, colWidths=[breed*0.18, breed*0.32, breed*0.22, breed*0.28])
    rd_t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
    ]))
    story.append(rd_t)

    # Gekozen voedingsmiddelen racedag
    ONTBIJT_PORTIE_MAP = {**CL_PORTIE_MAP,
        "Pasta (hoofdmaaltijd)":"1 bord","Pasta (bijgerecht)":"1 bord",
        "Rijst (hoofdmaaltijd)":"1 bord","Rijst (bijgerecht)":"1 bord",
        "Aardappelen gekookt":"1 bord","Groentenmix rauw":"1 bord",
        "Groentenmix warm":"1 bord","Sportdrank":"1 bidon",
    }

    rd_items = []
    for k, val in rd_waarden.items():
        if val and val > 0:
            # Key formaat: rd_Ontbijt_Havermout of rd_Lunch_Pasta
            parts = k.split("_", 2)
            prod_naam = parts[2] if len(parts) > 2 else k
            kh_pp    = CL_KH_MAP.get(prod_naam, 0)
            portie_e = ONTBIJT_PORTIE_MAP.get(prod_naam, "portie")
            omschr   = _portie_omschrijving(prod_naam, portie_e + " (x)", int(val))
            rd_items.append((omschr, round(val * kh_pp)))

    if rd_items:
        story.append(Spacer(1, 5))
        rd_rows = [[Paragraph("VOEDINGSMIDDEL — HOEVEELHEID", s_kop),
                    Paragraph("KH", s_kop)]]
        for omschr, kh in rd_items:
            rd_rows.append([Paragraph(omschr, s_body),
                            Paragraph(f"{kh}g", s_body)])
        rd_food_t = Table(rd_rows, colWidths=[breed*0.78, breed*0.22])
        rd_food_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DONKER),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),7),
            ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ]))
        story.append(rd_food_t)

    # Racedag tips (zonder cafeïne tip)
    rd_tips = [
        "Kies producten die je al getest hebt in training — geen nieuw voedsel op racedag.",
        "Kies licht verteerbaar: laag in vezels en vetten.",
        "Drink geen grote hoeveelheden vocht vlak voor de start — kleine slokjes.",
    ]
    story.append(Spacer(1, 5))
    rd_tip_rows = [[Paragraph("TIPS LAATSTE MAALTIJD", s_kop)]]
    for tip in rd_tips:
        rd_tip_rows.append([Paragraph(f"  →  {tip}", s_tip)])
    rd_tip_t = Table(rd_tip_rows, colWidths=[breed])
    rd_tip_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),MIDDEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRIJS,WIT]),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
    ]))
    story.append(rd_tip_t)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINA 2 — UUR-PER-UUR RACEPLAN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    for blok in maak_header("UUR-PER-UUR RACEPLAN",
                             f"{sport}  ·  {duur_str}  ·  Start {start}  ·  {atleet}"):
        story.append(blok)
    story.append(Spacer(1, 8))

    min_kh = data.get("min_kh", 0)
    max_kh = data.get("max_kh", 0)
    pool   = data.get("pool", {})
    supp   = pool.get("supplementen", {})
    uren, vocht_per_m = _bereken_raceplan(data)

    # Info balk
    info_txt = f"{temp}°C  ·  {vocht}% vochtigheid  ·  Vocht per innamemoment: {vocht_per_m}ml"
    if min_kh and max_kh:
        info_txt += f"  ·  KH-target: {min_kh}–{max_kh}g/uur"
    ib = Table([[Paragraph(info_txt, S("IB", fontSize=8, textColor=colors.HexColor("#93c5fd"),
                                        alignment=TA_CENTER, leading=12))]],
               colWidths=[breed])
    ib.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),MIDDEL),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(ib)
    story.append(Spacer(1, 8))

    # Per uur
    for uur_data in uren:
        u_num   = uur_data["uur"]
        u_start = uur_data["uur_start"]
        u_kh    = uur_data["uur_kh"]
        u_min   = uur_data["min_kh"]
        u_max   = uur_data["max_kh"]
        items   = uur_data["items"]
        geen_kh = uur_data["geen_kh"]
        is_last = uur_data["is_last"]

        bar_c = GROEN if u_kh >= u_min else (GEEL if u_kh >= u_min*0.8 else ROOD)
        if geen_kh: bar_c = BLAUW

        kh_info = ("Geen extra KH nodig" if geen_kh else
                   f"Berekend: {u_kh}g KH  |  Target: {u_min}–{u_max}g")

        uur_kop = Table([[
            Paragraph(f"UUR {u_num}   ⏰ {u_start}", s_uur_kop),
            Paragraph(kh_info, S("KI", fontSize=7.5, alignment=TA_RIGHT,
                                  textColor=bar_c, leading=11)),
        ]], colWidths=[breed*0.5, breed*0.5])
        uur_kop.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),DONKER),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))

        item_rows = []
        for item in items:
            item_rows.append([
                Paragraph(item["min"], S("MIN", fontSize=8, fontName="Helvetica-Bold",
                                          textColor=BLAUW, leading=12)),
                Paragraph(f"{item['emoji']}  {item['naam']}", s_body),
                Paragraph(f"{item['kh']}g" if item["kh"] > 0 else "—",
                          S("KHI", fontSize=8, textColor=ORANJE if item["kh"] > 0 else GRIJS,
                            fontName="Helvetica-Bold", leading=12, alignment=TA_RIGHT)),
            ])
        if not item_rows:
            item_rows.append([Paragraph("", s_body),
                              Paragraph("💧  Water", s_body),
                              Paragraph("—", s_body)])

        items_t = Table(item_rows, colWidths=[breed*0.15, breed*0.67, breed*0.18])
        items_t.setStyle(TableStyle([
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WIT,LGRIJS]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("BOX",(0,0),(-1,-1),0.3,colors.HexColor("#cbd5e1")),
            ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#e2e8f0")),
        ]))
        story.append(KeepTogether([uur_kop, items_t, Spacer(1, 6)]))

    # Supplementen
    if supp and any([supp.get("cafeine_mg"), supp.get("natrium_mg"), supp.get("vrij")]):
        story.append(Spacer(1, 4))
        story.append(Paragraph("SUPPLEMENTEN", s_sectie))
        story.append(HRFlowable(width=breed, thickness=1, color=ORANJE, spaceAfter=5))
        supp_rows = []
        if supp.get("cafeine_mg"):
            supp_rows.append([Paragraph("Cafeïne (totaal)", s_body),
                               Paragraph(f"{supp['cafeine_mg']} mg", s_waarde)])
        if supp.get("natrium_mg"):
            supp_rows.append([Paragraph("Natrium (per uur)", s_body),
                               Paragraph(f"{supp['natrium_mg']} mg/uur", s_waarde)])
        if supp.get("vrij"):
            supp_rows.append([Paragraph("Overige", s_body),
                               Paragraph(supp["vrij"], s_waarde)])
        if supp_rows:
            st_t = Table(supp_rows, colWidths=[breed*0.4, breed*0.6])
            st_t.setStyle(TableStyle([
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[LGRIJS,WIT]),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),8),
                ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ]))
            story.append(st_t)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINA 3 — SNELKAART (stuurbuis / arm)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    for blok in maak_header("SNELKAART — STUURBUIS / ARM",
                             f"{sport}  ·  {duur_str}  ·  Start {start}  ·  {atleet}"):
        story.append(blok)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Knip uit en bevestig op de stuurbuis of schrijf de emojis op je arm. Eén blokje = één uur.",
        S("INS", fontSize=8, textColor=GRIJS, alignment=TA_CENTER, leading=12)
    ))
    story.append(Spacer(1, 10))

    MAX_COLS = 4
    sym_rows = []
    sym_row  = []

    for uur_data in uren:
        u_num   = uur_data["uur"]
        u_start = uur_data["uur_start"]
        items   = uur_data["items"]
        geen_kh = uur_data["geen_kh"]
        u_kh    = uur_data["uur_kh"]

        if geen_kh:
            emoji_str = "💧"
            prod_str  = "Water"
        else:
            ec = {}
            for item in items:
                ec[item["emoji"]] = ec.get(item["emoji"], 0) + 1
            emoji_str = "  ".join(f"{e}×{n}" if n > 1 else e for e, n in ec.items())
            namen = list({item["naam"].split("(")[0].strip()[:14]
                         for item in items if item["kh"] > 0})
            prod_str = " / ".join(namen[:2])

        kh_txt = f"{u_kh}g KH" if not geen_kh and u_kh > 0 else "—"

        cel = [
            [Paragraph(f"UUR {u_num}   {u_start}",
                       S("UC", fontSize=7, fontName="Helvetica-Bold",
                         textColor=ORANJE, leading=10, alignment=TA_CENTER))],
            [Paragraph(emoji_str, S("EM", fontSize=16, leading=22, alignment=TA_CENTER))],
            [Paragraph(prod_str, S("NM", fontSize=6.5, textColor=GRIJS,
                                    alignment=TA_CENTER, leading=9))],
            [Paragraph(kh_txt, S("KT", fontSize=7, fontName="Helvetica-Bold",
                                   textColor=BLAUW, alignment=TA_CENTER, leading=10))],
        ]
        sym_row.append(cel)
        if len(sym_row) == MAX_COLS:
            sym_rows.append(sym_row)
            sym_row = []

    if sym_row:
        while len(sym_row) < MAX_COLS:
            sym_row.append([[Paragraph("", s_body)]])
        sym_rows.append(sym_row)

    col_w = breed / MAX_COLS
    for row in sym_rows:
        flat = []
        for cel in row:
            cel_tbl = Table(cel, colWidths=[col_w * 0.88])
            cel_tbl.setStyle(TableStyle([
                ("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("TOPPADDING",(0,0),(-1,-1),3),
                ("BOTTOMPADDING",(0,0),(-1,-1),3),
            ]))
            flat.append(cel_tbl)
        row_tbl = Table([flat], colWidths=[col_w]*MAX_COLS)
        row_tbl.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),1.5,ORANJE),
            ("INNERGRID",(0,0),(-1,-1),0.5,ORANJE),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("BACKGROUND",(0,0),(-1,-1),WIT),
        ]))
        story.append(row_tbl)
        story.append(Spacer(1, 5))

    # Legende
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width=breed, thickness=0.5, color=GRIJS, spaceAfter=5))
    leg_items = [["💧","Water / mondspoeling"],["🥤","Sportdrank"],
                 ["⚡","Energy gel"],["🍌","Vast voedsel"],["☕","Gel + cafeïne"]]
    leg_row = [[Paragraph(f"{s}  {l}", S("LG", fontSize=8, textColor=DONKER, leading=12))
               for s, l in leg_items]]
    leg_t = Table(leg_row, colWidths=[breed/5]*5)
    leg_t.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("BOX",(0,0),(-1,-1),0.5,GRIJS),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("BACKGROUND",(0,0),(-1,-1),LGRIJS),
    ]))
    story.append(leg_t)

    # Footer
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width=breed, thickness=0.5, color=GRIJS))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Gegenereerd door Carboo Race Nutrition  •  carboo-z9tbmypf2zc56jzqjwc6bo.streamlit.app  •  "
        "Dit plan is een richtlijn — overleg met een sportdiëtist voor gepersonaliseerd advies.",
        s_footer
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()



def _stap_samenvatting():
    data = st.session_state.get("coach_data", {})
    naam = st.session_state.get("current_user", {}).get("name", "Atleet")

    _coach_bubble(f"""
    🎉 <b>Super gedaan, {naam}!</b> Hier is jouw <b>volledig gepersonaliseerd race nutrition plan</b>. 
    Bewaar dit goed en volg het stap voor stap!
    """, "🏆")

    st.markdown("""
    <div style="background:#1e293b; border-radius:16px; padding:20px; margin-bottom:20px; border-top:4px solid #f97316;">
        <div style="font-weight:900; color:#f97316; font-size:0.85rem; letter-spacing:2px; margin-bottom:14px;">📋 JOUW PLAN OVERZICHT</div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    info_items = [
        (c1, "Atleet", naam, "#f97316"),
        (c2, "Sport", f"{SPORT_ICONS.get(data.get('sport',''), '🏅')} {data.get('sport','—')}", "#3b82f6"),
        (c3, "Wedstrijd", data.get("wedstrijd_datum","—"), "#22c55e"),
        (c4, "Duur", f"{data.get('totale_min',0)//60}u{data.get('totale_min',0)%60:02d}m", "#8b5cf6"),
    ]
    for col, lbl, val, color in info_items:
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:10px; background:#0f172a; border-radius:10px; border-top:3px solid {color};">
                <div style="font-size:0.62rem; color:#64748b; font-weight:700; letter-spacing:1px;">{lbl.upper()}</div>
                <div style="font-size:0.95rem; font-weight:800; color:#f8fafc; margin-top:4px;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    tab_cl, tab_race, tab_plan = st.tabs(["🍝  CARBOLOADING", "🌅  RACEDAG", "⏱️  RACEPLAN"])

    with tab_cl:
        factor = data.get("factor", 8)
        dag_target = data.get("dag_target", 0)
        cl_data = data.get("carboloading", {})

        st.markdown(f"""
        <div style="background:rgba(249,115,22,0.1); border:1px solid #f97316; padding:14px; 
             border-radius:10px; margin-bottom:16px; text-align:center; color:#fb923c; font-weight:700;">
            📊 Protocol: {factor}g KH/kg/dag &nbsp;|&nbsp; 
            🎯 Dagdoel: {dag_target}g KH &nbsp;|&nbsp;
            ⚖️ Gewicht: {data.get("gewicht",70)}kg
        </div>
        """, unsafe_allow_html=True)

        for dag_key in ["dag1", "dag2"]:
            dag_info = cl_data.get(dag_key, {})
            totaal = dag_info.get("totaal", 0)
            pct = dag_info.get("pct", 0)
            bar_c = "#22c55e" if pct >= 90 else ("#fbbf24" if pct >= 70 else "#ef4444")
            dag_num = dag_key[-1]
            dag_label = "2 dagen voor race" if dag_num == "1" else "1 dag voor race"

            st.markdown(f"""
            <div style="background:#0f172a; border-radius:12px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="font-weight:800; color:#f8fafc;">DAG {dag_num} — {dag_label}</div>
                    <div style="font-weight:700; color:{bar_c};">{totaal}g / {dag_target}g</div>
                </div>
                <div style="background:#334155; border-radius:6px; height:8px;">
                    <div style="width:{min(pct,100)}%; height:100%; background:{bar_c}; border-radius:6px;"></div>
                </div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">{pct}% van dagtarget</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:16px;">
            <div style="font-weight:800; color:#f97316; margin-bottom:10px; font-size:0.85rem;">💡 CARBOLOADING TIPS</div>
        """, unsafe_allow_html=True)
        tips_cl = [
            "🍚 Kies witte pasta, rijst en wit brood — minder vezels = minder maagklachten",
            "🍌 Bananen, dadelstroop en sportdranken zijn snelle koolhydraatbronnen",
            "🥩 Beperk eiwitten en vetten de laatste dag niet, maar geef koolhydraten prioriteit",
            "💧 Drink voldoende water — koolhydraten binden vocht (3g water per 1g KH)",
            "🚫 Vermijd nieuwe, onbekende voedingsmiddelen de dag voor de race",
        ]
        for tip in tips_cl:
            st.markdown(f'<div style="background:#1e293b; border-radius:8px; padding:10px 14px; margin-bottom:6px; font-size:0.82rem; color:#f8fafc;">{tip}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_race:
        ontbijt_tijd = data.get("ontbijt_tijd", "—")
        start_time = data.get("start_time", "—")
        ontbijt_kh = data.get("ontbijt_kh", 0)
        pre_totaal = data.get("pre_totaal_kh", 0)

        st.markdown(f"""
        <div style="background:#0f172a; border-radius:14px; padding:20px; margin-bottom:16px;">
            <div style="font-weight:900; color:#22c55e; margin-bottom:14px; font-size:0.85rem; letter-spacing:1px;">⏰ RACEDAGTIJDLIJN</div>
        """, unsafe_allow_html=True)

        tijdlijn = [
            (ontbijt_tijd, "🍳 ONTBIJT", f"{ontbijt_kh}g KH — licht verteerbaar, geen nieuwe producten", "#f97316"),
            ("30-60 min voor", "⚡ PRE-RACE", f"{'Gel + ' if data.get('pre_gel') else ''}{'Sportdrank + ' if data.get('sportdrank_ont') else ''}{'Koffie' if data.get('koffie') else 'Alleen water'}", "#3b82f6"),
            (start_time, "🏁 START", f"Totaal {pre_totaal}g KH geconsumeerd voor de start", "#22c55e"),
        ]
        for tijd, event, beschr, color in tijdlijn:
            st.markdown(f"""
            <div style="display:flex; gap:14px; margin-bottom:12px; align-items:flex-start;">
                <div style="background:{color}22; color:{color}; padding:4px 10px; border-radius:6px; 
                     font-size:0.7rem; font-weight:800; white-space:nowrap; min-width:80px; text-align:center; margin-top:2px;">{tijd}</div>
                <div>
                    <div style="font-weight:800; color:#f8fafc; font-size:0.85rem;">{event}</div>
                    <div style="color:#94a3b8; font-size:0.8rem; margin-top:2px;">{beschr}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        cafe_strat = data.get("cafeine_strategie", "—")
        st.markdown(f"""
        <div style="background:#fef3c7; border-left:4px solid #f59e0b; padding:12px 16px; 
             border-radius:8px; color:#92400e; font-size:0.85rem;">
            ☕ <b>Cafeïne strategie:</b> {cafe_strat}
        </div>
        """, unsafe_allow_html=True)

    with tab_plan:
        pool = data.get("pool", {})
        totale_min = data.get("totale_min", 180)
        min_kh = data.get("min_kh", 60)
        max_kh = data.get("max_kh", 90)
        temp = data.get("temp", 18)
        hoogte = data.get("hoogte", 0)
        vochtigheid = data.get("vochtigheid", 50)
        start_dt = datetime.strptime(data.get("start_time", "09:00"), "%H:%M")
        aantal_uren = math.ceil(totale_min / 60)

        if not any(len(pool.get(k, [])) > 0 for k in ["drank", "gels", "vast", "cafe"]):
            st.markdown("""
            <div style="background:#fef2f2; border-left:4px solid #ef4444; padding:14px; 
                 border-radius:8px; color:#991b1b;">
                ⚠️ Geen producten ingevoerd. Ga terug naar stap 5 om je race-producten toe te voegen.
            </div>
            """, unsafe_allow_html=True)
        else:
            basis_vocht = 800 if temp > 25 else (600 if temp > 15 else 500)
            f_factor = (hoogte / 1000) * 0.15 + (0.15 if vochtigheid > 70 else 0)
            vocht_per_m = round(((basis_vocht * (1 + f_factor)) / 3) / 10) * 10

            if temp > 28 or (temp > 24 and vochtigheid > 75):
                st.markdown('<div class="alert-red">⚠️ <b>ORS NODIG:</b> Hitte + vochtigheid. Gebruik ORS voor zoutbalans.</div>', unsafe_allow_html=True)

            vast_idx = 0
            cafeine_gebruikt = False

            for u in range(aantal_uren):
                is_last = (u == aantal_uren - 1)
                cur_min_kh = round(min_kh * 0.6) if is_last else min_kh
                cur_max_kh = round(max_kh * 0.6) if is_last else max_kh
                uur_kh = 0
                moment_items = {1: [], 2: [], 3: []}
                uur_start = start_dt + timedelta(hours=u)
                uur_label = uur_start.strftime("%H:%M")

                if pool.get("drank"):
                    d = pool["drank"][0]
                    kh_per_m = round((d["kh"] / 500) * vocht_per_m)
                    for m in [1, 2, 3]:
                        moment_items[m].append({"label": f"🥤 {vocht_per_m}ml <b>{d['name']}</b> ({kh_per_m}g)", "kh": kh_per_m})
                        uur_kh += kh_per_m

                cafe_strat = data.get("cafeine_strategie", "")
                if u == 1 and not is_last and pool.get("cafe") and "uur 2" in cafe_strat:
                    c = pool["cafe"][0]
                    moment_items[1].append({"label": f"⚡ <b>{c['name']}</b> ({c['kh']}g)", "kh": c["kh"]})
                    uur_kh += c["kh"]
                    cafeine_gebruikt = True

                if "verspreid" in cafe_strat and not is_last and pool.get("cafe") and u % 2 == 1:
                    c = pool["cafe"][0]
                    moment_items[2].append({"label": f"⚡ <b>{c['name']}</b> ({c['kh']}g)", "kh": c["kh"]})
                    uur_kh += c["kh"]

                if pool.get("vast") and uur_kh < cur_min_kh:
                    item = pool["vast"][vast_idx % len(pool["vast"])]
                    moment_items[2].append({"label": f"🍱 <b>{item['name']}</b> ({item['kh']}g)", "kh": item["kh"]})
                    uur_kh += item["kh"]
                    vast_idx += 1

                if pool.get("gels") and uur_kh < cur_min_kh:
                    g = pool["gels"][0]
                    moment_items[3].append({"label": f"🧪 <b>{g['name']}</b> ({g['kh']}g)", "kh": g["kh"]})
                    uur_kh += g["kh"]

                status_color = "#22c55e" if uur_kh >= cur_min_kh else "#f59e0b"
                rows_html = ""
                for m_num in [1, 2, 3]:
                    min_label = f"+{m_num * 20}min"
                    if is_last and m_num > 1:
                        item_text = '<span style="color:#94a3b8;">Enkel spoelen / water.</span>'
                    elif moment_items[m_num]:
                        item_text = " + ".join(i["label"] for i in moment_items[m_num])
                    else:
                        item_text = f"🥤 {vocht_per_m}ml water"

                    rows_html += f"""
                    <div style="display:flex; gap:10px; margin-bottom:8px; font-size:0.83rem;">
                        <span style="color:#3b82f6; font-weight:700; min-width:55px;">{min_label}</span>
                        <span style="color:#1e293b;">{item_text}</span>
                    </div>"""

                st.markdown(f"""
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; color:#1e293b;">
                    <div style="display:flex; justify-content:space-between; font-weight:900; font-size:0.92rem; 
                         border-bottom:2px solid #3b82f6; padding-bottom:6px; margin-bottom:10px;">
                        <span>UUR {u+1} — ⏰ {uur_label}</span>
                        <span style="font-size:0.72rem; color:#64748b;">Doel: {cur_min_kh}–{cur_max_kh}g KH</span>
                    </div>
                    {rows_html}
                    <div style="text-align:right; font-weight:700; color:{status_color}; font-size:0.8rem; 
                         padding-top:8px; border-top:1px dashed #cbd5e1; margin-top:4px;">
                        TOTAAL: {round(uur_kh)}g KH &nbsp;|&nbsp; DOEL: {cur_min_kh}–{cur_max_kh}g
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:14px; text-align:center;">
                <div style="color:#94a3b8; font-size:0.82rem;">
                    💧 Vocht/moment: <b style="color:white;">{vocht_per_m}ml</b> &nbsp;|&nbsp;
                    🌡️ {temp}°C &nbsp;|&nbsp;
                    💦 {vochtigheid}% vochtigheid &nbsp;|&nbsp;
                    ⛰️ {hoogte}m
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # ── PDF Download knop ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('''
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid #334155;
         border-radius:16px;padding:20px 24px;text-align:center;margin-bottom:16px;">
        <div style="font-size:1.5rem;margin-bottom:8px;">📄</div>
        <div style="font-weight:900;color:#f8fafc;font-size:1rem;margin-bottom:6px;">
            Genereer jouw PDF Race Nutrition Plan
        </div>
        <div style="color:#64748b;font-size:0.82rem;">
            Alle keuzes, richtlijnen en wetenschappelijke adviezen in één overzichtelijk rapport.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    try:
        gebruiker_naam = st.session_state.get("current_user", {}).get("name", "Atleet")
        pdf_bytes    = _genereer_pdf(data, gebruiker_naam)
        atleet       = data.get("atleet_naam", gebruiker_naam).replace(" ", "_")
        wedstrijd    = data.get("wedstrijd_naam", "race").replace(" ", "_")
        bestandsnaam = f"Carboo_RacePlan_{atleet}_{wedstrijd}.pdf"
        st.download_button(
            label="📄  GENEREER PLAN (PDF)",
            data=pdf_bytes,
            file_name=bestandsnaam,
            mime="application/pdf",
            use_container_width=True,
            key="sum_pdf_download"
        )
    except Exception as e:
        st.error(f"Fout bij genereren PDF: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Terug naar raceplan", key="sum_prev"):
            st.session_state.coach_stap = 5
            st.rerun()
    with col2:
        if st.button("🔄 Nieuw plan starten", key="sum_new"):
            for k in list(st.session_state.keys()):
                if k.startswith("cl_") or k.startswith("rp_") or k.startswith("rd_") or k.startswith("p_") or k.startswith("w_"):
                    del st.session_state[k]
            st.session_state.coach_stap = 0
            st.session_state.coach_data = {}
            st.rerun()
    with col3:
        if st.button("🏠 Terug naar menu", key="sum_menu"):
            st.session_state.module = "menu"
            st.rerun()


# ─── MAIN RENDER ─────────────────────────────────────────────────────────────

def render_coach(user: dict):
    naam = user.get("name", "Atleet")

    if "coach_stap" not in st.session_state:
        st.session_state.coach_stap = 0
    if "coach_data" not in st.session_state:
        st.session_state.coach_data = {}

    stap = st.session_state.coach_stap
    stap_idx = min(stap, len(STAPPEN) - 1)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:16px; padding:18px 22px; 
         margin-bottom:20px; border-left:5px solid #f97316; display:flex; justify-content:space-between;">
        <div>
            <div style="font-size:0.68rem; color:#f97316; font-weight:800; letter-spacing:2px;">CARBOO COACH</div>
            <div style="font-size:1.1rem; font-weight:900; color:#f8fafc; margin-top:2px;">
                {STAPPEN[stap_idx].replace("_"," ").upper()}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.68rem; color:#64748b;">Gebruiker</div>
            <div style="font-size:0.9rem; font-weight:700; color:#f8fafc;">{naam}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _progress_bar(stap_idx)

    if stap == 0:
        _stap_welkom(naam)
    elif stap == 1:
        _stap_profiel(naam)
    elif stap == 2:
        _stap_wedstrijd()
    elif stap == 3:
        _stap_carboloading()
    elif stap == 4:
        _stap_racedag()
    elif stap == 5:
        _stap_raceplan()
    elif stap == 6:
        _stap_samenvatting()
