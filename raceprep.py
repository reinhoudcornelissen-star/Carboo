import streamlit as st
from datetime import datetime, timedelta
import math


SPORTS = {
    "fietsen":      ("🚴", "Fietsen"),
    "lopen":        ("🏃", "Lopen"),
    "duatlon":      ("🏃🚴", "Duatlon"),
    "triatlon":     ("🏊🚴", "Triatlon"),
    "crosstriatlon":("🚵", "Crosstriatlon"),
}

KH_TARGETS = {
    "fietsen":  {(0,75): (0,0), (75,120): (30,60), (120,180): (60,90), (180,9999): (85,110)},
    "lopen":    {(0,60): (0,0), (60,90):  (30,60), (90,180):  (60,90), (180,9999): (75,90)},
    "duatlon":  {(0,60): (0,0), (60,120): (30,60), (120,9999):(60,90)},
    "triatlon": {(0,90): (0,0), (90,180): (60,90), (180,9999):(80,110)},
    "crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}


def _get_kh_range(sport: str, minuten: int):
    ranges = KH_TARGETS.get(sport, KH_TARGETS["fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= minuten < hi:
            return mn, mx
    return 60, 90


def render_raceprep():
    st.markdown('<div class="section-title">🏁 RACEPREP PRO — Slim Raceplan</div>', unsafe_allow_html=True)

    # ─── SPORT + BASISINPUTS ───────────────────────────────────────────────
    sport_keys   = list(SPORTS.keys())
    sport_labels = [f"{v[0]} {v[1]}" for v in SPORTS.values()]
    sport_sel    = st.selectbox("Discipline", sport_labels, index=0)
    sport        = sport_keys[sport_labels.index(sport_sel)]

    col1, col2, col3 = st.columns(3)
    with col1:
        start_time = st.time_input("Starttijd", value=datetime.strptime("09:00", "%H:%M").time())
    with col2:
        eind_time  = st.time_input("Geschatte eindtijd", value=datetime.strptime("12:00", "%H:%M").time())
    with col3:
        temp = st.number_input("Temperatuur °C", value=18, min_value=-10, max_value=50)

    col4, col5 = st.columns(2)
    with col4:
        hoogte    = st.number_input("Hoogte (m)", value=0, min_value=0, max_value=5000)
    with col5:
        vochtigheid = st.number_input("Vochtigheid (%)", value=50, min_value=0, max_value=100)

    # Duur berekening
    start_dt = datetime.combine(datetime.today(), start_time)
    eind_dt  = datetime.combine(datetime.today(), eind_time)
    if eind_dt <= start_dt:
        eind_dt += timedelta(days=1)
    totale_min = int((eind_dt - start_dt).total_seconds() / 60)
    aantal_uren = math.ceil(totale_min / 60)

    min_kh, max_kh = _get_kh_range(sport, totale_min)

    st.markdown(f"""
    <div style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; padding:14px; 
         border-radius:10px; margin: 10px 0 20px 0; text-align:center; color:#93c5fd; font-weight:700;">
        ⏱ Duur: {totale_min // 60}u{totale_min % 60:02d}m &nbsp;|&nbsp; 
        🎯 KH-target: {min_kh}–{max_kh}g/uur &nbsp;|&nbsp; 
        📊 {aantal_uren} uur te plannen
    </div>
    """, unsafe_allow_html=True)

    # ─── PRODUCTEN INVOER ─────────────────────────────────────────────────
    st.markdown("<div style='font-weight:800; color:#3b82f6; margin-bottom:12px;'>🛒 Producten die je gaat gebruiken</div>", unsafe_allow_html=True)

    pcol1, pcol2 = st.columns(2)

    with pcol1:
        st.markdown("<div style='color:#3b82f6; font-weight:700; font-size:0.85rem; margin-bottom:8px;'>🥤 SPORTDRANK (per 500ml)</div>", unsafe_allow_html=True)
        n_drank = st.number_input("Aantal sportdranken toevoegen", 0, 5, 1, key="n_drank", label_visibility="collapsed")
        drank_pool = []
        for i in range(int(n_drank)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam drank {i+1}", key=f"drank_naam_{i}", placeholder="bijv. Maurten 320")
            with c2: kh   = st.number_input("KH/500ml", key=f"drank_kh_{i}", min_value=0, value=70)
            if naam:
                drank_pool.append({"name": naam, "kh": kh, "type": "drank"})

        st.markdown("<div style='color:#10b981; font-weight:700; font-size:0.85rem; margin:12px 0 8px 0;'>🍱 VASTE VOEDING</div>", unsafe_allow_html=True)
        n_vast = st.number_input("Vast voedsel", 0, 5, 0, key="n_vast", label_visibility="collapsed")
        vast_pool = []
        for i in range(int(n_vast)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam vast {i+1}", key=f"vast_naam_{i}", placeholder="bijv. Banaan")
            with c2: kh   = st.number_input("KH", key=f"vast_kh_{i}", min_value=0, value=25)
            if naam:
                vast_pool.append({"name": naam, "kh": kh, "type": "vast"})

    with pcol2:
        st.markdown("<div style='color:#60a5fa; font-weight:700; font-size:0.85rem; margin-bottom:8px;'>🧪 ENERGY GELS</div>", unsafe_allow_html=True)
        n_gels = st.number_input("Gels", 0, 5, 1, key="n_gels", label_visibility="collapsed")
        gels_pool = []
        for i in range(int(n_gels)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam gel {i+1}", key=f"gel_naam_{i}", placeholder="bijv. SIS Go Gel")
            with c2: kh   = st.number_input("KH", key=f"gel_kh_{i}", min_value=0, value=22)
            if naam:
                gels_pool.append({"name": naam, "kh": kh, "type": "gels"})

        st.markdown("<div style='color:#f59e0b; font-weight:700; font-size:0.85rem; margin:12px 0 8px 0;'>⚡ GELS + CAFEÏNE</div>", unsafe_allow_html=True)
        n_cafe = st.number_input("Cafeïne gels", 0, 5, 0, key="n_cafe", label_visibility="collapsed")
        cafe_pool = []
        for i in range(int(n_cafe)):
            c1, c2 = st.columns([2,1])
            with c1: naam = st.text_input(f"Naam caf {i+1}", key=f"cafe_naam_{i}", placeholder="bijv. Caffeine Gel")
            with c2: kh   = st.number_input("KH", key=f"cafe_kh_{i}", min_value=0, value=25)
            if naam:
                cafe_pool.append({"name": naam, "kh": kh, "type": "cafe"})

    pool = {
        "drank": sorted(drank_pool, key=lambda x: x["kh"], reverse=True),
        "gels":  sorted(gels_pool,  key=lambda x: x["kh"], reverse=True),
        "cafe":  cafe_pool,
        "vast":  vast_pool,
    }

    # ─── GENERATE ─────────────────────────────────────────────────────────
    if st.button("🚀  GENEREER SLIM RACEPLAN", key="gen_race"):
        _render_race_plan(
            pool, start_dt, totale_min, aantal_uren,
            min_kh, max_kh, temp, hoogte, vochtigheid, sport
        )


def _render_race_plan(pool, start_dt, totale_min, aantal_uren,
                      min_kh, max_kh, temp, hoogte, vochtigheid, sport):

    st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#1e293b; padding:20px; border-radius:16px; text-align:center; margin-bottom:20px;">
        <div style="font-size:1.4rem; font-weight:900; color:#3b82f6; letter-spacing:3px;">SLIM RACEPLAN</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── MELDINGEN ────────────────────────────────────────────────────────
    if temp > 28 or (temp > 24 and vochtigheid > 75):
        st.markdown('<div class="alert-red">⚠️ <b>ORS NODIG:</b> Hitte/vochtigheid te hoog. Gebruik ORS voor zoutbalans.</div>', unsafe_allow_html=True)

    has_fuel = any(len(pool[k]) > 0 for k in ["gels", "vast"])
    if totale_min > 120 and len(pool["drank"]) > 0 and not has_fuel:
        st.markdown('<div class="alert-orange">⚠️ <b>COMBINEER:</b> Bij ritten langer dan 2u is enkel sportdrank onvoldoende. Voeg gels of vast voedsel toe.</div>', unsafe_allow_html=True)

    if totale_min >= 300 and len(pool["vast"]) == 0:
        st.markdown('<div class="alert-orange">⚠️ <b>VASTE VOEDING:</b> Bij +5u is vaste voeding cruciaal voor de maag.</div>', unsafe_allow_html=True)

    # Vocht berekening
    basis_vocht = 800 if temp > 25 else (600 if temp > 15 else 500)
    f_factor    = (hoogte / 1000) * 0.15 + (0.15 if vochtigheid > 70 else 0)
    vocht_per_m = round(((basis_vocht * (1 + f_factor)) / 3) / 10) * 10  # per 20-min moment

    # PRE-START
    st.markdown("""
    <div style="background:#f1f5f9; padding:15px; border-radius:14px; margin-bottom:15px; border:2px dashed #3b82f6;">
        <div style="font-weight:900; color:#3b82f6; margin-bottom:5px;">🏁 PRE-START</div>
        <div style="font-size:0.85rem; color:#334155;">Kleine slokjes vocht + optionele gel 15min voor start.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sprint protocol
    if totale_min < 75 and sport == "fietsen":
        st.markdown("""
        <div style="background:#eff6ff; padding:20px; border-radius:14px; border-left:5px solid #3b82f6; color:#1e3a8a;">
            <h3 style="margin:0;">⚡ SPRINT PROTOCOL</h3>
            <p style="font-size:0.85rem; margin-top:8px;">Mondspoeling + kleine slokjes water naar behoefte. Geen supplementen nodig.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ─── UUR-PER-UUR PLANNING ─────────────────────────────────────────────
    vast_idx = 0

    for u in range(aantal_uren):
        is_last    = (u == aantal_uren - 1)
        cur_min_kh = round(min_kh * 0.6) if is_last else min_kh
        cur_max_kh = round(max_kh * 0.6) if is_last else max_kh
        uur_kh     = 0

        moment_items = {1: [], 2: [], 3: []}
        uur_start    = start_dt + timedelta(hours=u)
        uur_label    = uur_start.strftime("%H:%M")

        # A. Sportdrank (alle 3 momenten)
        if pool["drank"]:
            d = pool["drank"][0]
            kh_per_m = round((d["kh"] / 500) * vocht_per_m)
            for m in [1, 2, 3]:
                moment_items[m].append({"label": f"🥤 {vocht_per_m}ml <b>{d['name']}</b> ({kh_per_m}g)", "kh": kh_per_m})
                uur_kh += kh_per_m

        # B. Cafeïne (uur 2 + niet laatste uur)
        if u == 1 and not is_last and pool["cafe"]:
            c = pool["cafe"][0]
            moment_items[1].append({"label": f"⚡ <b>{c['name']}</b> ({c['kh']}g)", "kh": c["kh"]})
            uur_kh += c["kh"]

        # C. Vast voedsel
        if pool["vast"] and uur_kh < cur_min_kh:
            item = pool["vast"][vast_idx % len(pool["vast"])]
            moment_items[2].append({"label": f"🍱 <b>{item['name']}</b> ({item['kh']}g)", "kh": item["kh"]})
            uur_kh += item["kh"]
            vast_idx += 1

        # D. Gels aanvullen
        if pool["gels"] and uur_kh < cur_min_kh:
            g = pool["gels"][0]
            moment_items[3].append({"label": f"🧪 <b>{g['name']}</b> ({g['kh']}g)", "kh": g["kh"]})
            uur_kh += g["kh"]

        # Render uur-blok
        status_color = "#22c55e" if uur_kh >= cur_min_kh else "#f59e0b"
        rows_html = ""
        for m_num in [1, 2, 3]:
            min_label = f"{m_num * 20} MIN"
            if is_last and m_num > 1:
                item_text = '<span style="color:#94a3b8;">Enkel spoelen / water.</span>'
            elif moment_items[m_num]:
                item_text = " + ".join(i["label"] for i in moment_items[m_num])
                if not any("🥤" in i["label"] for i in moment_items[m_num]):
                    item_text = f"🥤 {vocht_per_m}ml water + " + item_text
            else:
                item_text = f"🥤 {vocht_per_m}ml water"

            rows_html += f"""
            <div class="timeline-row">
                <span class="min-label">{min_label}</span>
                <span style="font-size:0.85rem; color:#1e293b;">{item_text}</span>
            </div>"""

        totaal_html = f'<div style="text-align:right; font-weight:700; color:{status_color}; font-size:0.8rem; padding-top:8px; border-top:1px dashed #cbd5e1; margin-top:8px;">TOTAAL: {round(uur_kh)}g KH &nbsp;|&nbsp; DOEL: {cur_min_kh}–{cur_max_kh}g</div>'

        st.markdown(f"""
        <div class="timeline-block">
            <div class="timeline-uur">
                <span>UUR {u+1} — ⏰ {uur_label}</span>
                <span style="font-size:0.7rem; color:#64748b;">Doel: {cur_min_kh}–{cur_max_kh}g KH</span>
            </div>
            {rows_html}
            {totaal_html}
        </div>
        """, unsafe_allow_html=True)

    # ─── EINDSAMENVATTING ────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:#1e293b; border-radius:12px; padding:16px; text-align:center; margin-top:10px;">
        <div style="color:#94a3b8; font-size:0.85rem;">
            💧 Vocht per moment: <b style="color:white;">{vocht_per_m}ml</b> &nbsp;|&nbsp;
            🌡️ Temp: <b style="color:white;">{temp}°C</b> &nbsp;|&nbsp;
            📏 Hoogte: <b style="color:white;">{hoogte}m</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
