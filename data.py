# ─── FOOD DATABASE ───────────────────────────────────────────────────────────
FOOD_DB = {
    # ONTBIJT
    "Wit Brood":          {"unit": "sneden",       "carbs": 15,    "grams": 35,  "type": "vast"},
    "Bruin Brood":        {"unit": "sneden",       "carbs": 14,    "grams": 35,  "type": "vast"},
    "Sandwich":           {"unit": "stuks",        "carbs": 18,    "grams": 45,  "type": "vast"},
    "Pistolet":           {"unit": "stuks",        "carbs": 26,    "grams": 60,  "type": "vast"},
    "Koffiekoek":         {"unit": "stuks",        "carbs": 35,    "grams": 80,  "type": "vast"},
    "Havermout":          {"unit": "soeplepels",   "carbs": 8,     "grams": 15,  "type": "vast"},
    "Ontbijtgranen":      {"unit": "portie",       "carbs": 30,    "grams": 40,  "type": "vast"},
    "Granola":            {"unit": "soeplepels",   "carbs": 12,    "grams": 20,  "type": "vast"},
    "Muesli":             {"unit": "soeplepels",   "carbs": 10,    "grams": 20,  "type": "vast"},
    "Banaan":             {"unit": "stuks",        "carbs": 25,    "grams": 150, "type": "vast"},
    "Yoghurt":            {"unit": "ml",           "carbs": 0.05,  "grams": 1,   "type": "vloeibaar"},
    "Platte kaas":        {"unit": "gram",         "carbs": 0.04,  "grams": 1,   "type": "vast"},
    "Melk":               {"unit": "ml",           "carbs": 0.048, "grams": 1,   "type": "vloeibaar"},
    "Sojamelk":           {"unit": "ml",           "carbs": 0.03,  "grams": 1,   "type": "vloeibaar"},
    "Jam/Confituur":      {"unit": "koffielp",     "carbs": 7,     "grams": 15,  "type": "vast"},
    "Chocopasta":         {"unit": "koffielp",     "carbs": 10,    "grams": 15,  "type": "vast"},
    "Honing":             {"unit": "koffielp",     "carbs": 6,     "grams": 10,  "type": "vast"},
    "Speculoospasta":     {"unit": "koffielp",     "carbs": 8,     "grams": 15,  "type": "vast"},
    # LUNCH & DINER
    "Rijst (bereid)":           {"unit": "eetlepels (23g)", "carbs": 6.4, "grams": 23,  "type": "vast"},
    "Pasta bijgerecht (150g)":  {"unit": "portie",          "carbs": 45,  "grams": 150, "type": "vast"},
    "Pasta hoofdgerecht (300g)":{"unit": "portie",          "carbs": 90,  "grams": 300, "type": "vast"},
    "Aardappelen":              {"unit": "stuks",           "carbs": 20,  "grams": 125, "type": "vast"},
    "Quinoa":                   {"unit": "soeplepels",      "carbs": 11,  "grams": 45,  "type": "vast"},
    "Couscous":                 {"unit": "soeplepels",      "carbs": 10,  "grams": 40,  "type": "vast"},
    "Wrap":                     {"unit": "stuks",           "carbs": 25,  "grams": 65,  "type": "vast"},
    "Appelmoes":                {"unit": "potje",           "carbs": 22,  "grams": 100, "type": "vast"},
    "Warme groentenmix":        {"unit": "gram",            "carbs": 0.08,"grams": 1,   "type": "vast"},
    "Koude groentenmix":        {"unit": "gram",            "carbs": 0.05,"grams": 1,   "type": "vast"},
    # TUSSENDOOR
    "Fruit":                {"unit": "stuks",      "carbs": 15,  "grams": 125, "type": "vast"},
    "Granenkoek":           {"unit": "stuks",      "carbs": 20,  "grams": 35,  "type": "vast"},
    "Noten/Zaden":          {"unit": "handvol",    "carbs": 4,   "grams": 25,  "type": "vast"},
    "Peperkoek":            {"unit": "sneden",     "carbs": 18,  "grams": 30,  "type": "vast"},
    "Rijstwafel":           {"unit": "stuks",      "carbs": 7,   "grams": 10,  "type": "vast"},
    "Gedroogde abrikozen":  {"unit": "stuks",      "carbs": 4,   "grams": 8,   "type": "vast"},
}

# ─── MEAL MOMENT CONFIGS ─────────────────────────────────────────────────────
MOMENT_CONFIGS = {
    "Ontbijt":       {"pct": 0.25,  "foods": ["Wit Brood","Bruin Brood","Sandwich","Pistolet","Koffiekoek","Jam/Confituur","Chocopasta","Honing","Speculoospasta","Havermout","Ontbijtgranen","Granola","Muesli","Banaan","Yoghurt","Platte kaas","Melk","Sojamelk"]},
    "Tussendoor VM": {"pct": 0.083, "foods": ["Fruit","Granenkoek","Noten/Zaden","Peperkoek","Rijstwafel","Gedroogde abrikozen","Banaan"]},
    "Lunch":         {"pct": 0.25,  "foods": ["Pasta bijgerecht (150g)","Pasta hoofdgerecht (300g)","Rijst (bereid)","Aardappelen","Wit Brood","Bruin Brood","Jam/Confituur","Honing","Chocopasta","Speculoospasta","Banaan","Warme groentenmix","Koude groentenmix"]},
    "Tussendoor NM": {"pct": 0.083, "foods": ["Fruit","Granenkoek","Noten/Zaden","Peperkoek","Rijstwafel","Gedroogde abrikozen","Banaan"]},
    "Avondmaal":     {"pct": 0.25,  "foods": ["Pasta bijgerecht (150g)","Pasta hoofdgerecht (300g)","Rijst (bereid)","Aardappelen","Wit Brood","Bruin Brood","Jam/Confituur","Honing","Chocopasta","Speculoospasta","Banaan","Warme groentenmix","Koude groentenmix"]},
    "Avond":         {"pct": 0.083, "foods": ["Fruit","Granenkoek","Noten/Zaden","Peperkoek","Rijstwafel","Gedroogde abrikozen","Banaan"]},
}

# ─── RACE PRODUCTS ────────────────────────────────────────────────────────────
RACE_PRODUCTS = {
    "gels": [
        {"name": "Standard Gel",    "kh": 25, "icon": "🧪"},
        {"name": "High Carb Gel",   "kh": 45, "icon": "🚀"},
        {"name": "Maurten Gel 100", "kh": 25, "icon": "🧪"},
        {"name": "SIS Beta Fuel",   "kh": 40, "icon": "🚀"},
    ],
    "cafe": [
        {"name": "Caffeine Gel",      "kh": 25, "icon": "⚡"},
        {"name": "Caffeine Gel High", "kh": 40, "icon": "💥"},
        {"name": "Maurten Caf 100",   "kh": 25, "icon": "⚡"},
    ],
    "vast": [
        {"name": "Banaan",       "kh": 25, "icon": "🍌"},
        {"name": "Energiereep",  "kh": 40, "icon": "🍫"},
        {"name": "Peperkoek",    "kh": 20, "icon": "🍞"},
        {"name": "Rijstbal",     "kh": 35, "icon": "🍙"},
        {"name": "Medjool dadel","kh": 18, "icon": "🌴"},
    ],
}

# ─── BOOST TIPS ───────────────────────────────────────────────────────────────
BOOST_TIPS = {
    "Ontbijt": [
        ("Extra lepel honing (+6g)",        "honing"),
        ("Glas appelsap 200ml (+20g)",       "appelsap"),
        ("Extra banaan (+25g)",              "banaan_extra"),
        ("Snee wit brood met jam (+22g)",    "wit_jam"),
    ],
    "Lunch": [
        ("Extra sandwich met stroop (+24g)", "stroop"),
        ("Beker drinkyoghurt 250ml (+25g)",  "drinkyoghurt"),
        ("Potje appelmoes (+22g)",           "appelmoes"),
        ("Extra wrap (+25g)",                "wrap_extra"),
    ],
    "Avondmaal": [
        ("Extra schep rijst/pasta (+12g)",   "rijst_pasta"),
        ("Glas limonade (+20g)",             "limonade"),
        ("Schaaltje sorbetijs (+30g)",       "sorbet"),
        ("Wit brood bij de maaltijd (+15g)", "brood_extra"),
    ],
    "Tussendoor": [
        ("Handvol Winegums (+25g)",              "winegums"),
        ("Blikje frisdrank 330ml (+35g)",        "cola"),
        ("Twee rijstwafels met honing (+20g)",   "rijstwafels"),
        ("Plak peperkoek (+18g)",                "peperkoek"),
        ("Sportdrank 500ml (+30g)",              "isotoon"),
        ("Gedroogde dadels 3 stuks (+18g)",      "dadels"),
    ],
}
