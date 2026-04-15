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

# Zelfde KH targets als Race Nutrition Plan (carboo_coach.py)
KH_TARGETS = {
    "Fietsen":      {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":        {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":      {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":     {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}

def _get_richtlijn(sport, duur_min):
    """Geeft (kh_min, kh_max) op basis van sport en wedstrijdduur."""
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= duur_min < hi:
            return mn, mx
    return 0, 0


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


def _genereer_tips(data: dict) -> list:
    """Genereer persoonlijke tips op basis van profiel."""
    tips = []
    maag       = data.get("maag_gevoelig","Af en toe")
    klachten   = data.get("klachten_lijst",[])
    klachten_p = data.get("klachten_producten","").lower()
    klachten_b = data.get("klachten_bij","").lower()
    maaltijd   = data.get("laatste_maaltijd","").lower()
    uren       = data.get("uren_voor_start",3)
    vocht      = data.get("vocht_voor_start",500)
    temp       = data.get("temp",16)
    hoogte     = data.get("hoogte",0)
    vochtigheid= data.get("vochtigheid",60)
    eetmom     = data.get("eetmomenten",2)
    drinkmom   = data.get("drinkmomenten",2)

    # Klachten-gebaseerde tips
    if "Misselijkheid" in klachten:
        tips.append("⚠️ Bij misselijkheid: verlaag de concentratie van je sportdrank en spreid innamen meer. Start met kleine slokjes.")
    if "Krampen" in klachten:
        tips.append("⚠️ Bij krampen: neem producten altijd in met voldoende water (min. 150ml per gel). Vermijd grote porties in één keer.")
    if "Opgeblazen gevoel" in klachten:
        tips.append("⚠️ Bij opgeblazen gevoel: vermijd koolzuurhoudende dranken en controleer het fructosegehalte van je producten.")
    if "Diarree" in klachten:
        tips.append("⚠️ Bij diarree: vermijd hoge fructose en te geconcentreerde oplossingen. Bouw zeer geleidelijk op.")

    # Productgerelateerde tips
    for tekst in [klachten_p, klachten_b]:
        if any(w in tekst for w in ["gel","geconcentreerd"]):
            tips.append("💡 Overweeg isotone gels of verdun geconcentreerde gels met extra water.")
        if "fructose" in tekst:
            tips.append("💡 Kies producten met enkel glucose of een lage fructose-glucoseverhouding.")
        if any(w in tekst for w in ["vast","wafel","banaan","reep"]):
            tips.append("💡 Vermijd vast voedsel in de eerste 2 weken van het testschema.")

    # Laatste maaltijd tips
    if any(w in maaltijd for w in ["vet","kaas","vlees","ei","room","boter","noten"]):
        tips.append("🍽️ Je laatste maaltijd bevat mogelijk te veel vet. Kies voor koolhydraatrijke, vetarme voeding.")
    if any(w in maaltijd for w in ["groente","salade","broccoli","vezels","fruit"]):
        tips.append("🍽️ Beperk vezels en rauwe groenten in je laatste maaltijd — dit vertraagt de maagontlediging.")
    if uren < 3:
        tips.append(f"⏰ Je eet de laatste maaltijd {uren}u voor de start — probeer dit naar 2.5–3u te vervroegen.")
    if vocht < 400:
        tips.append("💧 Je drinkt te weinig voor de wedstrijd. Streef naar 500ml water 2u voor de start.")
    if vocht > 1000:
        tips.append("💧 Meer dan 1000ml voor de start verhoogt het risico op hyponatriëmie. Spreid je vochtinname beter.")

    # Omstandigheden tips
    if temp > 28:
        tips.append("🌡️ Bij temperaturen boven 28°C: prioriteit gaat naar vocht. Voeg ORS toe en verhoog drinkfrequentie.")
    if hoogte > 2000:
        tips.append("🏔️ Boven 2000m daalt de eetlust. Start met vloeibare KH en bouw extra traag op.")
    if vochtigheid > 80:
        tips.append("💦 Hoge luchtvochtigheid: voeg extra natrium toe en verhoog je vochtinname per uur.")

    # Inname patroon tips
    if eetmom == 1:
        tips.append("🍌 Je eet 1x per uur — dit zijn grote porties. Verdeel over 2-3 momenten voor betere vertering.")
    if drinkmom == 1:
        tips.append("🥤 Je drinkt 1x per uur — grote slokken verhogen maagklachten. Drink liever 2-3x kleinere hoeveelheden.")
    if eetmom == 3:
        tips.append("✅ 3 eetmomenten per uur is optimaal voor maagontlediging en constante energietoevoer.")
    if drinkmom == 3:
        tips.append("✅ 3 drinkmomenten per uur bevordert optimale hydratatie en maagontlediging.")

    return tips


def _bereken_startpunt(data: dict) -> int:
    """Bereken startpunt in g KH/uur op basis van alle parameters."""
    maag      = data.get("maag_gevoelig","Af en toe")
    ervaring  = data.get("ervaring","Nog nooit")
    sport     = data.get("sport","Fietsen")
    inname    = data.get("huidige_inname",40)
    temp      = data.get("temp",16)
    hoogte    = data.get("hoogte",0)

    if maag == "Altijd met sportvoeding":
        start = 10
    else:
        erv_factor = {
            "Nog nooit": 0.50,
            "2-4 wedstrijden": 0.70,
            "5-10 wedstrijden": 0.85,
            "Meer dan 10 wedstrijden": 1.00,
        }.get(ervaring, 0.70)
        start = round(inname * erv_factor)
        if maag == "Af en toe":
            start = max(10, start - 5)
        if sport == "Lopen":
            start = max(10, start - 5)

    # Omstandigheden correcties
    if temp > 28:
        start = max(10, start - 5)
    if hoogte > 2000:
        start = max(10, start - 5)

    return round(start / 5) * 5  # afronden op 5g


def _stap_intro():
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;
                padding:24px;margin-bottom:20px;">
        <div style="font-size:1rem;font-weight:800;color:#f8fafc;margin-bottom:10px;">
            Waarom maagtraining?</div>
        <div style="font-size:0.85rem;color:#94a3b8;line-height:1.8;">
            Tijdens intensieve inspanning vermindert de bloedtoevoer naar je maag.
            Dit maakt het moeilijker om voeding te verteren. Door systematisch te trainen
            went je maag aan grotere hoeveelheden koolhydraten.
            <br><br>
            Onderzoek toont aan dat atleten die hun maag trainen
            <b style="color:#f97316;">significant minder maagklachten</b>
            rapporteren op racedag.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _sectie("HOE WERKT HET?")
    for nr, naam, uitleg in [
        ("1","Profiel","Sport, duur en KH-target instellen"),
        ("2","Producten","Gels, sportdranken of vast voedsel toevoegen"),
        ("3","Schema","Week per week testschema — dynamisch aangepast"),
        ("4","Dagboek","Na elke training score en symptomen invullen"),
        ("5","Rapport","Welke producten werken voor jou op racedag"),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;' +
            f'border-bottom:1px solid #1e293b;">' +
            f'<div style="width:24px;height:24px;border-radius:50%;background:#f97316;' +
            f'display:flex;align-items:center;justify-content:center;font-size:11px;' +
            f'font-weight:700;color:white;flex-shrink:0;">{nr}</div>' +
            f'<div><span style="font-weight:600;color:#f8fafc;">{naam}</span> ' +
            f'<span style="color:#64748b;font-size:0.82rem;">— {uitleg}</span></div>' +
            f'</div>', unsafe_allow_html=True)


def _stap_profiel():
    _sectie("JOUW TRAININGSPROFIEL")
    data    = st.session_state.get("tg_data", {})
    weken   = 6
    ERV_OPTIES = ["Nog nooit","2-4 wedstrijden","5-10 wedstrijden","Meer dan 10 wedstrijden"]

    c1, c2 = st.columns(2)
    with c1:
        sport = st.selectbox("Sport", SPORTEN,
                              index=SPORTEN.index(data.get("sport","Fietsen")),
                              key="tg_sport")
        wedstrijd_datum = st.date_input("Wedstrijddatum",
                                         value=date.fromisoformat(data.get("wedstrijd_datum",
                                             str(date.today() + timedelta(weeks=8)))),
                                         key="tg_wedstrijddatum")
        import re as _re
        wd_raw = st.text_input("Geschatte wedstrijdduur (bv. 3u15 of 2u30)",
                                value=data.get("wedstrijd_duur_str",""),
                                placeholder="bijv. 3u15",
                                key="tg_wd_raw")
        _m = _re.match(r"(\d+)u(\d+)?", wd_raw.strip().lower())
        if _m:
            wedstrijd_duur = int(_m.group(1))*60 + int(_m.group(2) or 0)
        else:
            wedstrijd_duur = int(data.get("wedstrijd_duur",180))

        ervaring = st.selectbox("Ervaring met wedstrijdvoeding", ERV_OPTIES,
                                 index=ERV_OPTIES.index(data.get("ervaring","Nog nooit")),
                                 key="tg_ervaring")
        heeft_erv = ervaring != "Nog nooit"

    with c2:
        niveau = st.selectbox("Niveau", ["Recreatief","Competitief","Elite"],
                               index=["Recreatief","Competitief","Elite"].index(
                                   data.get("niveau","Recreatief")), key="tg_niveau")
        maag_gevoelig = st.selectbox("Gevoelige maag?",
                                      ["Nooit","Af en toe","Altijd met sportvoeding"],
                                      index=["Nooit","Af en toe","Altijd met sportvoeding"].index(
                                          data.get("maag_gevoelig","Nooit")), key="tg_maag")
        huidige_inname = 0
        if heeft_erv:
            huidige_inname = st.number_input(
                "Geschatte inname KH tijdens vorige wedstrijden (g/uur)",
                0, 150, int(data.get("huidige_inname",40)), 5, key="tg_huidige_inname")

    eetmomenten   = int(data.get("eetmomenten",2))
    drinkmomenten = int(data.get("drinkmomenten",2))
    if heeft_erv:
        _sectie("INNAME PATROON BIJ VORIGE WEDSTRIJDEN")
        c3, c4 = st.columns(2)
        with c3:
            eetmomenten = st.radio("Hoeveel eetmomenten per uur?", [1,2,3],
                                    index=[1,2,3].index(eetmomenten),
                                    key="tg_eetmomenten", horizontal=True)
        with c4:
            drinkmomenten = st.radio("Hoeveel drinkmomenten per uur?", [1,2,3],
                                      index=[1,2,3].index(drinkmomenten),
                                      key="tg_drinkmomenten", horizontal=True)

    _sectie("KH TARGET RACEDAG")
    kh_min_r, kh_max_r = _get_richtlijn(sport, wedstrijd_duur)
    target_kh = st.slider("KH-target op racedag (g/uur)", 0, 120,
                           int(data.get("target_kh", max(kh_min_r,30))), 5, key="tg_target")
    if kh_max_r > 0:
        st.markdown(f'<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">' +
                    f'Richtlijn literatuur: <b style="color:#f8fafc;">{kh_min_r}–{kh_max_r}g/uur</b></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">' +
                    'Richtlijn literatuur: <b style="color:#f8fafc;">geen extra KH nodig</b></div>',
                    unsafe_allow_html=True)

    start_kh = round(target_kh * SPORT_START_PCT.get(sport,0.35) / 5) * 5

    klachten_producten = data.get("klachten_producten","")
    klachten_lijst     = data.get("klachten_lijst",[])
    laatste_maaltijd   = data.get("laatste_maaltijd","")
    uren_voor_start    = data.get("uren_voor_start",3)
    vocht_voor_start   = data.get("vocht_voor_start",500)

    if maag_gevoelig in ["Altijd met sportvoeding","Af en toe"]:
        kleur_s = "#ef4444" if maag_gevoelig=="Altijd met sportvoeding" else "#fbbf24"
        _sectie("MAAGKLACHTEN BIJ VORIGE WEDSTRIJDEN", kleur_s)
        st.markdown('<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:10px;">' +
                    'De vragen hieronder gaan over ervaringen uit vorige wedstrijden.</div>',
                    unsafe_allow_html=True)
        klachten_producten = st.text_area("Welke producten gebruik(te) je?",
                                           value=klachten_producten, key="tg_kl_prod", height=68,
                                           placeholder="bijv. Maurten gels, SIS sportdrank...")
        KLACHTEN_OPTIES = ["Misselijkheid","Krampen","Opgeblazen gevoel","Diarree"]
        klachten_lijst = st.multiselect("Welke klachten had je?", KLACHTEN_OPTIES,
                                         default=[k for k in data.get("klachten_lijst",[])
                                                  if k in KLACHTEN_OPTIES], key="tg_kl_lijst")
        c5, c6 = st.columns(2)
        with c5:
            laatste_maaltijd = st.text_area("Samenstelling laatste maaltijd voor de wedstrijd",
                                             value=laatste_maaltijd, key="tg_lm", height=68,
                                             placeholder="bijv. pasta, rijst, brood...")
            uren_voor_start = st.number_input("Hoeveel uur voor de start at je?",
                                               1, 6, int(uren_voor_start), 1, key="tg_uren_start")
        with c6:
            vocht_voor_start = st.number_input("Hoeveel ml dronk je voor de wedstrijd?",
                                                0, 2000, int(vocht_voor_start), 100,
                                                key="tg_vocht_start")

    _sectie("WEDSTRIJDOMSTANDIGHEDEN")
    c7, c8 = st.columns(2)
    with c7:
        wedstrijd_plaats = st.text_input("Plaats van wedstrijd",
                                          value=data.get("wedstrijd_plaats",""),
                                          placeholder="bijv. Gent, Mallorca", key="tg_plaats")
        temp = st.number_input("Verwachte temperatuur (°C)", -10, 50,
                                int(data.get("temp",16)), 1, key="tg_temp")
    with c8:
        hoogte = st.number_input("Hoogte (m)", 0, 5000,
                                  int(data.get("hoogte",0)), 50, key="tg_hoogte")
        vochtigheid = st.number_input("Luchtvochtigheid (%)", 0, 100,
                                       int(data.get("vochtigheid",60)), 5, key="tg_vochtigheid")

    if st.button("Volgende →", key="tg_prof_next", use_container_width=True):
        st.session_state.tg_data = {
            "sport":sport,"weken":weken,"target_kh":target_kh,
            "niveau":niveau,"ervaring":ervaring,
            "wedstrijd_datum":str(wedstrijd_datum),
            "wedstrijd_duur":wedstrijd_duur,"wedstrijd_duur_str":wd_raw,
            "maag_gevoelig":maag_gevoelig,"huidige_inname":huidige_inname,
            "eetmomenten":eetmomenten,"drinkmomenten":drinkmomenten,
            "klachten_producten":klachten_producten,"klachten_lijst":klachten_lijst,
            "laatste_maaltijd":laatste_maaltijd,"uren_voor_start":uren_voor_start,
            "vocht_voor_start":vocht_voor_start,"wedstrijd_plaats":wedstrijd_plaats,
            "temp":temp,"hoogte":hoogte,"vochtigheid":vochtigheid,"start_kh":start_kh,
        }
        st.session_state.tg_stap = 3
        st.rerun()


def _stap_producten():
    _sectie("TE TESTEN PRODUCTEN")
    data = st.session_state.get("tg_data", {})
    opgeslagen = data.get("producten",[{"naam":"","type":"Gel","kh":22}])
    n = st.session_state.get("tg_n_prod", len(opgeslagen))

    st.markdown('<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:12px;">' +
                'Voeg de producten toe die je wil testen voor de wedstrijd.</div>',
                unsafe_allow_html=True)

    h1,h2,h3,h4 = st.columns([3,2,1,1])
    for col, lbl in [(h1,"Product naam"),(h2,"Type"),(h3,"KH/portie"),(h4,"")]:
        col.markdown(f'<div style="font-size:10px;color:#64748b;">{lbl}</div>',
                     unsafe_allow_html=True)

    producten = []
    for i in range(n):
        p = opgeslagen[i] if i < len(opgeslagen) else {"naam":"","type":"Gel","kh":22}
        c1,c2,c3,c4 = st.columns([3,2,1,1])
        with c1:
            naam = st.text_input(f"n{i}", value=p.get("naam",""),
                                  placeholder="Productnaam",
                                  key=f"tg_pnaam_{i}", label_visibility="collapsed")
        with c2:
            idx_t = PRODUCT_TYPES.index(p.get("type","Gel")) if p.get("type") in PRODUCT_TYPES else 0
            ptype = st.selectbox(f"t{i}", PRODUCT_TYPES, index=idx_t,
                                  key=f"tg_ptype_{i}", label_visibility="collapsed")
        with c3:
            kh = st.number_input(f"k{i}", 0, 120, int(p.get("kh",22)),
                                   key=f"tg_pkh_{i}", label_visibility="collapsed")
        with c4:
            if n > 1 and st.button("✕", key=f"tg_pdel_{i}"):
                st.session_state["tg_n_prod"] = n - 1
                st.rerun()
        producten.append({"naam":naam,"type":ptype,"kh":kh})

    if st.button("＋ Product toevoegen", key="tg_padd"):
        st.session_state["tg_n_prod"] = n + 1
        st.rerun()

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


def _bereken_week_kh(data: dict, logs: dict, week_nr: int) -> int:
    """Bereken KH target voor een bepaalde week op basis van vorige logboeken."""
    start_kh = int(data.get("start_kh", 20))
    target   = int(data.get("target_kh", 60))
    weken    = int(data.get("weken", 6))

    if week_nr == 1:
        return start_kh

    # Kijk naar vorige week log
    prev_log = logs.get(str(week_nr - 1), {})
    if not prev_log.get("ingevuld"):
        # Geen log — gebruik lineaire opbouw
        stijging = round((target - start_kh) / max(weken - 1, 1) / 5) * 5
        return min(start_kh + (week_nr - 1) * stijging, target)

    score   = prev_log.get("score", 3)
    symptoom = prev_log.get("symptoom", "Geen klachten")
    heeft_klachten = symptoom != "Geen klachten"
    prev_kh = prev_log.get("kh_doel", start_kh)

    if score == 5 and not heeft_klachten:
        delta = 10
    elif score == 4 and not heeft_klachten:
        delta = 8
    elif score == 3 and not heeft_klachten:
        delta = 5
    elif score == 3 and heeft_klachten:
        delta = 0  # herhalen
    elif score == 2:
        delta = -5
    else:  # score 1
        delta = -10

    nieuw_kh = prev_kh + delta
    nieuw_kh = round(nieuw_kh / 5) * 5
    nieuw_kh = max(10, min(nieuw_kh, target))
    return nieuw_kh


def _week_beschikbaar(week_nr: int, logs: dict) -> bool:
    """Week N is beschikbaar als week N-1 ingevuld is (of week 1 altijd)."""
    if week_nr == 1:
        return True
    return logs.get(str(week_nr - 1), {}).get("ingevuld", False)


def _genereer_week(data: dict, logs: dict, week_nr: int) -> dict:
    """Genereer schema voor één week op basis van dynamische KH berekening."""
    from datetime import date as _date
    sport     = data.get("sport", "Fietsen")
    producten = [p for p in data.get("producten", []) if p.get("naam")]
    eetmom    = int(data.get("eetmomenten", 2))
    weken     = int(data.get("weken", 6))

    kh_doel = _bereken_week_kh(data, logs, week_nr)
    fase    = _week_fase(week_nr, weken)
    intensiteit = FASE_INTENSITEIT[fase]

    prod = producten[(week_nr - 1) % len(producten)] if producten else {"naam":"—","type":"Gel","kh":22}
    kh_pp   = prod.get("kh", 22)
    porties = max(1, round(kh_doel / kh_pp)) if kh_pp > 0 else 1
    interval = max(10, round(60 / max(eetmom, porties) / 5) * 5)

    return {
        "week":        week_nr,
        "kh_doel":     kh_doel,
        "pct":         round((kh_doel / max(data.get("target_kh",60), 1)) * 100),
        "product":     prod.get("naam", "—"),
        "type":        prod.get("type", "Gel"),
        "kh_pp":       kh_pp,
        "porties":     porties,
        "interval":    interval,
        "intensiteit": intensiteit,
        "fase":        fase,
        "tip":         _week_tip(week_nr, weken, kh_doel, sport),
    }


def _stap_schema():
    """Toont het schema week per week — enkel beschikbare weken zichtbaar."""
    _sectie("TESTSCHEMA")
    data  = st.session_state.get("tg_data", {})
    logs  = st.session_state.get("tg_logs", {})
    weken = int(data.get("weken", 6))
    target = int(data.get("target_kh", 60))

    tips = _genereer_tips(data)
    if tips:
        _sectie("PERSOONLIJKE TIPS", "#fbbf24")
        for tip in tips:
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #fbbf24;border-radius:8px;' +
                f'padding:10px 14px;font-size:0.82rem;color:#f1f5f9;margin-bottom:6px;">{tip}</div>',
                unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    _sectie("WEKELIJKS SCHEMA")

    fase_kleuren = {"opbouw":"#3b82f6","midden":"#f97316","finale":"#22c55e"}
    fase_namen   = {"opbouw":"Opbouw","midden":"Intensiteit opbouw","finale":"Wedstrijdsimulatie"}

    for w in range(1, weken + 1):
        beschikbaar = _week_beschikbaar(w, logs)
        log_w       = logs.get(str(w), {})
        ingevuld    = log_w.get("ingevuld", False)
        week        = _genereer_week(data, logs, w)
        kleur       = fase_kleuren[week["fase"]]
        pct         = week["pct"]

        if not beschikbaar:
            # Gelockt tonen
            st.markdown(f"""
            <div style="background:#0a0f1e;border:1px solid #1e293b;border-radius:10px;
                        padding:12px 14px;margin-bottom:8px;opacity:0.4;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#334155;font-weight:700;">Week {w} — 🔒 Beschikbaar na week {w-1}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Toon week
            innamen = " → ".join([f"+{week['interval']*i}min" for i in range(1, week["porties"]+1)])                       if week["porties"] > 1 else f"+{week['interval']}min"
            status_icon = "✅" if ingevuld else ("📝" if w == next(
                (x for x in range(1, weken+1) if not logs.get(str(x),{}).get("ingevuld")), weken+1) else "⬜")

            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid {'#22c55e' if ingevuld else kleur};
                        border-radius:10px;padding:14px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-weight:800;color:#f8fafc;">Week {w}</span>
                        <span style="font-size:10px;">{status_icon}</span>
                        <span style="background:rgba(255,255,255,0.05);color:{kleur};
                                     font-size:10px;padding:2px 8px;border-radius:4px;
                                     border:1px solid {kleur};">{fase_namen[week["fase"]]}</span>
                    </div>
                    <span style="font-weight:800;color:{kleur};">{week["kh_doel"]}g/uur</span>
                </div>
                <div style="background:#1e293b;border-radius:4px;height:5px;overflow:hidden;margin-bottom:10px;">
                    <div style="width:{pct}%;height:100%;background:{kleur};border-radius:4px;"></div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.78rem;color:#94a3b8;">
                    <div>🧪 <b style="color:#f8fafc;">{week["product"]}</b> ({week["type"]})</div>
                    <div>💊 {week["porties"]}x {week["kh_pp"]}g = {week["kh_doel"]}g KH</div>
                    <div>⏱ {week["intensiteit"]}</div>
                    <div>📍 {innamen}</div>
                </div>
                {'<div style="margin-top:8px;font-size:0.75rem;color:#64748b;font-style:italic;border-top:1px solid #1e293b;padding-top:6px;">💡 ' + week["tip"] + "</div>" if week["tip"] else ""}
            </div>
            """, unsafe_allow_html=True)

            # Dagboek knop direct onder elke beschikbare week
            if not ingevuld:
                if st.button(f"📝 Dagboek week {w} invullen", key=f"goto_log_{w}",
                             use_container_width=True):
                    st.session_state["tg_actieve_week"] = w
                    st.session_state.tg_stap = 5
                    st.rerun()
            else:
                # Toon samenvatting log
                s = log_w.get("score", 0)
                sym = log_w.get("symptoom","")
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#64748b;margin:-6px 0 8px 0;">' +
                    f'Score: <b style="color:{_score_kleur(s)};">{s}/5</b>' +
                    (f' · {sym}' if sym and sym != "Geen klachten" else ' · Geen klachten') +
                    f'</div>', unsafe_allow_html=True)

    c_terug, c_rapport = st.columns(2)
    with c_terug:
        if st.button("← Terug", key="tg_schema_back"):
            st.session_state.tg_stap = 3
            st.rerun()
    with c_rapport:
        if st.button("📊 Rapport →", key="tg_schema_rapport", use_container_width=True):
            st.session_state.tg_stap = 6
            st.rerun()


def _stap_logboek():
    """Dynamisch dagboek — toont enkel de actieve week."""
    _sectie("DAGBOEK")
    data   = st.session_state.get("tg_data", {})
    logs   = st.session_state.get("tg_logs", {})
    weken  = int(data.get("weken", 6))

    # Bepaal actieve week
    actieve_week = st.session_state.get("tg_actieve_week",
        next((w for w in range(1, weken+1)
              if not logs.get(str(w),{}).get("ingevuld")), 1))

    week = _genereer_week(data, logs, actieve_week)
    log  = logs.get(str(actieve_week), {})

    # Header
    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                padding:14px;margin-bottom:16px;">
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:6px;">
            WEEK {actieve_week} VAN {weken}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-weight:800;color:#f8fafc;font-size:1rem;">
                    {week["product"]}</div>
                <div style="font-size:0.78rem;color:#64748b;">
                    {week["porties"]}x {week["kh_pp"]}g · {week["kh_doel"]}g/uur · {week["intensiteit"]}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.4rem;font-weight:800;color:#f97316;">
                    {week["kh_doel"]}g/uur</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Week selectie
    beschikbare_weken = [w for w in range(1, weken+1) if _week_beschikbaar(w, logs)]
    if len(beschikbare_weken) > 1:
        actieve_week = st.selectbox(
            "Week selecteren",
            beschikbare_weken,
            index=beschikbare_weken.index(actieve_week) if actieve_week in beschikbare_weken else 0,
            format_func=lambda w: f"Week {w} {'✅' if logs.get(str(w),{}).get('ingevuld') else '📝'}",
            key="tg_week_select")
        st.session_state["tg_actieve_week"] = actieve_week
        week = _genereer_week(data, logs, actieve_week)
        log  = logs.get(str(actieve_week), {})

    st.markdown('<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:14px;">' +
                'Vul in hoe de training verliep. Het schema van volgende week wordt ' +
                'automatisch aangepast op basis van je score.</div>', unsafe_allow_html=True)

    # Invoervelden
    c1, c2 = st.columns(2)
    with c1:
        score = st.slider("Verdraagbaarheid (1=slecht — 5=uitstekend)",
                           1, 5, int(log.get("score", 3)), key=f"tg_score_{actieve_week}")
        st.markdown(
            f'<div style="font-size:0.8rem;color:{_score_kleur(score)};font-weight:700;">' +
            f'{_score_label(score)}</div>', unsafe_allow_html=True)
    with c2:
        symptoom = st.selectbox("Symptomen", SYMPTOMEN,
                                 index=SYMPTOMEN.index(log.get("symptoom","Geen klachten")),
                                 key=f"tg_symp_{actieve_week}")

    int_uitg = st.selectbox("Werkelijk uitgevoerde intensiteit", INTENSITEITEN,
                             index=INTENSITEITEN.index(log.get("int_uitg", week["intensiteit"]))
                             if log.get("int_uitg") in INTENSITEITEN else 1,
                             key=f"tg_int_{actieve_week}")

    c3, c4 = st.columns(2)
    with c3:
        temp_log = st.number_input("Temperatuur tijdens training (°C)", -5, 45,
                                    int(log.get("temp", 18)), 1, key=f"tg_temp_{actieve_week}")
    with c4:
        timing_ok = st.radio("Innamen op geplande tijdstip?",
                              ["Ja","Gedeeltelijk","Neen"],
                              index=["Ja","Gedeeltelijk","Neen"].index(
                                  log.get("timing_ok","Ja")),
                              key=f"tg_timing_{actieve_week}", horizontal=True)

    notitie = st.text_area(
        "Notities",
        value=log.get("notitie",""), key=f"tg_notitie_{actieve_week}", height=80,
        placeholder="Hoe smaakte het? Maagklachten op welk moment? Zou je het opnieuw gebruiken?")

    actie = st.selectbox("Actie voor volgende week", [
        "Doorgaan met dit product",
        "Hoeveelheid verlagen en opnieuw testen",
        "Ander product testen",
        "Product schrappen"],
        index=["Doorgaan met dit product","Hoeveelheid verlagen en opnieuw testen",
               "Ander product testen","Product schrappen"].index(
            log.get("actie","Doorgaan met dit product")),
        key=f"tg_actie_{actieve_week}")

    # Preview volgende week
    if actieve_week < weken:
        preview_logs = dict(logs)
        preview_logs[str(actieve_week)] = {"score":score,"symptoom":symptoom,"kh_doel":week["kh_doel"],"ingevuld":True}
        volgende_kh = _bereken_week_kh(data, preview_logs, actieve_week + 1)
        delta = volgende_kh - week["kh_doel"]
        delta_kleur = "#22c55e" if delta > 0 else ("#ef4444" if delta < 0 else "#fbbf24")
        delta_txt   = f"+{delta}g" if delta > 0 else (f"{delta}g" if delta < 0 else "gelijk")
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                    padding:10px 14px;margin-top:12px;font-size:0.82rem;">
            📋 Op basis van score <b style="color:{_score_kleur(score)};">{score}/5</b>
            wordt week {actieve_week+1}:
            <b style="color:{delta_kleur};">{volgende_kh}g/uur ({delta_txt})</b>
        </div>
        """, unsafe_allow_html=True)

    # Opslaan
    if st.button(f"✅ Opslaan week {actieve_week}", key=f"tg_save_{actieve_week}",
                  use_container_width=True):
        if "tg_logs" not in st.session_state:
            st.session_state.tg_logs = {}
        st.session_state.tg_logs[str(actieve_week)] = {
            "score": score, "symptoom": symptoom, "int_uitg": int_uitg,
            "temp": temp_log, "timing_ok": timing_ok,
            "notitie": notitie, "actie": actie,
            "kh_doel": week["kh_doel"],
            "ingevuld": True,
        }
        st.success(f"✅ Week {actieve_week} opgeslagen!")
        # Ga naar schema voor volgende week
        st.session_state["tg_actieve_week"] = min(actieve_week + 1, weken)
        st.session_state.tg_stap = 4
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
