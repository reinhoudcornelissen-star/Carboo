import streamlit as st
import random
from data import FOOD_DB, MOMENT_CONFIGS, BOOST_TIPS


def _get_boost_tip(moment: str) -> str:
    cat = "Tussendoor" if ("Tussendoor" in moment or moment == "Avond") else moment
    pool = BOOST_TIPS.get(cat, BOOST_TIPS["Tussendoor"])
    tip, _ = random.choice(pool)
    return f"• {tip}"


def render_carbomax():
    st.markdown('<div class="section-title">🍝 CARBOMAX — Carbohydrate Loading Plan</div>', unsafe_allow_html=True)

    # ─── USER INPUTS ────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        gewicht = st.number_input("Lichaamsgewicht (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.5)
    with col2:
        duur = st.number_input("Wedstrijdduur (uren)", min_value=0.5, max_value=24.0, value=4.0, step=0.5)

    # Determine factor & daily target
    if duur > 5:
        factor = 12
    elif duur > 3:
        factor = 10
    elif duur > 1.5:
        factor = 8
    else:
        factor = 6

    dag_target = round(gewicht * factor)

    st.markdown(f"""
    <div style="background:rgba(249,115,22,0.1); border:1px solid #f97316; padding:14px; 
         border-radius:10px; margin-bottom:20px; text-align:center; color:#fb923c; font-weight:700;">
        🎯 Koolhydraatdoelstelling: <span style="font-size:1.3rem;">{dag_target}g / dag</span>
        &nbsp;&nbsp;|&nbsp;&nbsp; Factor: {factor}g/kg &nbsp;&nbsp;|&nbsp;&nbsp; Duur: {duur}u
    </div>
    """, unsafe_allow_html=True)

    # ─── DAG TABS ────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📅  DAG 1", "📅  DAG 2"])

    results = {}  # dag -> moment -> (carbs, items_html)

    for dag_idx, tab in enumerate([tab1, tab2], start=1):
        dag_key = f"dag{dag_idx}"
        results[dag_key] = {}

        with tab:
            # Build a 2-column meal grid
            moments = list(MOMENT_CONFIGS.keys())
            left_moments  = moments[:3]
            right_moments = moments[3:]

            left_col, right_col = st.columns(2)

            for col, moment_list in [(left_col, left_moments), (right_col, right_moments)]:
                with col:
                    for moment in moment_list:
                        cfg = MOMENT_CONFIGS[moment]
                        target_m = round(dag_target * cfg["pct"])

                        st.markdown(f"""
                        <div class="meal-card">
                            <div class="meal-card-title">{moment.upper()} — doel: {target_m}g KH</div>
                        """, unsafe_allow_html=True)

                        moment_carbs = 0
                        items_list = []

                        for food in cfg["foods"]:
                            info = FOOD_DB.get(food)
                            if not info:
                                continue
                            key = f"c_{dag_idx}_{moment}_{food}"
                            val = st.number_input(
                                f"{food} ({info['unit']})",
                                min_value=0.0, value=0.0, step=1.0,
                                key=key
                            )
                            if val > 0:
                                c = round(val * info["carbs"])
                                moment_carbs += c
                                items_list.append(f"{val} {info['unit']} {food} ({c}g)")

                        # Custom product row
                        with st.expander("➕ Eigen product toevoegen"):
                            cname = st.text_input("Naam", key=f"cname_{dag_idx}_{moment}")
                            ccarbs = st.number_input("KH (gram)", min_value=0.0, key=f"ccarbs_{dag_idx}_{moment}")
                            if cname and ccarbs > 0:
                                moment_carbs += ccarbs
                                items_list.append(f"{cname} (eigen) {round(ccarbs)}g")

                        st.markdown("</div>", unsafe_allow_html=True)

                        results[dag_key][moment] = {
                            "carbs": moment_carbs,
                            "target": target_m,
                            "items": items_list,
                        }

    # ─── GENERATE PLAN BUTTON ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀  GENEREER CARB-RAPPORT", key="calc_btn"):
        _render_results(results, dag_target)


def _render_results(results: dict, dag_target: int):
    st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#1e293b; padding:20px; border-radius:16px; text-align:center; margin-bottom:24px;">
        <div style="font-size:1.5rem; font-weight:900; color:#f97316; letter-spacing:3px;">NUTRIFLOW CARB-REPORT</div>
    </div>
    """, unsafe_allow_html=True)

    for dag_key in ["dag1", "dag2"]:
        dag_num = dag_key[-1]
        dag_data = results[dag_key]

        st.markdown(f"<div style='font-weight:800; font-size:1.1rem; color:#3b82f6; margin-bottom:12px;'>DAG {dag_num}</div>", unsafe_allow_html=True)

        dag_totaal = 0
        for moment, data in dag_data.items():
            carbs   = data["carbs"]
            target  = data["target"]
            items   = data["items"]
            tekort  = target - carbs
            ok      = tekort <= 5

            dag_totaal += carbs
            css_class = "result-ok" if ok else "result-low"
            icon      = "✅" if ok else "❌"
            items_html = "".join(f"<li style='font-size:0.8rem;'>{i}</li>" for i in items) if items else "<li style='font-size:0.8rem; color:#64748b;'>Geen inname gepland</li>"

            boost_html = ""
            if not ok and tekort > 5:
                tip = _get_boost_tip(moment)
                boost_html = f"""<div class="boost-tip"><strong>💡 Booster Tip:</strong> {tip}</div>"""

            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between; font-weight:700; margin-bottom:6px;">
                    <span>{icon} {moment}</span>
                    <span>{round(carbs)}g / {target}g</span>
                </div>
                <ul style="margin:0; padding-left:18px;">{items_html}</ul>
                {boost_html}
            </div>
            """, unsafe_allow_html=True)

        # Day total
        pct = round((dag_totaal / dag_target) * 100) if dag_target else 0
        bar_color = "#22c55e" if pct >= 90 else ("#fbbf24" if pct >= 70 else "#ef4444")
        st.markdown(f"""
        <div style="background:#1e293b; border-radius:12px; padding:16px; text-align:center; margin-bottom:20px;">
            <div style="font-weight:900; font-size:1rem; margin-bottom:8px;">
                TOTAAL DAG {dag_num}: {round(dag_totaal)}g / {dag_target}g
            </div>
            <div style="background:#334155; border-radius:8px; height:10px; overflow:hidden;">
                <div style="width:{min(pct,100)}%; height:100%; background:{bar_color}; border-radius:8px;"></div>
            </div>
            <div style="font-size:0.8rem; color:#94a3b8; margin-top:5px;">{pct}% van dagtarget</div>
        </div>
        """, unsafe_allow_html=True)
