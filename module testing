"""
Train the Gut — Carboo module voor systematische maagtraining
"""
import streamlit as st
from datetime import date, timedelta

SPORTEN = ["Fietsen", "Lopen", "Triatlon", "Duatlon", "Crosstriatlon"]
PRODUCT_TYPES = ["Gel", "Sportdrank", "Vast voedsel", "Cafeïnegel", "Supplement"]
SYMPTOMEN = [
    "Geen klachten", "Lichte maagkramp", "Misselijkheid",
    "Opgeblazen gevoel", "Reflux / brandend maagzuur",
    "Diarree", "Braken", "Hoofdpijn", "Steken in de zij",
]
INTENSITEITEN = [
    "Z1 — Actief herstel", "Z2 — Duurtraining", "Z3 — Tempo",
    "Z4 — Drempeltraining", "Z5 — Wedstrijdintensiteit",
]
SPORT_START_PCT = {
    "Fietsen": 0.40, "Lopen": 0.30, "Triatlon": 0.35,
    "Duatlon": 0.35, "Crosstriatlon": 0.35,
}
FASE_INTENSITEIT = {
    "opbouw": "Z2 — Duurtraining",
    "midden": "Z3 — Tempo",
    "finale": "Z4 — Drempeltraining",
}


def _sectie(titel, kleur="#f97316"):
    st.markdown(
        f'<div style="font-size:0.72rem;font-weight:700;color:{kleur};'
        f'letter-spacing:2px;margin:18px 0 8px;padding-bottom:4px;'
        f'border-bottom:1px solid #1e293b;">{titel}</div>',
        unsafe_allow_html=True)


def _score_kleur(score):
    if score >= 4.5: return "#22c55e"
    if score >= 3.5: return "#84cc16"
    if score >= 2.5: return "#fbbf24"
    if score >= 1.5: return "#f97316"
    return "#ef4444"


def _score_label(score):
    return {1:"Zeer slecht ❌",2:"Slecht ⚠️",3:"Matig 🟡",
            4:"Goed ✅",5:"Uitstekend 🌟"}.get(score,"—")


def _week_fase(w, totaal):
    pct = w / totaal
    if pct <= 0.33: return "opbouw"
    if pct <= 0.67: return "midden"
    return "finale"


def _week_tip(w, totaal, kh, sport):
    fase = _week_fase(w, totaal)
    tips = {
        "opbouw": [
            f"Start rustig — neem {kh}g KH/uur in tijdens een Z2 training.",
            "Test op een nuchtere maag of na een lichte maaltijd.",
            "Drink voldoende water bij elk product.",
        ],
        "midden": [
            f"Verhoog de intensiteit terwijl je {kh}g KH/uur inneemt.",
            "Let op maagklachten bij hogere snelheid.",
            "Combineer producten als je meerdere types test.",
        ],
        "finale": [
            f"Simuleer wedstrijdcondities met {kh}g KH/uur.",
            "Neem producten in op hetzelfde ritme als je raceplan.",
            "Test bij wedstrijdtemperatuur en -intensiteit.",
        ],
    }
    lst = tips.get(fase, [])
    return lst[w % len(lst)] if lst else ""


def _genereer_schema(data):
    weken     = data.get("weken", 6)
    target    = data.get("target_kh", 60)
    sport     = data.get("sport", "Fietsen")
    start     = date.fromisoformat(data.get("start_datum", str(date.today())))
    producten = [p for p in data.get("producten", []) if p.get("naam")]
    start_pct = SPORT_START_PCT.get(sport, 0.35)
    schema = []
    for w in range(1, weken + 1):
        week_datum = start + timedelta(weeks=w - 1)
        pct_kh = start_pct + (1 - start_pct) * ((w - 1) / max(weken - 1, 1))
        kh_doel = max(10, min(round(target * pct_kh / 5) * 5, target))
        fase = _week_fase(w, weken)
        prod = producten[(w - 1) % len(producten)] if producten else {"naam":"—","type":"Gel","kh":22,"ml":0}
        kh_pp = prod.get("kh", 22)
        porties = max(1, round(kh_doel / kh_pp)) if kh_pp > 0 else 1
        interval = max(10, round(60 / porties / 5) * 5)
        schema.append({
            "week": w, "datum": week_datum,
            "kh_doel": kh_doel, "pct": round(pct_kh * 100),
            "product": prod.get("naam","—"), "type": prod.get("type","Gel"),
            "kh_pp": kh_pp, "ml": prod.get("ml",0),
            "porties": porties, "interval": interval,
            "intensiteit": FASE_INTENSITEIT[fase], "fase": fase,
            "tip": _week_tip(w, weken, kh_doel, sport),
        })
    return schema


# ── Stap 1: Intro ─────────────────────────────────────────────────────────────
def _stap_intro():
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;
                padding:24px;margin-bottom:20px;">
        <div style="font-size:1rem;font-weight:800;color:#f8fafc;margin-bottom:10px;">
            Waarom maagtraining?</div>
        <div style="font-size:0.85rem;color:#94a3b8;line-height:1.8;">
            Tijdens intensieve inspanning vermindert de bloedtoevoer naar je maag.
            Dit maakt het moeilijker om voeding te verteren. Door systematisch te trainen
            went je maag aan grotere hoeveelheden koolhydraten — tot 90g of meer per uur.
            <br><br>
            Onderzoek toont aan dat atleten die hun maag trainen
            <b style="color:#f97316;">significant minder maagklachten</b>
            rapporteren op racedag.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, lbl, val in [
        (c1,"📅","Duur","4–8 weken"),
        (c2,"📈","Aanpak","Oplopende KH"),
        (c3,"🎯","Doel","90g/uur tolerantie"),
    ]:
        col.markdown(
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;'
            f'padding:14px;text-align:center;">'
            f'<div style="font-size:1.4rem;">{icon}</div>'
            f'<div style="font-size:10px;color:#64748b;margin:4px 0;">{lbl}</div>'
            f'<div style="font-weight:700;color:#f8fafc;font-size:0.85rem;">{val}</div>'
            f'</div>', unsafe_allow_html=True)

    _sectie("HOE WERKT HET?")
    for nr, naam, uitleg in [
        ("1","Profiel","Sport, duur en KH-target instellen"),
        ("2","Producten","Gels, sportdranken of vast voedsel toevoegen"),
        ("3","Schema","Automatisch testschema van 4-8 weken"),
        ("4","Logboek","Na elke training score en symptomen invullen"),
        ("5","Rapport","Welke producten werken voor jou op racedag"),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;'
            f'border-bottom:1px solid #1e293b;">'
            f'<div style="width:24px;height:24px;border-radius:50%;background:#f97316;'
            f'display:flex;align-items:center;justify-content:center;font-size:11px;'
            f'font-weight:700;color:white;flex-shrink:0;">{nr}</div>'
            f'<div><span style="font-weight:600;color:#f8fafc;">{naam}</span> '
            f'<span style="color:#64748b;font-size:0.82rem;">— {uitleg}</span></div>'
            f'</div>', unsafe_allow_html=True)


# ── Stap 2: Profiel ───────────────────────────────────────────────────────────
def _stap_profiel():
    _sectie("JOUW TRAININGSPROFIEL")
    data = st.session_state.get("tg_data", {})
    c1, c2 = st.columns(2)
    with c1:
        sport = st.selectbox("Sport", SPORTEN,
                              index=SPORTEN.index(data.get("sport","Fietsen")), key="tg_sport")
        weken = st.number_input("Testperiode (weken)", 4, 12, int(data.get("weken",6)), 1, key="tg_weken")
        target_kh = st.slider("KH-target op racedag (g/uur)", 30, 120, int(data.get("target_kh",60)), 5, key="tg_target")
    with c2:
        duur = st.number_input("Typische trainingsduur (min)", 45, 360, int(data.get("duur",90)), 15, key="tg_duur")
        start_datum = st.date_input("Startdatum", value=date.today(), key="tg_start")
        niveau = st.selectbox("Niveau", ["Recreatief","Competitief","Elite"],
                               index=["Recreatief","Competitief","Elite"].index(data.get("niveau","Recreatief")),
                               key="tg_niveau")

    start_kh = round(target_kh * SPORT_START_PCT.get(sport, 0.35) / 5) * 5
    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                padding:12px 14px;margin-top:10px;font-size:0.82rem;color:#94a3b8;">
        📋 Je begint op <b style="color:#f97316;">{start_kh}g/uur</b> en bouwt op naar
        <b style="color:#22c55e;">{target_kh}g/uur</b> over {weken} weken
        (+{round((target_kh-start_kh)/weken,1)}g per week).
    </div>
    """, unsafe_allow_html=True)

    if sport == "Lopen":
        st.markdown(
            '<div style="background:rgba(139,92,246,0.1);border:1px solid #8b5cf6;'
            'border-radius:8px;padding:10px 14px;font-size:0.8rem;color:#c4b5fd;margin-top:8px;">'
            '💡 Voor lopen wordt conservatiever gestart — de maag heeft meer moeite '
            'bij loopbewegingen.</div>', unsafe_allow_html=True)

    if st.button("Volgende →", key="tg_prof_next", use_container_width=True):
        st.session_state.tg_data = {
            "sport": sport, "weken": weken, "target_kh": target_kh,
            "duur": duur, "start_datum": str(start_datum), "niveau": niveau,
        }
        st.session_state.tg_stap = 3
        st.rerun()


# ── Stap 3: Producten ─────────────────────────────────────────────────────────
def _stap_producten():
    _sectie("TE TESTEN PRODUCTEN")
    data = st.session_state.get("tg_data", {})
    opgeslagen = data.get("producten", [{"naam":"","type":"Gel","kh":22,"ml":0}])
    n = st.session_state.get("tg_n_prod", len(opgeslagen))

    st.markdown(
        '<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:12px;">'
        'Voeg de producten toe die je wil testen. Carboo roteert ze doorheen het schema. '
        'Voeg meerdere types toe om te vergelijken.</div>', unsafe_allow_html=True)

    h1, h2, h3, h4, h5 = st.columns([3,2,1,1,1])
    for col, lbl in [(h1,"Product naam"),(h2,"Type"),(h3,"KH/portie"),(h4,"ml/portie"),(h5,"")]:
        col.markdown(f'<div style="font-size:10px;color:#64748b;">{lbl}</div>', unsafe_allow_html=True)

    producten = []
    for i in range(n):
        p = opgeslagen[i] if i < len(opgeslagen) else {"naam":"","type":"Gel","kh":22,"ml":0}
        c1,c2,c3,c4,c5 = st.columns([3,2,1,1,1])
        with c1:
            naam = st.text_input(f"n{i}", value=p.get("naam",""),
                                  placeholder="bijv. Maurten Gel 100",
                                  key=f"tg_pnaam_{i}", label_visibility="collapsed")
        with c2:
            idx_t = PRODUCT_TYPES.index(p.get("type","Gel")) if p.get("type") in PRODUCT_TYPES else 0
            ptype = st.selectbox(f"t{i}", PRODUCT_TYPES, index=idx_t,
                                  key=f"tg_ptype_{i}", label_visibility="collapsed")
        with c3:
            kh = st.number_input(f"k{i}", 0, 120, int(p.get("kh",22)),
                                   key=f"tg_pkh_{i}", label_visibility="collapsed")
        with c4:
            ml = st.number_input(f"m{i}", 0, 1000, int(p.get("ml",0)),
                                  key=f"tg_pml_{i}", label_visibility="collapsed")
        with c5:
            if n > 1 and st.button("✕", key=f"tg_pdel_{i}"):
                st.session_state["tg_n_prod"] = n - 1
                st.rerun()
        producten.append({"naam":naam,"type":ptype,"kh":kh,"ml":ml})

    if st.button("＋ Product toevoegen", key="tg_padd"):
        st.session_state["tg_n_prod"] = n + 1
        st.rerun()

    with st.expander("📋 Voorbeeldproducten met KH-waarden"):
        voor = [
            ("Maurten Gel 100","Gel",25,0),("SIS Go Gel","Gel",22,0),
            ("Maurten 320 (500ml)","Sportdrank",80,500),
            ("SIS Beta Fuel (500ml)","Sportdrank",80,500),
            ("Rijstwafel","Vast voedsel",25,0),("Banaan","Vast voedsel",23,0),
            ("Maurten Gel 100 CAF","Cafeïnegel",25,0),
        ]
        for nm, pt, kh, ml in voor:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
                f'font-size:12px;border-bottom:1px solid #1e293b;">'
                f'<span style="color:#f8fafc;">{nm}</span>'
                f'<span style="color:#64748b;">{pt} · {kh}g KH'
                f'{f" · {ml}ml" if ml else ""}</span></div>',
                unsafe_allow_html=True)

    c_terug, c_next = st.columns(2)
    with c_terug:
        if st.button("← Terug", key="tg_prod_back"):
            st.session_state.tg_stap = 2
            st.rerun()
    with c_next:
        if st.button("Genereer schema →", key="tg_prod_next", use_container_width=True):
            gevulde = [p for p in producten if p["naam"]]
            if not gevulde:
                st.error("Voeg minstens 1 product toe.")
            else:
                st.session_state.tg_data["producten"] = gevulde
                st.session_state.tg_stap = 4
                st.rerun()


# ── Stap 4: Schema ────────────────────────────────────────────────────────────
def _stap_schema():
    _sectie("TESTSCHEMA")
    data   = st.session_state.get("tg_data", {})
    schema = _genereer_schema(data)
    target = data.get("target_kh", 60)

    fase_kleuren = {"opbouw":"#3b82f6","midden":"#f97316","finale":"#22c55e"}
    fase_namen   = {"opbouw":"Opbouw","midden":"Intensiteit opbouw","finale":"Wedstrijdsimulatie"}

    c1,c2,c3 = st.columns(3)
    for col, lbl, val, kleur in [
        (c1,"Weken",str(data.get("weken",6)),"#f97316"),
        (c2,"KH opbouw",f"{schema[0]['kh_doel']}→{target}g","#f8fafc"),
        (c3,"Producten",str(len(data.get("producten",[]))),"#8b5cf6"),
    ]:
        col.markdown(
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;'
            f'padding:12px;text-align:center;">'
            f'<div style="font-size:1.4rem;font-weight:800;color:{kleur};">{val}</div>'
            f'<div style="font-size:11px;color:#64748b;">{lbl}</div></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for week in schema:
        kleur = fase_kleuren[week["fase"]]
        innamen = " → ".join([f"+{week['interval']*i}min" for i in range(1,week["porties"]+1)]) if week["porties"]>1 else f"+{week['interval']}min"

        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                    padding:14px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-weight:800;color:#f8fafc;">Week {week['week']}</span>
                    <span style="font-size:11px;color:#64748b;">{week['datum'].strftime('%d/%m/%Y')}</span>
                    <span style="background:rgba(255,255,255,0.05);color:{kleur};
                                 font-size:10px;padding:2px 8px;border-radius:4px;border:1px solid {kleur};">
                        {fase_namen[week['fase']]}</span>
                </div>
                <span style="font-weight:800;color:{kleur};">{week['kh_doel']}g/uur</span>
            </div>
            <div style="background:#1e293b;border-radius:4px;height:5px;overflow:hidden;margin-bottom:10px;">
                <div style="width:{week['pct']}%;height:100%;background:{kleur};border-radius:4px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.78rem;color:#94a3b8;">
                <div>🧪 <b style="color:#f8fafc;">{week['product']}</b> ({week['type']})</div>
                <div>💊 {week['porties']}x {week['kh_pp']}g = {week['kh_doel']}g KH</div>
                <div>⏱ {week['intensiteit']}</div>
                <div>📍 {innamen}</div>
            </div>
            <div style="margin-top:8px;font-size:0.75rem;color:#64748b;font-style:italic;
                        border-top:1px solid #1e293b;padding-top:6px;">
                💡 {week['tip']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    c_terug, c_next = st.columns(2)
    with c_terug:
        if st.button("← Terug", key="tg_schema_back"):
            st.session_state.tg_stap = 3
            st.rerun()
    with c_next:
        if st.button("📝 Start logboek →", key="tg_schema_next", use_container_width=True):
            st.session_state.tg_data["schema"] = [
                {**w, "datum": str(w["datum"])} for w in schema]
            st.session_state.tg_stap = 5
            st.rerun()


# ── Stap 5: Logboek ───────────────────────────────────────────────────────────
def _stap_logboek():
    _sectie("LOGBOEK")
    data   = st.session_state.get("tg_data", {})
    schema = data.get("schema", [])
    logs   = st.session_state.get("tg_logs", {})

    st.markdown(
        '<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:14px;">'
        'Vul na elke testtraining in hoe je je voelde. Wees eerlijk — '
        'dit bepaalt welke producten je op racedag gebruikt.</div>',
        unsafe_allow_html=True)

    ingevuld_count = sum(1 for w in schema if logs.get(str(w["week"]),{}).get("ingevuld"))
    pct_done = round((ingevuld_count / len(schema)) * 100) if schema else 0
    kleur_done = "#22c55e" if pct_done==100 else ("#fbbf24" if pct_done>=50 else "#f97316")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
        <div style="flex:1;background:#1e293b;border-radius:4px;height:6px;overflow:hidden;">
            <div style="width:{pct_done}%;height:100%;background:{kleur_done};border-radius:4px;"></div>
        </div>
        <span style="font-size:12px;color:{kleur_done};font-weight:700;min-width:80px;">
            {ingevuld_count}/{len(schema)} weken</span>
    </div>
    """, unsafe_allow_html=True)

    eerste_open = min(
        [x["week"] for x in schema if not logs.get(str(x["week"]),{}).get("ingevuld")],
        default=1)

    for week in schema:
        w   = week["week"]
        log = logs.get(str(w), {})
        ok  = log.get("ingevuld", False)

        with st.expander(
            f"Week {w} — {week['product']} · {week['kh_doel']}g/uur {'✅' if ok else '⬜'}",
            expanded=(not ok and w == eerste_open)):

            st.markdown(f"""
            <div style="background:#0a0f1e;border:1px solid #1e293b;border-radius:6px;
                        padding:10px;font-size:0.78rem;color:#64748b;margin-bottom:12px;">
                📅 {week['datum']} &nbsp;·&nbsp; ⏱ {week['intensiteit']}
                &nbsp;·&nbsp; 🧪 {week['porties']}x {week['product']}
                &nbsp;·&nbsp; 💊 {week['kh_doel']}g KH/uur
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                score = st.slider("Verdraagbaarheid (1=slecht — 5=uitstekend)",
                                   1, 5, int(log.get("score",3)), key=f"tg_score_{w}")
                st.markdown(
                    f'<div style="font-size:0.8rem;color:{_score_kleur(score)};font-weight:700;">'
                    f'{_score_label(score)}</div>', unsafe_allow_html=True)
            with c2:
                symptoom = st.selectbox("Symptomen", SYMPTOMEN,
                    index=SYMPTOMEN.index(log.get("symptoom","Geen klachten")),
                    key=f"tg_symp_{w}")

            int_uitg = st.selectbox("Werkelijk uitgevoerde intensiteit", INTENSITEITEN,
                index=INTENSITEITEN.index(log.get("int_uitg",week["intensiteit"]))
                if log.get("int_uitg") in INTENSITEITEN else 1, key=f"tg_int_{w}")

            c3, c4 = st.columns(2)
            with c3:
                temp = st.number_input("Temperatuur (°C)", -5, 45,
                                        int(log.get("temp",18)), 1, key=f"tg_temp_{w}")
            with c4:
                timing_ok = st.radio("Innamen op geplande tijdstip?",
                    ["Ja","Gedeeltelijk","Neen"],
                    index=["Ja","Gedeeltelijk","Neen"].index(log.get("timing_ok","Ja")),
                    key=f"tg_timing_{w}", horizontal=True)

            notitie = st.text_area(
                "Notities (smaak, textuur, praktisch gebruik, aanpassingen)",
                value=log.get("notitie",""), key=f"tg_notitie_{w}", height=80,
                placeholder="Hoe smaakte het? Maagklachten op welk moment? Zou je het opnieuw gebruiken?")

            actie = st.selectbox("Actie voor volgende week", [
                "Doorgaan met dit product",
                "Hoeveelheid verlagen en opnieuw testen",
                "Ander product testen",
                "Product schrappen"],
                index=["Doorgaan met dit product","Hoeveelheid verlagen en opnieuw testen",
                       "Ander product testen","Product schrappen"].index(
                    log.get("actie","Doorgaan met dit product")),
                key=f"tg_actie_{w}")

            if st.button(f"✅ Opslaan week {w}", key=f"tg_save_{w}", use_container_width=True):
                if "tg_logs" not in st.session_state:
                    st.session_state.tg_logs = {}
                st.session_state.tg_logs[str(w)] = {
                    "score": score, "symptoom": symptoom, "int_uitg": int_uitg,
                    "temp": temp, "timing_ok": timing_ok,
                    "notitie": notitie, "actie": actie, "ingevuld": True,
                }
                st.success(f"✅ Week {w} opgeslagen!")
                st.rerun()

    c_terug, c_rapport = st.columns(2)
    with c_terug:
        if st.button("← Schema", key="tg_log_back"):
            st.session_state.tg_stap = 4
            st.rerun()
    with c_rapport:
        if st.button("📊 Rapport →", key="tg_log_rapport", use_container_width=True):
            st.session_state.tg_stap = 6
            st.rerun()


# ── Stap 6: Rapport ───────────────────────────────────────────────────────────
def _stap_rapport():
    _sectie("TESTRAPPORT — TRAIN THE GUT")
    data     = st.session_state.get("tg_data", {})
    schema   = data.get("schema", [])
    logs     = st.session_state.get("tg_logs", {})

    ingevuld = [w for w in schema if logs.get(str(w["week"]),{}).get("ingevuld")]
    if not ingevuld:
        st.warning("Nog geen trainingen gelogd.")
        if st.button("← Naar logboek", key="tg_rep_back2"):
            st.session_state.tg_stap = 5
            st.rerun()
        return

    gem_score = sum(logs[str(w["week"])]["score"] for w in ingevuld) / len(ingevuld)
    max_kh    = max(w["kh_doel"] for w in ingevuld)
    klachten  = [w for w in ingevuld if logs[str(w["week"])]["symptoom"] != "Geen klachten"]

    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                padding:18px;margin-bottom:18px;">
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:12px;">
            SAMENVATTING — {data.get('sport','').upper()}</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
            <div style="text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:#f97316;">
                    {len(ingevuld)}/{len(schema)}</div>
                <div style="font-size:11px;color:#64748b;">trainingen gelogd</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:{_score_kleur(gem_score)};">
                    {gem_score:.1f}/5</div>
                <div style="font-size:11px;color:#64748b;">gemiddelde score</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:#22c55e;">{max_kh}g</div>
                <div style="font-size:11px;color:#64748b;">max KH/uur getest</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:{'#22c55e' if not klachten else '#fbbf24'};">
                    {len(klachten)}</div>
                <div style="font-size:11px;color:#64748b;">trainingen met klachten</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _sectie("PRODUCTRESULTATEN", "#8b5cf6")
    prod_data = {}
    for w in ingevuld:
        log  = logs[str(w["week"])]
        prod = w["product"]
        if prod not in prod_data:
            prod_data[prod] = {"scores":[],"symptomen":[],"kh_max":0,"acties":[]}
        prod_data[prod]["scores"].append(log["score"])
        prod_data[prod]["symptomen"].append(log["symptoom"])
        prod_data[prod]["kh_max"] = max(prod_data[prod]["kh_max"], w["kh_doel"])
        prod_data[prod]["acties"].append(log.get("actie",""))

    aanbevolen = []
    vermijden  = []

    for prod, pdata in prod_data.items():
        scores = pdata["scores"]
        gem    = sum(scores) / len(scores)
        kleur  = _score_kleur(gem)
        ok     = gem >= 4.0
        symp_freq = max(set(pdata["symptomen"]), key=pdata["symptomen"].count)
        actie_freq = max(set(pdata["acties"]), key=pdata["acties"].count)
        if ok: aanbevolen.append(prod)
        else:  vermijden.append(prod)

        st.markdown(f"""
        <div style="background:#0f172a;border:2px solid {'#22c55e' if ok else '#ef4444'};
                    border-radius:12px;padding:14px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
                <div>
                    <div style="font-weight:800;color:#f8fafc;">{prod}</div>
                    <div style="font-size:11px;color:#64748b;">{len(scores)} test(s) · max {pdata['kh_max']}g KH/uur</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.3rem;font-weight:800;color:{kleur};">{gem:.1f}/5</div>
                    <div style="font-size:10px;color:{'#22c55e' if ok else '#ef4444'};">
                        {'✅ Aanbevolen' if ok else '❌ Vermijden'}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.75rem;color:#94a3b8;">
                <div>⚠️ Symptoom: <b style="color:#f8fafc;">{symp_freq}</b></div>
                <div>📋 Advies: <b style="color:#f8fafc;">{actie_freq}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    _sectie("AANBEVELING VOOR RACEDAG", "#22c55e")
    if aanbevolen:
        st.success(f"✅ Goedgekeurde producten: **{', '.join(aanbevolen)}**")
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #22c55e;border-radius:8px;
                    padding:14px;font-size:0.82rem;color:#94a3b8;line-height:1.7;margin-top:8px;">
            Je hebt aangetoond dat je maag <b style="color:#22c55e;">{max_kh}g KH/uur</b>
            verdraagt. Gebruik <b style="color:#f8fafc;">enkel geteste producten</b> op racedag.
            <br><br>
            🏁 Je bent klaar om dit te integreren in je
            <b style="color:#f97316;">Race Nutrition Coach</b> raceplan.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Nog geen producten met score ≥ 4. Ga verder met testen.")

    if vermijden:
        st.error(f"❌ Vermijden op racedag: **{', '.join(vermijden)}**")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Terug naar logboek", key="tg_rep_back"):
            st.session_state.tg_stap = 5
            st.rerun()
    with c2:
        if st.button("🔄 Nieuw testschema", key="tg_nieuw", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("tg_"):
                    del st.session_state[k]
            st.rerun()


# ── Hoofdfunctie ──────────────────────────────────────────────────────────────
def render_testing(user: dict):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <div style="font-size:2rem;font-weight:900;letter-spacing:3px;color:#f8fafc;">
            CAR<span style="color:#f97316;">BOO</span></div>
        <div style="font-size:0.85rem;font-weight:700;color:#8b5cf6;letter-spacing:2px;
                     border:1px solid #8b5cf6;border-radius:6px;padding:3px 10px;">
            TRAIN THE GUT</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Terug naar modules", key="tg_terug_top"):
        st.session_state.module = "menu"
        st.rerun()

    stap = st.session_state.get("tg_stap", 1)
    namen = ["Intro","Profiel","Producten","Schema","Logboek","Rapport"]
    cols  = st.columns(len(namen))
    for i, (col, naam) in enumerate(zip(cols, namen)):
        actief = (i+1) == stap
        gedaan = i+1 < stap
        kleur  = "#f97316" if actief else ("#22c55e" if gedaan else "#334155")
        col.markdown(
            f'<div style="text-align:center;font-size:10px;font-weight:700;'
            f'color:{kleur};border-bottom:2px solid {kleur};padding-bottom:4px;">'
            f'{"✓ " if gedaan else ""}{naam}</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if   stap == 1: _stap_intro(); st.markdown("<br>",unsafe_allow_html=True); \
        st.button("Start Train the Gut →",key="tg_start",use_container_width=True) and \
        (st.session_state.update({"tg_stap":2}) or st.rerun())
    elif stap == 2: _stap_profiel()
    elif stap == 3: _stap_producten()
    elif stap == 4: _stap_schema()
    elif stap == 5: _stap_logboek()
    elif stap == 6: _stap_rapport()
