"""
Train the Gut — Carboo module voor systematische maagtraining
Portie-gebaseerde opbouw | Fase-systeem multisport | Productwaarschuwingen
"""
import streamlit as st
from datetime import date, timedelta

SPORTEN       = ["Fietsen", "Lopen", "Triatlon", "Duatlon", "Crosstriatlon"]
MULTISPORT    = ["Triatlon", "Duatlon", "Crosstriatlon"]
ENKELVOUDIG   = ["Fietsen", "Lopen"]
PRODUCT_TYPES = ["Gel", "Sportdrank", "Vast voedsel", "Cafeïnegel", "Supplement"]
SYMPTOMEN     = [
    "Geen klachten", "Lichte maagkramp", "Misselijkheid",
    "Opgeblazen gevoel", "Reflux / brandend maagzuur",
    "Diarree", "Braken", "Hoofdpijn", "Steken in de zij",
]
INTENSITEITEN = [
    "Z1 — Actief herstel", "Z2 — Duurtraining", "Z3 — Tempo",
    "Z4 — Drempeltraining", "Z5 — Wedstrijdintensiteit",
]

# ── KH targets (zelfde als carboo_coach.py) ───────────────────────────────────
KH_TARGETS = {
    "Fietsen":      {(0,75):(0,0),(75,120):(30,60),(120,180):(60,90),(180,9999):(85,110)},
    "Lopen":        {(0,60):(0,0),(60,90):(30,60),(90,180):(60,90),(180,9999):(75,90)},
    "Duatlon":      {(0,60):(0,0),(60,120):(30,60),(120,9999):(60,90)},
    "Triatlon":     {(0,90):(0,0),(90,180):(60,90),(180,9999):(80,110)},
    "Crosstriatlon":{(0,90):(0,0),(90,180):(60,90),(180,9999):(75,100)},
}

def _get_richtlijn(sport, duur_min):
    ranges = KH_TARGETS.get(sport, KH_TARGETS["Fietsen"])
    for (lo, hi), (mn, mx) in ranges.items():
        if lo <= duur_min < hi:
            return mn, mx
    return 0, 0

# ── Fases per sport ───────────────────────────────────────────────────────────
# Enkelvoudig: 1 fase
# Multisport: meerdere fases met eigen naam en toegelaten producttypes
SPORT_FASES = {
    "Fietsen":      [{"naam":"Fietsen",    "icon":"🚴", "toegelaten":["Gel","Sportdrank","Vast voedsel","Cafeïnegel","Supplement"]}],
    "Lopen":        [{"naam":"Lopen",      "icon":"🏃", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]}],
    "Triatlon":     [
        {"naam":"Fietsgedeelte", "icon":"🚴", "toegelaten":["Gel","Sportdrank","Vast voedsel","Cafeïnegel","Supplement"]},
        {"naam":"Loopgedeelte",  "icon":"🏃", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
        {"naam":"Combinatie",    "icon":"🏊🚴🏃","toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
    ],
    "Duatlon":      [
        {"naam":"Fietsgedeelte", "icon":"🚴", "toegelaten":["Gel","Sportdrank","Vast voedsel","Cafeïnegel","Supplement"]},
        {"naam":"Eerste loop",   "icon":"🏃", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
        {"naam":"Tweede loop",   "icon":"🏃", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
        {"naam":"Combinatie",    "icon":"🏃🚴","toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
    ],
    "Crosstriatlon":[
        {"naam":"Fietsgedeelte", "icon":"🚵", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
        {"naam":"Loopgedeelte",  "icon":"🏃", "toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
        {"naam":"Combinatie",    "icon":"🚵🏃","toegelaten":["Gel","Sportdrank","Cafeïnegel","Supplement"]},
    ],
}

# ── Productwaarschuwingen per sport ───────────────────────────────────────────
SPORT_PRODUCT_WAARSCHUWINGEN = {
    "Lopen": {
        "Vast voedsel": ("⚠️", "#ef4444", "Vast voedsel wordt sterk afgeraden bij lopen — schokbelasting verhoogt maagklachten sterk."),
    },
    "Crosstriatlon": {
        "Vast voedsel": ("⚠️", "#ef4444", "Offroad en trail verhogen de schokbelasting — vast voedsel is risicovol."),
    },
    "Triatlon": {
        "Vast voedsel": ("💡", "#fbbf24", "Vast voedsel enkel testen tijdens het fietsgedeelte, nooit tijdens het lopen."),
    },
    "Duatlon": {
        "Vast voedsel": ("💡", "#fbbf24", "Vast voedsel enkel tijdens de fiets — niet tijdens de eerste of tweede loop."),
    },
}

# ── Sport-specifieke producttips ──────────────────────────────────────────────
SPORT_PRODUCT_TIPS = {
    "Fietsen": {
        "icon": "🚴",
        "intro": "Op de fiets heb je de meeste vrijheid qua voeding — geen loopimpact op de maag.",
        "tips": [
            ("✅", "Vast voedsel werkt goed", "Rijstwafels, repen en bananen zijn ideaal op de fiets."),
            ("✅", "Sportdrank als basis", "Vul je bidons met sportdrank voor constante KH-inname."),
            ("✅", "Gels als aanvulling", "Gebruik gels bij hogere intensiteit of als vast voedsel moeilijk gaat."),
            ("💡", "Grote variatie mogelijk", "Omdat je zit en niet loopt, verdraagt de maag meer verschillende producten."),
        ]
    },
    "Lopen": {
        "icon": "🏃",
        "intro": "Bij lopen staat de maag onder druk door de schokbelasting — kies eenvoudig en bewezen.",
        "tips": [
            ("⚠️", "Vermijd vast voedsel", "De loopbeweging verhoogt de kans op maagklachten bij vast voedsel sterk."),
            ("✅", "Gels + water is de gouden combinatie", "Neem elke gel altijd in met minstens 150ml water."),
            ("💡", "Kleine frequente porties", "Liever 3x een kleine portie per uur dan 1x een grote."),
        ]
    },
    "Triatlon": {
        "icon": "🏊🚴🏃",
        "intro": "Bij triatlon wissel je van discipline — stem je voeding af per segment.",
        "tips": [
            ("ℹ️", "Zwemmen: geen voeding mogelijk", "Start vroeg op de fiets met inname — je maag is nog fris."),
            ("✅", "Fietsgedeelte: maximale inname", "Vast voedsel, sportdrank én gels zijn hier allemaal mogelijk."),
            ("⚠️", "Loopgedeelte: enkel vloeibaar", "Geen vast voedsel meer na de wissel — enkel gels en sportdrank."),
            ("💡", "Overgang fiets→lopen", "Laatste inname op fiets minstens 10 min voor T2."),
        ]
    },
    "Duatlon": {
        "icon": "🏃🚴",
        "intro": "Bij duatlon begin en eindig je met lopen — plan je voeding per segment.",
        "tips": [
            ("⚠️", "Eerste loop: licht houden", "Enkel gels en sportdrank — de maag is nog koud."),
            ("✅", "Fietsgedeelte: ideaal moment", "Dit is je beste kans voor hogere KH-inname — vast voedsel mag hier."),
            ("⚠️", "Tweede loop: enkel vloeibaar", "De maag is al vermoeid — beperk je tot gels en kleine slokjes."),
            ("💡", "Timing is alles", "Laatste vaste voeding minstens 15 min voor het einde van de fiets."),
        ]
    },
    "Crosstriatlon": {
        "icon": "🚵",
        "intro": "Offroad en trail verhogen de schokbelasting — wees extra voorzichtig.",
        "tips": [
            ("⚠️", "Vermijd vast voedsel", "De oneven ondergrond maakt vast voedsel risicovol."),
            ("✅", "Enkel vloeibaar en isotone gels", "Kies goed verteerbare, isotone producten."),
            ("⚠️", "Geen nieuwe producten op offroad", "Test altijd eerst op de weg."),
            ("💡", "Hydratatie is prioriteit", "Bij cross is regelmatig drinken moeilijker — train dit bewust in."),
        ]
    },
}

# ── Week 1 sport-specifieke tips ─────────────────────────────────────────────
WEEK1_SPORT_TIPS = {
    "Fietsen":      "Test tijdens een rustige Z2 rit van 90-120 min. Eerste portie na 20 min — niet wachten op honger.",
    "Lopen":        "Test tijdens een Z2 loopduur van 60-90 min. Gels om de 20-30 min. Loop rustig genoeg om te kunnen eten.",
    "Triatlon":     "Test enkel het fietsgedeelte in fase 1. Simuleer inname alsof je net uit het water komt — start vroeg.",
    "Duatlon":      "Start met de fiets in fase 1. Eerste loopgedeelte bewust licht — geen voeding testen tijdens loop in fase 1.",
    "Crosstriatlon":"Test op een vlakke weg, niet offroad. Bouw eerst basiscomfort op voor je naar crossomstandigheden gaat.",
}

SPORT_START_PCT = {
    "Fietsen": 0.40, "Lopen": 0.30, "Triatlon": 0.35,
    "Duatlon": 0.35, "Crosstriatlon": 0.35,
}
FASE_INTENSITEIT = {
    "opbouw": "Z2 — Duurtraining",
    "midden": "Z3 — Tempo",
    "finale": "Z4 — Drempeltraining",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HULPFUNCTIES
# ═══════════════════════════════════════════════════════════════════════════════

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


def _week_tip(fase_naam, porties, kh_doel, sport):
    """Geeft een contextgevoelige tip op basis van fase en porties."""
    if porties == 1:
        return f"Start met 1 portie — observeer goed hoe je maag reageert tijdens {fase_naam.lower()}."
    elif porties == 2:
        return f"Spreid de 2 porties gelijkmatig over het uur — niet te dicht op elkaar."
    else:
        return f"Bij {porties} porties per uur is timing cruciaal — elke portie met minstens 150ml water."


def _bereken_startpunt(data: dict) -> int:
    """
    Bereken startpunt KH/uur voor week 1.
    'Nooit last' + ervaring → vertrek van huidige inname bij 5+ wedstrijden.
    """
    maag     = data.get("maag_gevoelig", "Af en toe")
    ervaring = data.get("ervaring", "Nog nooit")
    sport    = data.get("sport", "Fietsen")
    inname   = int(data.get("huidige_inname", 0))
    target   = int(data.get("target_kh", 60))
    temp     = data.get("temp", 16)
    hoogte   = data.get("hoogte", 0)

    if maag == "Altijd met sportvoeding":
        start = 10
    elif maag == "Nooit":
        if ervaring == "Nog nooit":
            start = round(target * 0.40)
        elif ervaring == "2-4 wedstrijden":
            start = round(target * 0.55)
        elif ervaring == "5-10 wedstrijden":
            start = min(inname, round(target * 0.80))
        else:
            start = min(inname, round(target * 0.90))
    else:  # Af en toe
        if ervaring == "Nog nooit":
            start = round(target * 0.30)
        elif ervaring == "2-4 wedstrijden":
            start = round(target * 0.45)
        elif ervaring == "5-10 wedstrijden":
            start = min(round(inname * 0.60), round(target * 0.70))
        else:
            start = min(round(inname * 0.70), round(target * 0.80))

    if sport in ["Lopen", "Crosstriatlon"]:
        start = max(10, start - 5)
    if temp > 28:
        start = max(10, start - 5)
    if hoogte > 2000:
        start = max(10, start - 5)

    return round(start / 5) * 5


def _bereken_start_porties(start_kh: int, basis_kh: int, test_kh: int) -> int:
    """
    Bereken startaantal porties testproduct.
    Trekt eerst de basis-KH af, rest wordt gedeeld door kh per testportie.
    Minimum 1 portie.
    """
    netto = max(0, start_kh - basis_kh)
    if test_kh <= 0:
        return 1
    return max(1, round(netto / test_kh))


def _bereken_volgende_porties(prev_porties: int, score: int,
                               heeft_klachten: bool, max_porties: int) -> int:
    """
    Portie-gebaseerde progressie op basis van score.
    Opbouw in echte porties — geen grammen meer.
    """
    if score == 5 and not heeft_klachten:
        delta = 1        # snel vooruit
    elif score == 4 and not heeft_klachten:
        delta = 1        # normaal vooruit
    elif score == 3 and not heeft_klachten:
        delta = 0        # herhalen
    elif score == 3 and heeft_klachten:
        delta = 0        # herhalen
    elif score == 2:
        delta = -1       # terugschakelen
    else:                # score 1
        delta = -1       # terugschakelen

    nieuw = prev_porties + delta
    return max(1, min(nieuw, max_porties))


def _is_fase_stabiel(logs: dict, fase_sleutel: str) -> bool:
    """
    Een fase is stabiel (= afgerond) als de laatste 2 ingevulde weken
    van die fase allebei score >= 4 hadden én geen klachten.
    """
    fase_logs = {k: v for k, v in logs.items()
                 if v.get("fase") == fase_sleutel and v.get("ingevuld")}
    if len(fase_logs) < 2:
        return False
    gesorteerd = sorted(fase_logs.items(), key=lambda x: int(x[0]))
    laatste2   = [v for _, v in gesorteerd[-2:]]
    return all(
        l.get("score", 0) >= 4 and l.get("symptoom","") in ["","Geen klachten"]
        for l in laatste2
    )


def _actieve_fase_idx(sport: str, logs: dict) -> int:
    """Geeft de index van de huidige actieve fase terug."""
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])
    for i, fase in enumerate(fases):
        sleutel = fase["naam"]
        if not _is_fase_stabiel(logs, sleutel):
            return i
    return len(fases) - 1  # alles afgerond, blijf op laatste


def _volgende_week_nr(logs: dict) -> int:
    """Geeft het volgende weeknummer (hoogste ingevulde + 1, min 1)."""
    if not logs:
        return 1
    ingevulde = [int(k) for k, v in logs.items() if v.get("ingevuld")]
    return max(ingevulde) + 1 if ingevulde else 1


def _genereer_tips(data: dict) -> list:
    """Genereer persoonlijke tips op basis van profiel."""
    tips = []
    klachten    = data.get("klachten_lijst",[])
    klachten_p  = data.get("klachten_producten","").lower()
    maaltijd    = data.get("laatste_maaltijd","").lower()
    uren        = data.get("uren_voor_start",3)
    vocht       = data.get("vocht_voor_start",500)
    temp        = data.get("temp",16)
    hoogte      = data.get("hoogte",0)
    vochtigheid = data.get("vochtigheid",60)
    eetmom      = data.get("eetmomenten",2)
    drinkmom    = data.get("drinkmomenten",2)

    if "Misselijkheid" in klachten:
        tips.append("⚠️ Bij misselijkheid: verlaag de concentratie van je sportdrank en spreid innamen meer.")
    if "Krampen" in klachten:
        tips.append("⚠️ Bij krampen: neem producten altijd in met voldoende water (min. 150ml per gel).")
    if "Opgeblazen gevoel" in klachten:
        tips.append("⚠️ Bij opgeblazen gevoel: vermijd koolzuurhoudende dranken en controleer het fructosegehalte.")
    if "Diarree" in klachten:
        tips.append("⚠️ Bij diarree: vermijd hoge fructose en te geconcentreerde oplossingen.")
    if any(w in klachten_p for w in ["gel","geconcentreerd"]):
        tips.append("💡 Overweeg isotone gels of verdun geconcentreerde gels met extra water.")
    if "fructose" in klachten_p:
        tips.append("💡 Kies producten met enkel glucose of een lage fructose-glucoseverhouding.")
    if any(w in maaltijd for w in ["vet","kaas","vlees","ei","room","boter","noten"]):
        tips.append("🍽️ Je laatste maaltijd bevat mogelijk te veel vet. Kies voor koolhydraatrijke, vetarme voeding.")
    if any(w in maaltijd for w in ["groente","salade","broccoli","vezels","fruit"]):
        tips.append("🍽️ Beperk vezels en rauwe groenten in je laatste maaltijd.")
    if uren < 3:
        tips.append(f"⏰ Je eet de laatste maaltijd {uren}u voor de start — probeer dit naar 2.5–3u te vervroegen.")
    if vocht < 400:
        tips.append("💧 Je drinkt te weinig voor de wedstrijd. Streef naar 500ml water 2u voor de start.")
    if vocht > 1000:
        tips.append("💧 Meer dan 1000ml voor de start verhoogt het risico op hyponatriëmie.")
    if temp > 28:
        tips.append("🌡️ Bij temperaturen boven 28°C: prioriteit gaat naar vocht. Voeg ORS toe.")
    if hoogte > 2000:
        tips.append("🏔️ Boven 2000m daalt de eetlust. Start met vloeibare KH en bouw extra traag op.")
    if vochtigheid > 80:
        tips.append("💦 Hoge luchtvochtigheid: voeg extra natrium toe en verhoog je vochtinname per uur.")
    if eetmom == 1:
        tips.append("🍌 Je eet 1x per uur — dit zijn grote porties. Verdeel over 2-3 momenten.")
    if drinkmom == 1:
        tips.append("🥤 Je drinkt 1x per uur — grote slokken verhogen maagklachten.")
    if eetmom == 3:
        tips.append("✅ 3 eetmomenten per uur is optimaal voor maagontlediging.")
    if drinkmom == 3:
        tips.append("✅ 3 drinkmomenten per uur bevordert optimale hydratatie.")
    return tips


# ═══════════════════════════════════════════════════════════════════════════════
# STAPPEN
# ═══════════════════════════════════════════════════════════════════════════════

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
        ("2","Producten","Gels, sportdranken of vast voedsel — met rol (basis/test)"),
        ("3","Schema","Fase per fase testschema — dynamisch op basis van jouw scores"),
        ("4","Dagboek","Na elke training score en symptomen invullen"),
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


def _stap_profiel():
    _sectie("JOUW TRAININGSPROFIEL")
    data       = st.session_state.get("tg_data", {})
    ERV_OPTIES = ["Nog nooit","2-4 wedstrijden","5-10 wedstrijden","Meer dan 10 wedstrijden"]

    c1, c2 = st.columns(2)
    with c1:
        sport = st.selectbox("Sport", SPORTEN,
                              index=SPORTEN.index(data.get("sport","Fietsen")),
                              key="tg_sport")

        test_discipline = data.get("test_discipline", "Beide")
        if sport in MULTISPORT:
            test_discipline = st.radio(
                "Wil je je voeding testen voor:",
                ["Lopen", "Fietsen", "Beide"],
                index=["Lopen", "Fietsen", "Beide"].index(
                    data.get("test_discipline", "Beide")),
                key="tg_test_discipline", horizontal=True,
                help="Bij multisport kan je per discipline je voedingsstrategie testen.")

        wedstrijd_datum = st.date_input("Wedstrijddatum",
                                         value=date.fromisoformat(data.get("wedstrijd_datum",
                                             str(date.today() + timedelta(weeks=8)))),
                                         key="tg_wedstrijddatum")
        import re as _re
        wd_raw = st.text_input("Geschatte wedstrijdduur (bv. 3u15 of 2u30)",
                                value=data.get("wedstrijd_duur_str",""),
                                placeholder="bijv. 3u15", key="tg_wd_raw")
        _m = _re.match(r"(\d+)u(\d+)?", wd_raw.strip().lower())
        wedstrijd_duur = int(_m.group(1))*60 + int(_m.group(2) or 0) if _m \
                         else int(data.get("wedstrijd_duur",180))

        if wd_raw.strip() and wedstrijd_duur > 0 and wedstrijd_duur < 90:
            st.markdown("""
            <div style="background:#1e1a0f;border:1px solid #fbbf24;border-radius:8px;
                        padding:10px 14px;margin-top:6px;font-size:0.82rem;color:#fbbf24;
                        line-height:1.6;">
                ⚠️ <b>Train the Gut is niet noodzakelijk voor inspanningen korter dan 90 minuten.</b><br>
                <span style="color:#94a3b8;">Bij kortere wedstrijden volstaat het maag-darmstelsel
                zonder specifieke training.</span>
            </div>
            """, unsafe_allow_html=True)

        ervaring  = st.selectbox("Ervaring met wedstrijdvoeding", ERV_OPTIES,
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
        st.markdown(f'<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">'
                    f'Richtlijn literatuur: <b style="color:#f8fafc;">{kh_min_r}–{kh_max_r}g/uur</b></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">'
                    'Richtlijn literatuur: <b style="color:#f8fafc;">geen extra KH nodig</b></div>',
                    unsafe_allow_html=True)

    klachten_producten = data.get("klachten_producten","")
    klachten_lijst     = data.get("klachten_lijst",[])
    laatste_maaltijd   = data.get("laatste_maaltijd","")
    uren_voor_start    = data.get("uren_voor_start",3)
    vocht_voor_start   = data.get("vocht_voor_start",500)

    if maag_gevoelig in ["Altijd met sportvoeding","Af en toe"]:
        kleur_s = "#ef4444" if maag_gevoelig=="Altijd met sportvoeding" else "#fbbf24"
        _sectie("MAAGKLACHTEN BIJ VORIGE WEDSTRIJDEN", kleur_s)
        st.markdown('<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:10px;">'
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
        profiel_data = {
            "sport": sport, "maag_gevoelig": maag_gevoelig, "ervaring": ervaring,
            "huidige_inname": huidige_inname, "target_kh": target_kh,
            "temp": temp, "hoogte": hoogte,
        }
        start_kh = _bereken_startpunt(profiel_data)
        st.session_state.tg_data = {
            "sport": sport, "target_kh": target_kh,
            "niveau": niveau, "ervaring": ervaring,
            "test_discipline": test_discipline,
            "wedstrijd_datum": str(wedstrijd_datum),
            "wedstrijd_duur": wedstrijd_duur, "wedstrijd_duur_str": wd_raw,
            "maag_gevoelig": maag_gevoelig, "huidige_inname": huidige_inname,
            "eetmomenten": eetmomenten, "drinkmomenten": drinkmomenten,
            "klachten_producten": klachten_producten, "klachten_lijst": klachten_lijst,
            "laatste_maaltijd": laatste_maaltijd, "uren_voor_start": uren_voor_start,
            "vocht_voor_start": vocht_voor_start, "wedstrijd_plaats": wedstrijd_plaats,
            "temp": temp, "hoogte": hoogte, "vochtigheid": vochtigheid,
            "start_kh": start_kh,
        }
        st.session_state.tg_stap = 3
        st.rerun()


def _stap_producten():
    _sectie("TE TESTEN PRODUCTEN")
    data  = st.session_state.get("tg_data", {})
    sport = data.get("sport", "Fietsen")
    opgeslagen = data.get("producten", [{"naam":"","type":"Gel","kh":22,"rol":"Test"}])
    n = st.session_state.get("tg_n_prod", len(opgeslagen))

    # Sport-specifieke producttips
    sport_tips = SPORT_PRODUCT_TIPS.get(sport)
    if sport_tips:
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;
                    padding:16px;margin-bottom:16px;">
            <div style="font-size:0.72rem;font-weight:700;color:#f97316;letter-spacing:2px;
                        margin-bottom:10px;">{sport_tips['icon']} PRODUCTTIPS VOOR {sport.upper()}</div>
            <div style="font-size:0.82rem;color:#94a3b8;margin-bottom:12px;font-style:italic;">
                {sport_tips['intro']}</div>
        """, unsafe_allow_html=True)
        for icoon, titel, uitleg in sport_tips["tips"]:
            kleur_map = {"✅":"#22c55e","⚠️":"#fbbf24","💡":"#3b82f6","ℹ️":"#64748b"}
            kleur = kleur_map.get(icoon, "#94a3b8")
            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #1e293b;">
                <div style="font-size:1rem;flex-shrink:0;">{icoon}</div>
                <div><span style="font-weight:700;color:{kleur};font-size:0.82rem;">{titel}</span>
                <span style="color:#64748b;font-size:0.8rem;"> — {uitleg}</span></div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Uitleg rolverdeling
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                padding:12px 16px;margin-bottom:14px;font-size:0.82rem;color:#94a3b8;">
        <b style="color:#f8fafc;">Rol per product:</b><br>
        🔵 <b style="color:#3b82f6;">Basis</b> — vaste inname per sessie (bijv. sportdrank in bidon) — KH telt mee maar bouwt niet op.<br>
        🟠 <b style="color:#f97316;">Test</b> — bouwt op in porties week per week — dit is het product dat je traint.
    </div>
    """, unsafe_allow_html=True)

    h1,h2,h3,h4,h5 = st.columns([3,2,1,1,1])
    for col, lbl in [(h1,"Product naam"),(h2,"Type"),(h3,"KH/portie"),(h4,"Rol"),(h5,"")]:
        col.markdown(f'<div style="font-size:10px;color:#64748b;">{lbl}</div>',
                     unsafe_allow_html=True)

    producten      = []
    heeft_basis    = any(p.get("rol","Test")=="Basis" for p in opgeslagen[:n])
    waarschuwingen = SPORT_PRODUCT_WAARSCHUWINGEN.get(sport, {})

    for i in range(n):
        p = opgeslagen[i] if i < len(opgeslagen) else {"naam":"","type":"Gel","kh":22,"rol":"Test"}
        c1,c2,c3,c4,c5 = st.columns([3,2,1,1,1])
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
            # Basis enkel mogelijk als nog geen ander basisproduct gekozen
            huidig_rol  = p.get("rol","Test")
            andere_basis = any(
                st.session_state.get(f"tg_prol_{j}", "Test") == "Basis"
                for j in range(n) if j != i
            )
            rol_opties = ["Test","Basis"] if not andere_basis or huidig_rol=="Basis" else ["Test"]
            rol = st.selectbox(f"r{i}", rol_opties,
                                index=rol_opties.index(huidig_rol) if huidig_rol in rol_opties else 0,
                                key=f"tg_prol_{i}", label_visibility="collapsed")
        with c5:
            if n > 1 and st.button("✕", key=f"tg_pdel_{i}"):
                st.session_state["tg_n_prod"] = n - 1
                st.rerun()
        producten.append({"naam":naam,"type":ptype,"kh":kh,"rol":rol})

        # Productwaarschuwing direct onder de rij
        if ptype in waarschuwingen:
            icoon, kleur, tekst = waarschuwingen[ptype]
            st.markdown(f"""
            <div style="background:#0f172a;border-left:3px solid {kleur};
                        border-radius:0 6px 6px 0;padding:6px 12px;
                        margin:-4px 0 8px 0;font-size:0.78rem;color:{kleur};">
                {icoon} {tekst}
            </div>""", unsafe_allow_html=True)

    if st.button("＋ Product toevoegen", key="tg_padd"):
        st.session_state["tg_n_prod"] = n + 1
        st.rerun()

    # Samenvatting KH-verdeling
    gevulde = [p for p in producten if p["naam"]]
    if gevulde:
        basis_kh = sum(p["kh"] for p in gevulde if p["rol"]=="Basis")
        test_prod = [p for p in gevulde if p["rol"]=="Test"]
        if basis_kh > 0:
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                        padding:10px 14px;margin-top:8px;font-size:0.8rem;color:#94a3b8;">
                🔵 Basis KH (vast per sessie): <b style="color:#3b82f6;">{basis_kh}g/uur</b><br>
                🟠 Test KH (bouwt op): <b style="color:#f97316;">
                {" + ".join(f"{p['naam']} ({p['kh']}g/portie)" for p in test_prod) or "—"}
                </b>
            </div>""", unsafe_allow_html=True)

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
            elif not any(p["rol"]=="Test" for p in gevulde):
                st.error("Voeg minstens 1 testproduct toe.")
            else:
                st.session_state.tg_data["producten"] = gevulde
                st.session_state.tg_stap = 4
                st.rerun()


def _stap_schema():
    """Fase-gebaseerd schema — geen vaste weekslimiet."""
    _sectie("TESTSCHEMA")
    data  = st.session_state.get("tg_data", {})
    logs  = st.session_state.get("tg_logs", {})
    sport = data.get("sport", "Fietsen")
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])

    producten  = [p for p in data.get("producten",[]) if p.get("naam")]
    basis_prod = next((p for p in producten if p.get("rol")=="Basis"), None)
    test_prods = [p for p in producten if p.get("rol")=="Test"]
    basis_kh   = basis_prod["kh"] if basis_prod else 0
    target_kh  = int(data.get("target_kh", 60))
    start_kh   = int(data.get("start_kh", 20))
    eetmom     = int(data.get("eetmomenten", 2))

    # Week 1 preview
    if test_prods:
        prod1    = test_prods[0]
        kh_pp1   = prod1["kh"]
        porties1 = _bereken_start_porties(start_kh, basis_kh, kh_pp1)
        kh_tot1  = basis_kh + porties1 * kh_pp1
        interval1 = max(10, round(60 / max(eetmom, porties1) / 5) * 5)
        tijden1   = " → ".join([f"+{interval1*i}min" for i in range(1,porties1+1)]) \
                    if porties1 > 1 else f"+{interval1}min na start"
        pct1      = round((kh_tot1 / max(target_kh,1)) * 100)
        maag      = data.get("maag_gevoelig","Af en toe")
        ervaring  = data.get("ervaring","Nog nooit")
        if maag=="Nooit" and ervaring in ["5-10 wedstrijden","Meer dan 10 wedstrijden"]:
            start_uitleg = f"Gebaseerd op jouw huidige inname van {data.get('huidige_inname',0)}g/uur"
        elif maag=="Altijd met sportvoeding":
            start_uitleg = "Voorzichtig gestart — maag is gevoelig"
        else:
            start_uitleg = "Berekend op basis van ervaring en maagprofiel"

        basis_blok = ""
        if basis_prod:
            bp_naam = basis_prod["naam"]
            basis_blok = (
                f'<div style="background:#0f172a;border-radius:8px;padding:10px 12px;'
                f'margin-bottom:10px;font-size:0.78rem;color:#64748b;">'
                f'🔵 Basis: <b style="color:#3b82f6;">{bp_naam} — {basis_kh}g/uur (vast)</b></div>'
            )
        week1_tip = WEEK1_SPORT_TIPS.get(sport, "")
        prod1_naam = prod1["naam"]
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0f172a,#1e1a2e);'
            f'border:2px solid #3b82f6;border-radius:14px;padding:20px;margin-bottom:20px;">'
            f'<div style="font-size:0.65rem;font-weight:700;color:#3b82f6;'
            f'letter-spacing:2px;margin-bottom:14px;">🚀 JOUW STARTPUNT — WEEK 1</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">'
            f'<div style="background:#0f172a;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:1.6rem;font-weight:800;color:#3b82f6;">{kh_tot1}g</div>'
            f'<div style="font-size:11px;color:#64748b;">KH per uur totaal</div>'
            f'<div style="font-size:10px;color:#475569;margin-top:4px;">{pct1}% van target</div>'
            f'</div>'
            f'<div style="background:#0f172a;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:1.6rem;font-weight:800;color:#f97316;">{porties1}x</div>'
            f'<div style="font-size:11px;color:#64748b;">{prod1_naam}</div>'
            f'<div style="font-size:10px;color:#475569;margin-top:4px;">{kh_pp1}g KH/portie</div>'
            f'</div>'
            f'<div style="background:#0f172a;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:1.6rem;font-weight:800;color:#22c55e;">Z2</div>'
            f'<div style="font-size:11px;color:#64748b;">Intensiteit</div>'
            f'<div style="font-size:10px;color:#475569;margin-top:4px;">Duurtraining</div>'
            f'</div></div>'
            f'{basis_blok}'
            f'<div style="background:#0f172a;border-radius:8px;padding:12px;margin-bottom:12px;">'
            f'<div style="font-size:10px;color:#64748b;margin-bottom:6px;">INNAMETIJDSTIPPEN TESTPRODUCT</div>'
            f'<div style="font-size:0.85rem;font-weight:700;color:#f8fafc;">📍 {tijden1}</div>'
            f'<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">'
            f'Elke {interval1} minuten — altijd met minstens 150ml water</div>'
            f'</div>'
            f'<div style="background:#0a1628;border-left:3px solid #3b82f6;'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px;">'
            f'<div style="font-size:0.78rem;color:#94a3b8;">'
            f'💡 <b style="color:#f8fafc;">Waarom dit startpunt?</b> {start_uitleg}</div>'
            f'</div>'
            f'<div style="background:#0a1628;border-left:3px solid #f97316;'
            f'border-radius:0 8px 8px 0;padding:10px 14px;">'
            f'<div style="font-size:0.78rem;color:#94a3b8;">'
            f'🏅 <b style="color:#f8fafc;">Tip week 1:</b> {week1_tip}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

    # Persoonlijke tips
    tips = _genereer_tips(data)
    if tips:
        _sectie("PERSOONLIJKE TIPS", "#fbbf24")
        for tip in tips:
            st.markdown(
                f'<div style="background:#0f172a;border:1px solid #fbbf24;border-radius:8px;'
                f'padding:10px 14px;font-size:0.82rem;color:#f1f5f9;margin-bottom:6px;">{tip}</div>',
                unsafe_allow_html=True)

    # Fase-overzicht
    _sectie("SCHEMA PER FASE")
    actieve_fase_idx = _actieve_fase_idx(sport, logs)

    fase_kleuren = ["#3b82f6","#f97316","#8b5cf6","#22c55e"]

    for fi, fase in enumerate(fases):
        fase_naam   = fase["naam"]
        fase_icon   = fase["icon"]
        fase_kleur  = fase_kleuren[fi % len(fase_kleuren)]
        stabiel     = _is_fase_stabiel(logs, fase_naam)
        actief      = fi == actieve_fase_idx
        gelockt     = fi > actieve_fase_idx

        # Fase header
        status = "✅ Afgerond" if stabiel else ("📝 Actief" if actief else "🔒 Nog niet gestart")
        status_kleur = "#22c55e" if stabiel else (fase_kleur if actief else "#334155")

        st.markdown(f"""
        <div style="background:#0f172a;border:2px solid {status_kleur};border-radius:12px;
                    padding:14px;margin-bottom:{'4' if actief else '12'}px;
                    {'opacity:0.5;' if gelockt else ''}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">{fase_icon}</span>
                    <span style="font-weight:800;color:#f8fafc;font-size:0.95rem;">{fase_naam}</span>
                </div>
                <span style="font-size:0.75rem;font-weight:700;color:{status_kleur};">{status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not gelockt:
            # Toon weken van deze fase
            fase_logs = {k: v for k, v in logs.items() if v.get("fase") == fase_naam}
            week_nrs  = sorted([int(k) for k in fase_logs.keys()])

            for wn in week_nrs:
                log_w    = logs.get(str(wn), {})
                ingevuld = log_w.get("ingevuld", False)
                porties  = log_w.get("porties", 1)
                prod_naam= log_w.get("product", "—")
                kh_pp    = log_w.get("kh_pp", 0)
                kh_tot   = basis_kh + porties * kh_pp
                pct      = round((kh_tot / max(target_kh,1)) * 100)
                interval = max(10, round(60 / max(eetmom, porties) / 5) * 5)
                innamen  = " → ".join([f"+{interval*i}min" for i in range(1,porties+1)]) \
                           if porties > 1 else f"+{interval}min"
                s        = log_w.get("score",0)
                sym      = log_w.get("symptoom","")

                st.markdown(f"""
                <div style="background:#0a0f1e;border:1px solid {'#22c55e' if ingevuld else fase_kleur};
                            border-radius:8px;padding:12px;margin-bottom:6px;margin-left:16px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                        <span style="font-weight:700;color:#f8fafc;">Week {wn}</span>
                        <span style="font-weight:800;color:{fase_kleur};">{kh_tot}g/uur</span>
                    </div>
                    <div style="background:#1e293b;border-radius:3px;height:4px;overflow:hidden;margin-bottom:8px;">
                        <div style="width:{min(pct,100)}%;height:100%;background:{fase_kleur};border-radius:3px;"></div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:0.75rem;color:#94a3b8;">
                        <div>🧪 <b style="color:#f8fafc;">{prod_naam}</b> — {porties}x {kh_pp}g</div>
                        <div>📍 {innamen}</div>
                        {"<div>Score: <b style='color:" + _score_kleur(s) + ";'>" + str(s) + "/5</b></div>" if ingevuld else ""}
                        {"<div>" + (sym if sym and sym!='Geen klachten' else '✅ Geen klachten') + "</div>" if ingevuld else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Knop voor volgende week in deze fase
            if actief and not stabiel:
                volgende_wn = _volgende_week_nr(logs)
                if st.button(f"📝 Week {volgende_wn} invullen — {fase_naam}",
                             key=f"goto_log_{fi}", use_container_width=True):
                    st.session_state["tg_actieve_week"] = volgende_wn
                    st.session_state["tg_actieve_fase"] = fase_naam
                    st.session_state.tg_stap = 5
                    st.rerun()

            if stabiel:
                st.markdown(f"""
                <div style="background:#0a1a0a;border:1px solid #22c55e;border-radius:8px;
                            padding:10px 14px;margin-bottom:8px;margin-left:16px;
                            font-size:0.8rem;color:#22c55e;">
                    ✅ <b>{fase_naam} afgerond</b> — 2 weken stabiel met score ≥ 4.
                    {"Fase " + fases[fi+1]["naam"] + " is nu beschikbaar." if fi+1 < len(fases) else "Alle fases afgerond — bekijk het rapport!"}
                </div>
                """, unsafe_allow_html=True)

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
    """Dagboek — portie-gebaseerd, fase-bewust."""
    _sectie("DAGBOEK")
    data  = st.session_state.get("tg_data", {})
    logs  = st.session_state.get("tg_logs", {})
    sport = data.get("sport", "Fietsen")
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])

    producten  = [p for p in data.get("producten",[]) if p.get("naam")]
    basis_prod = next((p for p in producten if p.get("rol")=="Basis"), None)
    test_prods = [p for p in producten if p.get("rol")=="Test"]
    basis_kh   = basis_prod["kh"] if basis_prod else 0
    target_kh  = int(data.get("target_kh", 60))
    eetmom     = int(data.get("eetmomenten", 2))

    actieve_week = st.session_state.get("tg_actieve_week", _volgende_week_nr(logs))
    actieve_fase = st.session_state.get("tg_actieve_fase",
                   fases[_actieve_fase_idx(sport, logs)]["naam"])
    log          = logs.get(str(actieve_week), {})

    # Bepaal testproduct voor deze week (wisselend per fase-week)
    fase_logs   = {k:v for k,v in logs.items() if v.get("fase")==actieve_fase and v.get("ingevuld")}
    prod_idx    = len(fase_logs) % len(test_prods) if test_prods else 0
    huidig_prod = test_prods[prod_idx] if test_prods else {"naam":"—","kh":22}

    # Bepaal porties op basis van vorige week in deze fase
    prev_fase_logs = sorted([(int(k),v) for k,v in fase_logs.items()], key=lambda x:x[0])
    if prev_fase_logs:
        prev_log     = prev_fase_logs[-1][1]
        prev_porties = prev_log.get("porties", 1)
        prev_score   = prev_log.get("score", 3)
        prev_klacht  = prev_log.get("symptoom","Geen klachten") != "Geen klachten"
        max_porties  = max(1, round(target_kh / max(huidig_prod["kh"],1)))
        huidig_porties = _bereken_volgende_porties(prev_porties, prev_score, prev_klacht, max_porties)
    else:
        start_kh       = int(data.get("start_kh", 20))
        huidig_porties = _bereken_start_porties(start_kh, basis_kh, huidig_prod["kh"])

    kh_tot   = basis_kh + huidig_porties * huidig_prod["kh"]
    interval = max(10, round(60 / max(eetmom, huidig_porties) / 5) * 5)
    pct      = round((kh_tot / max(target_kh,1)) * 100)

    # Header
    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;
                padding:14px;margin-bottom:16px;">
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:6px;">
            WEEK {actieve_week} — {actieve_fase.upper()}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-weight:800;color:#f8fafc;font-size:1rem;">
                    {huidig_prod['naam']}</div>
                <div style="font-size:0.78rem;color:#64748b;">
                    {huidig_porties}x {huidig_prod['kh']}g
                    {f"+ {basis_prod['naam']} {basis_kh}g basis" if basis_prod else ""}
                    = {kh_tot}g/uur totaal
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.4rem;font-weight:800;color:#f97316;">{kh_tot}g/uur</div>
                <div style="font-size:10px;color:#64748b;">{pct}% van target</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.82rem;color:#94a3b8;margin-bottom:14px;">'
                'Vul in hoe de training verliep. De volgende portie wordt automatisch '
                'aangepast op basis van je score.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        score = st.slider("Verdraagbaarheid (1=slecht — 5=uitstekend)",
                           1, 5, int(log.get("score", 3)), key=f"tg_score_{actieve_week}")
        st.markdown(
            f'<div style="font-size:0.8rem;color:{_score_kleur(score)};font-weight:700;">'
            f'{_score_label(score)}</div>', unsafe_allow_html=True)
    with c2:
        symptoom = st.selectbox("Symptomen", SYMPTOMEN,
                                 index=SYMPTOMEN.index(log.get("symptoom","Geen klachten")),
                                 key=f"tg_symp_{actieve_week}")

    int_uitg = st.selectbox("Werkelijk uitgevoerde intensiteit", INTENSITEITEN,
                             index=INTENSITEITEN.index(log.get("int_uitg","Z2 — Duurtraining"))
                             if log.get("int_uitg") in INTENSITEITEN else 1,
                             key=f"tg_int_{actieve_week}")

    c3, c4 = st.columns(2)
    with c3:
        temp_log = st.number_input("Temperatuur tijdens training (°C)", -5, 45,
                                    int(log.get("temp", 18)), 1, key=f"tg_temp_{actieve_week}")
    with c4:
        timing_ok = st.radio("Innamen op geplande tijdstip?",
                              ["Ja","Gedeeltelijk","Neen"],
                              index=["Ja","Gedeeltelijk","Neen"].index(log.get("timing_ok","Ja")),
                              key=f"tg_timing_{actieve_week}", horizontal=True)

    notitie = st.text_area("Notities", value=log.get("notitie",""),
                            key=f"tg_notitie_{actieve_week}", height=80,
                            placeholder="Hoe smaakte het? Maagklachten op welk moment?")

    actie = st.selectbox("Actie voor volgende week", [
        "Doorgaan met dit product",
        "Hoeveelheid verlagen en opnieuw testen",
        "Ander product testen",
        "Product schrappen"],
        index=["Doorgaan met dit product","Hoeveelheid verlagen en opnieuw testen",
               "Ander product testen","Product schrappen"].index(
            log.get("actie","Doorgaan met dit product")),
        key=f"tg_actie_{actieve_week}")

    # Preview volgende portie
    heeft_klachten = symptoom != "Geen klachten"
    max_porties    = max(1, round(target_kh / max(huidig_prod["kh"],1)))
    volgende_p     = _bereken_volgende_porties(huidig_porties, score, heeft_klachten, max_porties)
    volgende_kh    = basis_kh + volgende_p * huidig_prod["kh"]
    delta_p        = volgende_p - huidig_porties
    delta_kleur    = "#22c55e" if delta_p > 0 else ("#ef4444" if delta_p < 0 else "#fbbf24")
    delta_txt      = f"+{delta_p} portie(s)" if delta_p > 0 else \
                     (f"{delta_p} portie(s)" if delta_p < 0 else "zelfde aantal")

    stabiel_na_opslaan = False
    if score >= 4 and not heeft_klachten:
        prev2 = [v for _,v in sorted(
            [(int(k),v) for k,v in fase_logs.items()], key=lambda x:x[0]
        )]
        if prev2 and prev2[-1].get("score",0) >= 4 and \
           prev2[-1].get("symptoom","Geen klachten") == "Geen klachten":
            stabiel_na_opslaan = True

    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;
                padding:10px 14px;margin-top:12px;font-size:0.82rem;">
        📋 Volgende week: <b style="color:{delta_kleur};">{volgende_p} portie(s) = {volgende_kh}g/uur ({delta_txt})</b>
        {('<br><span style="color:#22c55e;font-size:0.78rem;">✅ Na opslaan is fase <b>' + actieve_fase + '</b> stabiel — volgende fase wordt ontgrendeld!</span>') if stabiel_na_opslaan else ""}
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"✅ Opslaan week {actieve_week}", key=f"tg_save_{actieve_week}",
                  use_container_width=True):
        if "tg_logs" not in st.session_state:
            st.session_state.tg_logs = {}
        st.session_state.tg_logs[str(actieve_week)] = {
            "score": score, "symptoom": symptoom, "int_uitg": int_uitg,
            "temp": temp_log, "timing_ok": timing_ok,
            "notitie": notitie, "actie": actie,
            "fase": actieve_fase,
            "product": huidig_prod["naam"],
            "kh_pp": huidig_prod["kh"],
            "porties": huidig_porties,
            "kh_doel": kh_tot,
            "ingevuld": True,
        }
        st.success(f"✅ Week {actieve_week} opgeslagen!")
        st.session_state["tg_actieve_week"] = actieve_week + 1
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
    data  = st.session_state.get("tg_data", {})
    logs  = st.session_state.get("tg_logs", {})
    sport = data.get("sport", "Fietsen")
    fases = SPORT_FASES.get(sport, SPORT_FASES["Fietsen"])

    ingevuld = [v for v in logs.values() if v.get("ingevuld")]
    if not ingevuld:
        st.warning("Nog geen trainingen gelogd.")
        if st.button("← Naar schema", key="tg_rep_back2"):
            st.session_state.tg_stap = 4
            st.rerun()
        return

    gem_score = sum(v["score"] for v in ingevuld) / len(ingevuld)
    max_kh    = max(v.get("kh_doel",0) for v in ingevuld)
    n_klacht  = sum(1 for v in ingevuld if v.get("symptoom","Geen klachten") != "Geen klachten")

    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                padding:18px;margin-bottom:18px;">
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:2px;margin-bottom:12px;">
            SAMENVATTING — {sport.upper()}</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
            <div style="text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:#f97316;">{len(ingevuld)}</div>
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
                <div style="font-size:1.6rem;font-weight:800;
                            color:{'#22c55e' if n_klacht==0 else '#fbbf24'}">{n_klacht}</div>
                <div style="font-size:11px;color:#64748b;">weken met klachten</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Per fase resultaten
    for fase in fases:
        fase_naam = fase["naam"]
        fase_logs = [v for v in ingevuld if v.get("fase")==fase_naam]
        if not fase_logs:
            continue
        stabiel = _is_fase_stabiel(logs, fase_naam)
        _sectie(f"{fase['icon']} {fase_naam.upper()}",
                "#22c55e" if stabiel else "#f97316")

        prod_data = {}
        for v in fase_logs:
            prod = v.get("product","—")
            if prod not in prod_data:
                prod_data[prod] = {"scores":[],"symptomen":[],"kh_max":0,"porties_max":0}
            prod_data[prod]["scores"].append(v["score"])
            prod_data[prod]["symptomen"].append(v.get("symptoom","Geen klachten"))
            prod_data[prod]["kh_max"]     = max(prod_data[prod]["kh_max"], v.get("kh_doel",0))
            prod_data[prod]["porties_max"]= max(prod_data[prod]["porties_max"], v.get("porties",0))

        aanbevolen = []
        vermijden  = []
        for prod, pd in prod_data.items():
            gem  = sum(pd["scores"]) / len(pd["scores"])
            ok   = gem >= 4.0
            kleur= _score_kleur(gem)
            symp = max(set(pd["symptomen"]), key=pd["symptomen"].count)
            if ok: aanbevolen.append(prod)
            else:  vermijden.append(prod)

            st.markdown(f"""
            <div style="background:#0f172a;border:2px solid {'#22c55e' if ok else '#ef4444'};
                        border-radius:10px;padding:12px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:800;color:#f8fafc;">{prod}</div>
                        <div style="font-size:11px;color:#64748b;">
                            max {pd['porties_max']} portie(s) · {pd['kh_max']}g KH/uur</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.2rem;font-weight:800;color:{kleur};">{gem:.1f}/5</div>
                        <div style="font-size:10px;color:{'#22c55e' if ok else '#ef4444'};">
                            {'✅ Aanbevolen' if ok else '❌ Vermijden'}</div>
                    </div>
                </div>
                <div style="font-size:0.75rem;color:#64748b;margin-top:6px;">
                    Meest voorkomend symptoom: <b style="color:#f8fafc;">{symp}</b></div>
            </div>
            """, unsafe_allow_html=True)

        if stabiel:
            st.markdown(f"""
            <div style="background:#0a1a0a;border:1px solid #22c55e;border-radius:8px;
                        padding:10px 14px;margin-bottom:12px;font-size:0.8rem;color:#22c55e;">
                ✅ <b>{fase_naam} stabiel</b> — aanbevolen producten: <b>{', '.join(aanbevolen) or '—'}</b>
            </div>""", unsafe_allow_html=True)

    # Eindadvies
    _sectie("AANBEVELING VOOR RACEDAG", "#22c55e")
    alle_aanbevolen = list({v.get("product") for v in ingevuld
                           if (sum(x["score"] for x in ingevuld
                                   if x.get("product")==v.get("product")) /
                               max(sum(1 for x in ingevuld
                                       if x.get("product")==v.get("product")),1)) >= 4.0})
    if alle_aanbevolen:
        st.success(f"✅ Goedgekeurde producten: **{', '.join(alle_aanbevolen)}**")
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #22c55e;border-radius:8px;
                    padding:14px;font-size:0.82rem;color:#94a3b8;line-height:1.7;margin-top:8px;">
            Je hebt aangetoond dat je maag <b style="color:#22c55e;">{max_kh}g KH/uur</b>
            verdraagt met geteste producten.<br>
            Gebruik <b style="color:#f8fafc;">enkel deze producten</b> op racedag.<br><br>
            🏁 Klaar om dit te integreren in je
            <b style="color:#f97316;">Race Nutrition Coach</b> raceplan.
        </div>""", unsafe_allow_html=True)
    else:
        st.warning("Nog geen producten met score ≥ 4. Ga verder met testen.")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Terug naar schema", key="tg_rep_back"):
            st.session_state.tg_stap = 4
            st.rerun()
    with c2:
        if st.button("🔄 Nieuw testschema", key="tg_nieuw", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("tg_"):
                    del st.session_state[k]
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# HOOFDFUNCTIE
# ═══════════════════════════════════════════════════════════════════════════════

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

    stap  = st.session_state.get("tg_stap", 1)
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
