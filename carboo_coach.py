import streamlit as st
import math
from datetime import datetime, timedelta

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
    "Fietsen": "🚴",
    "Lopen": "🏃",
    "Duatlon": "🏃🚴",
    "Triatlon": "🏊🚴",
    "Crosstriatlon": "🚵",
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
    st.markdown(f"""
    <div style="display:flex; gap:12px; margin-bottom:20px; align-items:flex-start;">
        <div style="background:#f97316; border-radius:50%; width:42px; height:42px; display:flex; align-items:center; 
             justify-content:center; font-size:1.2rem; flex-shrink:0; margin-top:2px;">{icon}</div>
        <div style="background:#1e293b; border:1px solid #334155; border-radius:0 14px 14px 14px; 
             padding:14px 18px; color:#f8fafc; font-size:0.9rem; line-height:1.6; max-width:680px;">
            {tekst}
        </div>
    </div>
    """, unsafe_allow_html=True)


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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀  JA, LET'S GO!", key="welkom_ja", use_container_width=True):
            st.session_state.coach_stap = 1
            st.rerun()
    with col2:
        if st.button("📋  Bekijk eerder plan", key="welkom_plan", use_container_width=True):
            if st.session_state.get("coach_data"):
                st.session_state.coach_stap = 6
                st.rerun()
            else:
                st.info("Nog geen eerder plan gevonden. Start een nieuw plan!")


def _stap_profiel(naam: str):
    _coach_bubble(f"""
    Laten we starten met jouw <b>atleetprofiel</b>. Dit helpt me om je koolhydraatbehoeften 
    nauwkeurig te berekenen. Vul de gegevens zo nauwkeurig mogelijk in.
    """)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            gewicht = st.number_input("⚖️ Lichaamsgewicht (kg)", 30.0, 150.0,
                st.session_state.get("coach_data", {}).get("gewicht", 70.0), 0.5, key="p_gewicht")
        with col2:
            sport_list = list(SPORT_ICONS.keys())
            sport_default = st.session_state.get("coach_data", {}).get("sport", "Fietsen")
            sport_idx = sport_list.index(sport_default) if sport_default in sport_list else 0
            sport = st.selectbox("🏅 Discipline",
                [f"{SPORT_ICONS[s]} {s}" for s in sport_list],
                index=sport_idx, key="p_sport")
            sport_clean = sport.split(" ", 1)[1] if " " in sport else sport

        niveau_list = ["Recreatief", "Amateurs competitie", "Gevorderd", "Elite / Semi-pro"]
        niveau_default = st.session_state.get("coach_data", {}).get("niveau", "Recreatief")
        niveau_idx = niveau_list.index(niveau_default) if niveau_default in niveau_list else 0
        niveau = st.selectbox("📊 Sportniveau", niveau_list, index=niveau_idx, key="p_niveau")

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
                "gewicht": gewicht,
                "sport": sport_clean,
                "niveau": niveau,
                "ervaring": ervaring,
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
            value=datetime.strptime(data.get("start_time", "09:00"), "%H:%M").time(), key="w_start")
    with col3:
        eind_time = st.time_input("🏁 Geschatte eindtijd",
            value=datetime.strptime(data.get("eind_time", "12:00"), "%H:%M").time(), key="w_eind")

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
        ⏱ Duur: {totale_min // 60}u{totale_min % 60:02d}m &nbsp;|&nbsp; 
        🎯 KH-target tijdens race: <b>{min_kh}–{max_kh}g/uur</b> &nbsp;|&nbsp;
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
    data = st.session_state.get("coach_data", {})
    gewicht = data.get("gewicht", 70)
    totale_min = data.get("totale_min", 180)

    if totale_min > 300:
        factor = 12
    elif totale_min > 180:
        factor = 10
    elif totale_min > 90:
        factor = 8
    else:
        factor = 6

    dag_target = round(gewicht * factor)

    _coach_bubble(f"""
    Op basis van jouw gewicht van <b>{gewicht}kg</b> en een wedstrijdduur van 
    <b>{totale_min // 60}u{totale_min % 60:02d}min</b> is het <b>carbohydrate loading protocol</b>:<br><br>
    📊 Factor: <b>{factor}g koolhydraten per kg lichaamsgewicht</b><br>
    🎯 Dagdoelstelling: <b style="color:#f97316; font-size:1.1rem;">{dag_target}g koolhydraten/dag</b><br><br>
    Vul hieronder in welke maaltijden je de komende 2 dagen plant. 
    Ik bereken dan automatisch of je jouw doel haalt.
    """)

    st.markdown("""
    <div style="background:rgba(249,115,22,0.08); border:1px solid #f97316; padding:12px 16px; 
         border-radius:10px; margin-bottom:20px; font-size:0.82rem; color:#fb923c;">
        💡 <b>Tip:</b> Focus op rijst, pasta, brood, aardappelen en sportdranken. Beperk vetten en vezels 
        de dag voor de race om maagproblemen te vermijden.
    </div>
    """, unsafe_allow_html=True)

    MAALTIJDEN = {
        "Ontbijt":       {"pct": 0.25,  "icon": "🌅"},
        "Tussendoor VM": {"pct": 0.083, "icon": "☕"},
        "Lunch":         {"pct": 0.25,  "icon": "🍽️"},
        "Tussendoor NM": {"pct": 0.083, "icon": "🍎"},
        "Avondmaal":     {"pct": 0.25,  "icon": "🌙"},
        "Avond snack":   {"pct": 0.083, "icon": "🍌"},
    }

    tab1, tab2 = st.tabs(["📅  DAG 1 (2 dagen voor)", "📅  DAG 2 (dag voor race)"])
    dag_totalen = {}

    for dag_idx, tab in enumerate([tab1, tab2], start=1):
        with tab:
            dag_kh = 0
            col1, col2 = st.columns(2)
            maaltijd_list = list(MAALTIJDEN.items())

            for col_idx, col in enumerate([col1, col2]):
                with col:
                    for m_name, m_cfg in maaltijd_list[col_idx*3:(col_idx+1)*3]:
                        m_target = round(dag_target * m_cfg["pct"])
                        st.markdown(f"""
                        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:10px; 
                             padding:14px; margin-bottom:12px; border-left:3px solid #f97316;">
                            <div style="color:#f97316; font-weight:800; font-size:0.78rem; margin-bottom:8px;">
                                {m_cfg['icon']} {m_name.upper()} — doel: {m_target}g KH
                            </div>
                        """, unsafe_allow_html=True)

                        kh_val = st.number_input(
                            f"KH (gram) voor {m_name}",
                            min_value=0, max_value=500,
                            value=st.session_state.get(f"cl_d{dag_idx}_{m_name}", 0),
                            step=5, key=f"cl_d{dag_idx}_{m_name}",
                            label_visibility="collapsed"
                        )
                        dag_kh += kh_val

                        pct_m = min(100, round((kh_val / m_target) * 100)) if m_target > 0 else 0
                        bar_c = "#22c55e" if pct_m >= 90 else ("#fbbf24" if pct_m >= 60 else "#ef4444")
                        st.markdown(f"""
                        <div style="background:#1e293b; border-radius:4px; height:4px; margin-top:6px;">
                            <div style="width:{pct_m}%; height:100%; background:{bar_c}; border-radius:4px;"></div>
                        </div>
                        <div style="font-size:0.65rem; color:#64748b; margin-top:3px;">{kh_val}g / {m_target}g ({pct_m}%)</div>
                        </div>
                        """, unsafe_allow_html=True)

            dag_pct = round((dag_kh / dag_target) * 100) if dag_target > 0 else 0
            bar_color = "#22c55e" if dag_pct >= 90 else ("#fbbf24" if dag_pct >= 70 else "#ef4444")
            status_msg = "✅ Doel bereikt!" if dag_pct >= 90 else ("⚠️ Bijna!" if dag_pct >= 70 else "❌ Te laag")

            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:16px; text-align:center; margin-top:8px;">
                <div style="font-weight:900; font-size:1rem; color:#f8fafc; margin-bottom:8px;">
                    TOTAAL DAG {dag_idx}: {dag_kh}g / {dag_target}g &nbsp; {status_msg}
                </div>
                <div style="background:#334155; border-radius:8px; height:12px; overflow:hidden;">
                    <div style="width:{min(dag_pct,100)}%; height:100%; background:{bar_color}; border-radius:8px;"></div>
                </div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:6px;">{dag_pct}% van dagtarget bereikt</div>
            </div>
            """, unsafe_allow_html=True)
            dag_totalen[f"dag{dag_idx}"] = {"totaal": dag_kh, "target": dag_target, "pct": dag_pct}

    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="cl_prev"):
            # Sla huidige waarden op voor terugnavigatie
            cl_waarden = {}
            for dag_idx2 in [1, 2]:
                for m_name in MAALTIJDEN.keys():
                    ss_key = f"cl_d{dag_idx2}_{m_name}"
                    cl_waarden[ss_key] = st.session_state.get(ss_key, 0)
            st.session_state.coach_data["cl_waarden"] = cl_waarden
            st.session_state.coach_stap = 2
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="cl_next", use_container_width=True):
            # Sla huidige waarden op
            cl_waarden = {}
            for dag_idx2 in [1, 2]:
                for m_name in MAALTIJDEN.keys():
                    ss_key = f"cl_d{dag_idx2}_{m_name}"
                    cl_waarden[ss_key] = st.session_state.get(ss_key, 0)
            st.session_state.coach_data["cl_waarden"] = cl_waarden
            st.session_state.coach_data.update({
                "carboloading": dag_totalen,
                "dag_target": dag_target,
                "factor": factor,
            })
            st.session_state.coach_stap = 4
            st.rerun()

    # Herstel waarden na terugnavigatie
    if "cl_waarden" in st.session_state.get("coach_data", {}):
        for ss_key, val in st.session_state.coach_data["cl_waarden"].items():
            if ss_key not in st.session_state:
                st.session_state[ss_key] = val


def _stap_racedag():
    data = st.session_state.get("coach_data", {})
    start_time_str = data.get("start_time", "09:00")
    _coach_bubble(f"""
    Perfect! Nu plannen we jouw <b>racedagvoeding</b> — het ontbijt en de pre-race strategie 
    vóór de start om {start_time_str}.<br><br>
    Het doel is om met volle glycogeenvoorraden aan de start te staan, maar zonder 
    een volle of zwaar gevoel in de maag.
    """)

    start_dt = datetime.strptime(start_time_str, "%H:%M")

    onbijt_tips = {
        "3-4 uur voor start (aanbevolen)": -210,
        "2-3 uur voor start": -150,
        "1-2 uur voor start (licht)": -90,
    }
    ontbijt_keuze = st.selectbox("⏰ Wanneer eet je ontbijt?", list(onbijt_tips.keys()), key="rd_ontbijt_timing")
    offset = onbijt_tips[ontbijt_keuze]
    ontbijt_tijd = (start_dt + timedelta(minutes=offset)).strftime("%H:%M")

    st.markdown(f"""
    <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e; padding:10px 14px; 
         border-radius:8px; margin-bottom:16px; color:#86efac; font-size:0.85rem;">
        ✅ Ontbijt om: <b>{ontbijt_tijd}</b> &nbsp;|&nbsp; Start om: <b>{start_time_str}</b>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='color:#3b82f6; font-weight:700; font-size:0.82rem; margin-bottom:8px;'>🍳 ONTBIJT KOOLHYDRATEN</div>", unsafe_allow_html=True)
        ontbijt_kh = st.number_input("KH (gram)", 0, 300,
            data.get("ontbijt_kh", 100), 10, key="rd_ontkh",
            help="Doel: 1-3g KH/kg. Kies licht verteerbaar: rijst, wit brood, havermout, banaan.")

        st.markdown("<div style='color:#22c55e; font-weight:700; font-size:0.82rem; margin:12px 0 8px 0;'>☕ DRANKEN ONTBIJT</div>", unsafe_allow_html=True)
        koffie = st.checkbox("Koffie (cafeïne ~95mg)", value=data.get("koffie", True), key="rd_koffie")
        sportdrank_ont = st.checkbox("Sportdrank 500ml (+35g KH)", value=data.get("sportdrank_ont", False), key="rd_sdont")

    with col2:
        st.markdown("<div style='color:#f97316; font-weight:700; font-size:0.82rem; margin-bottom:8px;'>⚡ PRE-RACE (30-60min voor start)</div>", unsafe_allow_html=True)
        pre_gel = st.checkbox("Pre-race gel (+22-25g KH)", value=data.get("pre_gel", True), key="rd_pregel")
        pre_kh_extra = st.number_input("Extra KH pre-race (g)", 0, 100,
            data.get("pre_kh_extra", 0), 5, key="rd_prekh",
            help="Bijv. rijstwafels, banaan of sportdrank")

        st.markdown("<div style='color:#8b5cf6; font-weight:700; font-size:0.82rem; margin:12px 0 8px 0;'>💊 SUPPLEMENTEN</div>", unsafe_allow_html=True)
        cafeine_timing = st.selectbox("Cafeïne strategie", [
            "Geen cafeïne",
            "Enkel koffie ontbijt",
            "Koffie + gel met cafeïne (uur 2)",
            "Meerdere cafeïne gels verspreid",
        ], index=data.get("cafeine_idx", 1), key="rd_cafe_strat")

    pre_totaal = ontbijt_kh + (35 if sportdrank_ont else 0) + (23 if pre_gel else 0) + pre_kh_extra
    gewicht = data.get("gewicht", 70)
    ideaal_min = round(gewicht * 1)
    ideaal_max = round(gewicht * 3)
    status = "✅ Goed!" if ideaal_min <= pre_totaal <= ideaal_max else ("⚠️ Mogelijk te veel" if pre_totaal > ideaal_max else "❌ Te weinig")

    st.markdown(f"""
    <div style="background:#1e293b; border-radius:12px; padding:16px; margin:16px 0; text-align:center;">
        <div style="color:#94a3b8; font-size:0.78rem; margin-bottom:4px;">TOTAAL KH VOOR DE START</div>
        <div style="font-size:1.5rem; font-weight:900; color:#f97316;">{pre_totaal}g</div>
        <div style="font-size:0.82rem; color:#64748b; margin-top:4px;">Ideaal: {ideaal_min}–{ideaal_max}g &nbsp; {status}</div>
    </div>
    """, unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="rd_prev"):
            st.session_state.coach_stap = 3
            st.rerun()
    with col_next:
        if st.button("Volgende →", key="rd_next", use_container_width=True):
            st.session_state.coach_data.update({
                "ontbijt_kh": ontbijt_kh,
                "ontbijt_timing": ontbijt_keuze,
                "ontbijt_tijd": ontbijt_tijd,
                "koffie": koffie,
                "sportdrank_ont": sportdrank_ont,
                "pre_gel": pre_gel,
                "pre_kh_extra": pre_kh_extra,
                "cafeine_strategie": cafeine_timing,
                "cafeine_idx": [
                    "Geen cafeïne",
                    "Enkel koffie ontbijt",
                    "Koffie + gel met cafeïne (uur 2)",
                    "Meerdere cafeïne gels verspreid",
                ].index(cafeine_timing),
                "pre_totaal_kh": pre_totaal,
            })
            st.session_state.coach_stap = 5
            st.rerun()


def _stap_raceplan():
    data = st.session_state.get("coach_data", {})
    _coach_bubble(f"""
    Bijna klaar! Voeg nu de <b>producten toe die je tijdens de race</b> gaat gebruiken. 
    Op basis hiervan bouw ik een <b>uur-per-uur raceplan</b> met exacte hoeveelheden en timing.
    """)

    pcol1, pcol2 = st.columns(2)

    with pcol1:
        st.markdown("<div style='color:#3b82f6; font-weight:700; font-size:0.82rem; margin-bottom:8px;'>🥤 SPORTDRANK (per 500ml)</div>", unsafe_allow_html=True)
        n_drank = st.number_input("", 0, 5, 1, key="rp_n_drank", label_visibility="collapsed")
        drank_pool = []
        for i in range(int(n_drank)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam drank {i+1}", key=f"rp_drank_{i}", placeholder="bijv. Maurten 320")
            with c2: kh = st.number_input("KH/500ml", key=f"rp_dkh_{i}", min_value=0, value=70)
            if naam:
                drank_pool.append({"name": naam, "kh": kh, "type": "drank"})

        st.markdown("<div style='color:#10b981; font-weight:700; font-size:0.82rem; margin:12px 0 8px 0;'>🍱 VASTE VOEDING</div>", unsafe_allow_html=True)
        n_vast = st.number_input("", 0, 5, 0, key="rp_n_vast", label_visibility="collapsed")
        vast_pool = []
        for i in range(int(n_vast)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam vast {i+1}", key=f"rp_vast_{i}", placeholder="bijv. Banaan")
            with c2: kh = st.number_input("KH", key=f"rp_vkh_{i}", min_value=0, value=25)
            if naam:
                vast_pool.append({"name": naam, "kh": kh, "type": "vast"})

    with pcol2:
        st.markdown("<div style='color:#60a5fa; font-weight:700; font-size:0.82rem; margin-bottom:8px;'>🧪 ENERGY GELS</div>", unsafe_allow_html=True)
        n_gels = st.number_input("", 0, 5, 1, key="rp_n_gels", label_visibility="collapsed")
        gels_pool = []
        for i in range(int(n_gels)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam gel {i+1}", key=f"rp_gel_{i}", placeholder="bijv. SIS Go Gel")
            with c2: kh = st.number_input("KH", key=f"rp_gkh_{i}", min_value=0, value=22)
            if naam:
                gels_pool.append({"name": naam, "kh": kh, "type": "gels"})

        st.markdown("<div style='color:#f59e0b; font-weight:700; font-size:0.82rem; margin:12px 0 8px 0;'>⚡ GELS + CAFEÏNE</div>", unsafe_allow_html=True)
        n_cafe = st.number_input("", 0, 5, 0, key="rp_n_cafe", label_visibility="collapsed")
        cafe_pool = []
        for i in range(int(n_cafe)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam caf {i+1}", key=f"rp_cafe_{i}", placeholder="bijv. Caffeine Gel")
            with c2: kh = st.number_input("KH", key=f"rp_ckh_{i}", min_value=0, value=25)
            if naam:
                cafe_pool.append({"name": naam, "kh": kh, "type": "cafe"})

    pool = {
        "drank": sorted(drank_pool, key=lambda x: x["kh"], reverse=True),
        "gels": sorted(gels_pool, key=lambda x: x["kh"], reverse=True),
        "cafe": cafe_pool,
        "vast": vast_pool,
    }

    col_prev, col_gen = st.columns(2)
    with col_prev:
        if st.button("← Vorige", key="rp_prev"):
            st.session_state.coach_stap = 4
            st.rerun()
    with col_gen:
        if st.button("✅  GENEREER VOLLEDIG PLAN", key="rp_gen", use_container_width=True):
            st.session_state.coach_data["pool"] = pool
            st.session_state.coach_stap = 6
            st.rerun()


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
            <div style="font-size:0.68rem; color:#64748b;">Atleet</div>
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
