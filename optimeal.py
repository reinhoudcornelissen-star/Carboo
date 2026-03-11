import streamlit as st


def render_optimeal():
    st.markdown('<div class="section-title">🥗 OPTIMEAL — Dagelijkse Voedingsoptimalisatie</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e; padding:16px; 
         border-radius:12px; margin-bottom:24px; color:#86efac; font-size:0.9rem;">
        💡 OPTIMEAL analyseert je dagelijkse voedingsinname en geeft persoonlijke aanbevelingen 
        op basis van je trainingsbelasting, doelstelling en tijdstip van de dag.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        gewicht = st.number_input("Lichaamsgewicht (kg)", 30.0, 150.0, 70.0, 0.5)
        doelstelling = st.selectbox("Doelstelling", [
            "🏆 Prestatie optimaliseren",
            "⚖️ Gewicht handhaven",
            "📉 Gewicht verliezen",
            "💪 Spiermassa opbouwen",
        ])

    with col2:
        training_duur = st.number_input("Trainingsduur vandaag (uren)", 0.0, 8.0, 1.5, 0.25)
        training_type = st.selectbox("Type training", [
            "🔵 Rustig (Z1-Z2)",
            "🟡 Matig intensief (Z3)",
            "🔴 Intensief (Z4-Z5)",
            "⚫ Wedstrijd",
            "😴 Rustdag",
        ])

    with col3:
        timing = st.selectbox("Training timing", [
            "🌅 Ochtend (voor ontbijt)",
            "☀️ Voormiddag",
            "🌤️ Namiddag",
            "🌙 Avond",
        ])
        doel_kh = st.number_input("Extra koolhydraatvraag (g)", 0, 600, 0, 10, help="Los van de basisinname")

    # ─── BEREKENINGEN ────────────────────────────────────────────────────────
    if st.button("🔍 ANALYSEER VOEDINGSPLAN", key="optimeal_btn"):

        # Basis kcal (Harris-Benedict simplified)
        bmr = gewicht * 24

        # Activiteitsmultiplier
        if "Rustdag" in training_type:
            pal = 1.3
        elif "Rustig" in training_type:
            pal = 1.5 + (training_duur * 0.1)
        elif "Matig" in training_type:
            pal = 1.6 + (training_duur * 0.15)
        else:
            pal = 1.7 + (training_duur * 0.2)

        total_kcal = round(bmr * pal)

        # Macros
        kh_gram  = round(gewicht * (8 if "Wedstrijd" in training_type else 6 if "Intensief" in training_type else 4))
        prot_gram = round(gewicht * 1.6)
        vet_gram  = round((total_kcal - (kh_gram * 4) - (prot_gram * 4)) / 9)
        vet_gram  = max(vet_gram, round(gewicht * 0.8))

        st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)

        # Macro overzicht
        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, unit, color in [
            (m1, "TOTAAL KCAL", total_kcal, "kcal", "#f97316"),
            (m2, "KOOLHYDRATEN", kh_gram, "gram", "#3b82f6"),
            (m3, "EIWITTEN", prot_gram, "gram", "#22c55e"),
            (m4, "VETTEN", vet_gram, "gram", "#a78bfa"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-box" style="border-top:3px solid {color};">
                    <div style="font-size:0.65rem; color:#64748b; text-transform:uppercase; font-weight:700; margin-bottom:5px;">{label}</div>
                    <div style="font-size:1.6rem; font-weight:900; color:{color};">{val}</div>
                    <div style="font-size:0.75rem; color:#94a3b8;">{unit}</div>
                </div>
                """, unsafe_allow_html=True)

        # Timing aanbevelingen
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-weight:800; color:#22c55e; margin-bottom:12px;">⏰ TIMING AANBEVELINGEN</div>', unsafe_allow_html=True)

        aanbevelingen = _get_timing_tips(training_type, timing, kh_gram, prot_gram)
        for rec in aanbevelingen:
            st.markdown(f"""
            <div style="background:#f0fdf4; border-left:4px solid #22c55e; padding:12px 16px; 
                 border-radius:8px; margin-bottom:10px; color:#1e293b; font-size:0.87rem;">
                {rec}
            </div>
            """, unsafe_allow_html=True)

        # Hydratatie
        water = round(gewicht * 35 + training_duur * 600)
        st.markdown(f"""
        <div style="background:#eff6ff; border-left:4px solid #3b82f6; padding:12px 16px; 
             border-radius:8px; color:#1e3a8a; font-size:0.87rem; margin-top:10px;">
            💧 <b>Hydratatie target vandaag: {water}ml</b> — 
            ({round(gewicht * 35)}ml basis + {round(training_duur * 600)}ml training)
        </div>
        """, unsafe_allow_html=True)


def _get_timing_tips(training_type, timing, kh_gram, prot_gram):
    tips = []
    kh3 = round(kh_gram * 0.3)
    kh2 = round(kh_gram * 0.2)
    p30 = round(prot_gram * 0.25)

    if "Ochtend" in timing:
        tips += [
            f"🌅 <b>Pre-training (30-60min voor):</b> {kh2}g KH — rijstwafel met honing of banaan.",
            f"🔁 <b>Post-training (binnen 30min):</b> {p30}g eiwit + {kh3}g KH — hersteldrank of kwark met fruit.",
            f"☀️ <b>Ontbijt (60-90min na training):</b> Volledig herstelontbijt met havermout, ei en fruit.",
        ]
    elif "Avond" in timing:
        tips += [
            f"🌤️ <b>Lunch:</b> Koolhydraatrijk — {kh3}g KH als voorbereiding op avondtraining.",
            f"🌆 <b>Pre-training snack (1-2u voor):</b> {kh2}g KH — licht verteerbaar (banaan, rijstwafel).",
            f"🌙 <b>Post-training:</b> {p30}g eiwit voor herstel. Beperk grote koolhydraatinname na 20u.",
        ]
    else:
        tips += [
            f"⚡ <b>Pre-training:</b> {kh2}g KH — licht verteerbaar snack.",
            f"🔄 <b>Post-training (30min):</b> {p30}g eiwit + {kh3}g KH voor snelle recovery.",
            f"🍽️ <b>Volgende maaltijd:</b> Gebalanceerd met koolhydraten, eiwit en groenten.",
        ]

    if "Intensief" in training_type or "Wedstrijd" in training_type:
        tips.append("🚀 <b>Intensieve training:</b> Overweeg electrolytdrank tijdens de inspanning (Na+, K+).")

    return tips
