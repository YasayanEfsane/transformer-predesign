"""Streamlit front end for the transformer pre-design engine."""

from __future__ import annotations
import yfinance as yf
import json
from datetime import datetime

from copy import deepcopy

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from transformer_design.calculations.costing import OIL_TYPES
from transformer_design.calculations.engine import synthesize_transformer
from transformer_design.calculations.optimization import run_pareto_optimization
from transformer_design.calculations.thermal import simulate_dynamic_thermal
from transformer_design.models.enums import (
    ConductorMaterial,
    CoolingMethod,
    CoreTopology,
    PhaseSystem,
    LossEvaluationMode,
)
from transformer_design.models.inputs import (
    CoreInfo,
    ElectricalInfo,
    GeneralInfo,
    InsulationThermalInfo,
    OrderInput,
    WindingInfo,
)
from transformer_design.reporting.pdf_generator import generate_engineering_pdf_bytes
from transformer_design.reporting.visualizer import (
    generate_thermal_heatmap_svg,
    generate_transformer_svg,
)



@st.cache_data(ttl=3600)
def get_market_prices():
    try:
        cu = yf.Ticker("HG=F").history(period="1d")["Close"].iloc[-1] * 2204.62
        al = yf.Ticker("ALI=F").history(period="1d")["Close"].iloc[-1]
        return {"copper": cu, "aluminum": al}
    except:
        return {"copper": 9800.0, "aluminum": 2400.0}

st.set_page_config(
    page_title="Transformer Design Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
        <style>
      .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        color: #0f172a;
      }
      [data-testid="stMain"] {color: #0f172a;}
      [data-testid="stMain"] h1,
      [data-testid="stMain"] h2,
      [data-testid="stMain"] h3,
      [data-testid="stMain"] h4,
      [data-testid="stMain"] p,
      [data-testid="stMain"] label,
      [data-testid="stMain"] li {color: #0f172a;}
      
      /* Sidebar */
      [data-testid="stSidebar"] {
        background: #0f172a;
      }
      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] span,
      [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: #e2e8f0 !important;
      }
      
      /* Inputs inside Sidebar should be light with dark text for readability */
      [data-testid="stSidebar"] input,
      [data-testid="stSidebar"] [data-baseweb="select"] div {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
      }
      [data-testid="stSidebar"] [data-baseweb="input"],
      [data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #f8fafc !important;
      }
      
      [data-testid="stMetric"] {
        background: rgba(255,255,255,.88); border: 1px solid #e2e8f0;
        border-radius: 16px; padding: 14px 16px; box-shadow: 0 8px 28px rgba(15,23,42,.06);
      }
      [data-testid="stMetricLabel"] p {color: #64748b !important;}
      [data-testid="stMetricValue"] {color: #0f172a !important;}
      [data-baseweb="tab"] p {color: #475569 !important;}
      [data-baseweb="tab"][aria-selected="true"] p {color: #ef4444 !important;}
      [data-testid="stAlert"] p {color: #1f2937 !important;}
      [data-testid="stCaptionContainer"] p {color: #64748b !important;}
      
      .hero {
        padding: 24px 28px; border-radius: 22px; color: white; margin-bottom: 18px;
        background: linear-gradient(120deg, #0f172a, #1d4ed8 62%, #06b6d4);
        box-shadow: 0 18px 50px rgba(29,78,216,.20);
      }
      .hero h1 {margin: 0 0 8px 0; font-size: 2.1rem; color: #ffffff !important;}
      .hero p {margin: 0; color: #dbeafe !important;}
      .screening-note {font-size: .9rem; color: #64748b !important;}
      
      .market-ticker {
          position: fixed;
          top: 10px;
          right: 20px;
          background-color: #0f172a;
          color: #f8fafc;
          padding: 8px 15px;
          border-radius: 8px;
          font-weight: bold;
          font-size: 14px;
          z-index: 9999999;
          border: 1px solid #334155;
          box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.5);
      }
      
      @media (max-width: 768px) {
          .stApp { padding: 0.5rem; }
          .hero h1 { font-size: 1.5rem; }
          [data-testid="stSidebar"] { min-width: 100%; }
      }
    </style>

    """,
    unsafe_allow_html=True,
)
prices = get_market_prices()
st.markdown(f'''
    <div class="market-ticker">
        📈 LME Bakır: ${prices["copper"]:,.0f}/t &nbsp;|&nbsp; 📈 LME Alüminyum: ${prices["aluminum"]:,.0f}/t
    </div>
''', unsafe_allow_html=True)

st.markdown(
    """
    <section class="hero">
      <h1>⚡ Transformer Design Engine</h1>
      <p>Üç fazlı dağıtım transformatörleri için tutarlı, izlenebilir ve karşılaştırılabilir ön tasarım.</p>
    </section>
    """,
    unsafe_allow_html=True,
)


def material_from_label(label: str) -> ConductorMaterial:
    return ConductorMaterial.COPPER if label == "Bakır" else ConductorMaterial.ALUMINUM


def material_label(material: ConductorMaterial) -> str:
    return "Bakır" if material == ConductorMaterial.COPPER else "Alüminyum"


def build_order_input(values: dict[str, object]) -> OrderInput:
    return OrderInput(
        general=GeneralInfo(
            standard="IEC 60076",
            standard_edition="project",
            application_type="Distribution",
            phase_system=PhaseSystem.THREE_PHASE,
            indoor_outdoor="Outdoor",
            protection_degree="IP00",
            tank_type="Corrugated",
            rated_power_kVA=values["power_kva"],
            rated_frequency_Hz=values["frequency_hz"],
            cooling_method=CoolingMethod.ONAN,
            ambient_temperature_C=values["ambient_c"],
            altitude_m=values["altitude_m"],
        ),
        core=CoreInfo(
            core_topology=CoreTopology.THREE_LEG,
            number_of_legs=3,
            number_of_windows=2,
            target_max_flux_density_T=values["target_flux_t"],
            core_steel_grade="M5",
            stacking_factor=values.get("stacking_factor", 0.96),
            additional_no_load_loss_factor=1.05
        ),
        electrical=ElectricalInfo(
            hv_voltage_V=values["hv_voltage_v"],
            lv_voltage_V=values["lv_voltage_v"],
            connection_group=values["connection_group"],
            tap_changer_side="HV",
            tap_changer_type="Boşta",
            rated_short_circuit_impedance_percent=values["uk_percent"],
            impedance_reference_temperature_C=75,
            no_load_loss_W=values["no_load_loss_w"],
            load_loss_W=values["load_loss_w"],
            load_loss_reference_temperature_C=75,
            load_loss_definition="total",
            loss_evaluation_mode=LossEvaluationMode.GUARANTEED,
            tap_percentages=[-5.0, -2.5, 0.0, 2.5, 5.0]
        ),
        winding=WindingInfo(
            hv_conductor_material=material_from_label(values["hv_material"]),
            lv_conductor_material=material_from_label(values["lv_material"]),
            hv_target_current_density_A_mm2=values["hv_j"],
            lv_target_current_density_A_mm2=values["lv_j"],
            hv_parallel_conductors=1,
            lv_parallel_conductors=1,
            hv_winding_height_mm=values["winding_height_mm"],
            lv_winding_height_mm=values["winding_height_mm"],
            additional_load_loss_factor=1.15
        ),
        insulation=InsulationThermalInfo(
            oil_type=values["oil_type"],
            top_oil_temp_rise_limit_K=values["top_oil_rise_k"],
            allowed_hot_spot_temp_C=values["hot_spot_limit_c"],
        ),
    )
def save_comparison(result: dict[str, object]) -> None:
    inputs = result["inputs"]
    row = {
        "Tasarım": (
            f"{inputs.general.rated_power_kVA:g} kVA · "
            f"{material_label(inputs.winding.hv_conductor_material)}/"
            f"{material_label(inputs.winding.lv_conductor_material)} · "
            f"{inputs.core.target_max_flux_density_T:.2f} T"
        ),
        "TOC ($)": round(result["toc_usd"], 0),
        "İmalat ($)": round(result["total_factory_cost"], 0),
        "Ağırlık (kg)": round(result["total_weight"], 0),
        "Verim (%)": round(result["eff"]["efficiency"] * 100, 3),
        "Hot-spot (°C)": round(result["hot_spot_temperature_c"], 1),
        "Uygun": "Evet" if result["is_feasible"] else "Kontrol",
    }
    history = st.session_state.setdefault("design_history", [])
    if not history or history[-1] != row:
        history.append(row)
    st.session_state["design_history"] = history[-10:]


def report_payload(result: dict[str, object]) -> dict[str, object]:
    inputs = result["inputs"]
    costs = result["cost_weight"]
    return {
        "s_rated_kva": inputs.general.rated_power_kVA,
        "standard": inputs.general.standard,
        "frequency_hz": inputs.general.rated_frequency_Hz,
        "connection_group": inputs.electrical.connection_group,
        "cooling_method": inputs.general.cooling_method.value,
        "protection_degree": inputs.general.protection_degree,
        "ambient_c": inputs.general.ambient_temperature_C,
        "v_hv": inputs.electrical.hv_voltage_V,
        "v_lv": inputs.electrical.lv_voltage_V,
        "uk_percent": inputs.electrical.rated_short_circuit_impedance_percent,
        "p_load_w": inputs.electrical.load_loss_W,
        "p_no_load_w": inputs.electrical.no_load_loss_W,
        "hv_mat": material_label(inputs.winding.hv_conductor_material),
        "lv_mat": material_label(inputs.winding.lv_conductor_material),
        "oil_type": result["oil_type"],
        "target_flux_T": inputs.core.target_max_flux_density_T,
        "eff": result["eff"]["efficiency"],
        "i_hv": result["line_currents"]["i_hv_line"].to("A").magnitude,
        "i_lv": result["line_currents"]["i_lv_line"].to("A").magnitude,
        "core_d_mm": result["core_geom"]["d_physical"].to("mm").magnitude,
        "core_a_cm2": result["core_geom"]["a_core_gross"].to("cm**2").magnitude,
        "hv_turns": result["hv_turns"]["n_selected"],
        "lv_turns": result["lv_turns"]["n_selected"],
        "hv_j": result["hv_cond"]["j_actual"].magnitude,
        "lv_j": result["lv_cond"]["j_actual"].magnitude,
        "rad_fins": result["hot_spot"]["num_radiator_fins"],
        "hot_spot_rise": result["hot_spot"]["hot_spot_rise_k"],
        "oil_volume": costs["oil_stats"]["volume_L"],
        "weight_active": costs["weights_kg"]["active_part_untanked"],
        "weight_tank": costs["weights_kg"]["tank"],
        "weight_oil": costs["weights_kg"]["oil"],
        "weight_total": result["total_weight"],
        "cost_total": result["total_factory_cost"],
        "toc_total": result["toc_usd"],
        "f_radial": result["mechanical"]["f_radial_kN"],
        "clearance": result["dielectric"]["phase_to_phase_mm"],
        "design_status": "Tarama uygun" if result["is_feasible"] else "Mühendislik kontrolü gerekli",
    }


with st.sidebar:
    st.header("Tasarım girdileri")
    with st.form("design_inputs"):
        st.caption("Elektriksel sipariş")
        power_kva = st.number_input("Anma gücü (kVA)", 25.0, 100000.0, 1000.0, 25.0)
        frequency_hz = st.selectbox("Frekans (Hz)", [50.0, 60.0])
        hv_voltage_v = st.number_input("HV hat gerilimi (V)", 1000.0, 500000.0, 33000.0, 1000.0)
        lv_voltage_v = st.number_input("LV hat gerilimi (V)", 100.0, 100000.0, 400.0, 10.0)
        connection_group = st.selectbox("Bağlantı grubu", ["Dyn11", "Yyn0", "Dd0"])
        uk_percent = st.number_input("Hedef uk (%)", 0.1, 30.0, 5.0, 0.1)
        no_load_loss_w = st.number_input("Boşta kayıp (W)", 1.0, 1000000.0, 1700.0, 10.0)
        load_loss_w = st.number_input("Yükte kayıp (W)", 1.0, 5000000.0, 10500.0, 100.0)

        with st.expander("Manyetik ve sargı", expanded=True):
            target_flux_t = st.number_input("Hedef akı yoğunluğu (T)", 0.8, 2.2, 1.60, 0.01)
            stacking_factor = st.number_input("İstifleme faktörü", 0.50, 1.00, 0.96, 0.01)
            hv_material = st.selectbox("HV iletkeni", ["Bakır", "Alüminyum"])
            lv_material = st.selectbox("LV iletkeni", ["Alüminyum", "Bakır"])
            hv_j = st.number_input("HV akım yoğunluğu (A/mm²)", 0.5, 10.0, 3.0, 0.1)
            lv_j = st.number_input("LV akım yoğunluğu (A/mm²)", 0.5, 10.0, 2.5, 0.1)
            winding_height_mm = st.number_input("Sargı yüksekliği (mm)", 100.0, 3000.0, 380.0, 10.0)

        with st.expander("Termal, ortam ve maliyet"):
            ambient_c = st.number_input("Ortam sıcaklığı (°C)", -50.0, 80.0, 40.0, 1.0)
            altitude_m = st.number_input("Rakım (m)", 0.0, 6000.0, 1000.0, 100.0)
            top_oil_rise_k = st.number_input("Anma üst yağ artışı (K)", 10.0, 100.0, 60.0, 1.0)
            hot_spot_limit_c = st.number_input("Hot-spot sınırı (°C)", 60.0, 200.0, 110.0, 1.0)
            oil_type = st.selectbox("İzolasyon sıvısı", list(OIL_TYPES))
            a_factor = st.number_input("A faktörü ($/W)", 0.0, 100.0, 8.0, 0.5)
            b_factor = st.number_input("B faktörü ($/W)", 0.0, 100.0, 2.0, 0.5)
            heat_dissipation = st.number_input("Isı yayılımı (W/m²K)", 1.0, 50.0, 12.5, 0.5)
            copper_price = st.number_input("Bakır ($/kg)", 0.01, 1000.0, 10.50, 0.10)
            aluminum_price = st.number_input("Alüminyum ($/kg)", 0.01, 1000.0, 3.20, 0.10)
            steel_price = st.number_input("Silisli sac/çelik ($/kg)", 0.01, 1000.0, 2.80, 0.10)

        calculate_clicked = st.form_submit_button("Tasarımı hesapla", type="primary", use_container_width=True)
        optimize_clicked = st.form_submit_button("Parametrik optimize et", use_container_width=True)

values = {
    "power_kva": power_kva,
    "frequency_hz": frequency_hz,
    "hv_voltage_v": hv_voltage_v,
    "lv_voltage_v": lv_voltage_v,
    "connection_group": connection_group,
    "uk_percent": uk_percent,
    "no_load_loss_w": no_load_loss_w,
    "load_loss_w": load_loss_w,
    "target_flux_t": target_flux_t,
    "stacking_factor": stacking_factor,
    "hv_material": hv_material,
    "lv_material": lv_material,
    "hv_j": hv_j,
    "lv_j": lv_j,
    "winding_height_mm": winding_height_mm,
    "ambient_c": ambient_c,
    "altitude_m": altitude_m,
    "top_oil_rise_k": top_oil_rise_k,
    "hot_spot_limit_c": hot_spot_limit_c,
    "oil_type": oil_type,
}
prices = {"COPPER": copper_price, "ALUMINUM": aluminum_price, "STEEL": steel_price}

if calculate_clicked or optimize_clicked:
    try:
        order_input = build_order_input(values)
        if optimize_clicked:
            with st.spinner("36 aday tasarım taranıyor…"):
                def evaluate(flux_t: float, hv_density: float, lv_density: float) -> dict[str, object]:
                    candidate = deepcopy(order_input)
                    candidate.core.target_max_flux_density_T = flux_t
                    candidate.winding.hv_target_current_density_A_mm2 = hv_density
                    candidate.winding.lv_target_current_density_A_mm2 = lv_density
                    return synthesize_transformer(
                        candidate,
                        prices,
                        a_factor,
                        b_factor,
                        oil_type_str=oil_type,
                        heat_dissipation_w_m2k=heat_dissipation,
                    )

                optimization = run_pareto_optimization(evaluate, objective="toc")
                result = optimization["best_result"]
                st.session_state["optimization_summary"] = optimization
        else:
            result = synthesize_transformer(
                order_input,
                prices,
                a_factor,
                b_factor,
                oil_type_str=oil_type,
                heat_dissipation_w_m2k=heat_dissipation,
            )
            st.session_state.pop("optimization_summary", None)
        st.session_state["design_result"] = result
        st.session_state.pop("thermal_result", None)
        save_comparison(result)
    except ValidationError as exc:
        messages = [error["msg"] for error in exc.errors()]
        st.error("Girdiler doğrulanamadı: " + " · ".join(messages))
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Tasarım hesaplanamadı: {exc}")

result = st.session_state.get("design_result")
if result is None:
    st.info("Başlamak için sol paneldeki doğrulanmış varsayılanları kullanarak **Tasarımı hesapla** seçeneğine basın.")
    st.markdown(
        '<p class="screening-note">Araç ön tasarım ve seçenek taraması içindir; üretim onayı veya tip testi yerine geçmez.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

optimization = st.session_state.get("optimization_summary")
if optimization:
    best = optimization["best_parameters"]
    st.success(
        f"Optimum aday: {best['flux_T']:.2f} T · HV {best['hv_j']:.1f} A/mm² · "
        f"LV {best['lv_j']:.1f} A/mm² · {optimization['evaluated_count']} aday değerlendirildi."
    )

metric_columns = st.columns(5)
metric_columns[0].metric("İmalat maliyeti", f"${result['total_factory_cost']:,.0f}")
metric_columns[1].metric("TOC", f"${result['toc_usd']:,.0f}")
metric_columns[2].metric("Toplam ağırlık", f"{result['total_weight']:,.0f} kg")
metric_columns[3].metric("Tam yük verimi", f"%{result['eff']['efficiency'] * 100:.3f}")
metric_columns[4].metric("Hot-spot", f"{result['hot_spot_temperature_c']:.1f} °C")

if result["warnings"]:
    st.warning("  ".join(f"• {warning}" for warning in result["warnings"]))
else:
    st.success("Tüm ön tasarım tarama kontrolleri geçti.")

tabs = st.tabs(
    [
        "Özet",
        "Elektrik & geometri",
        "Dinamik termal",
        "Maliyet & ağırlık",
        "İmalat",
        "Görsel & rapor",
        "Karşılaştırma",
    ]
)

with tabs[0]:
    st.subheader("Tasarım sağlık kontrolü")
    labels = {
        "flux_density": "Akı yoğunluğu",
        "ampere_turn_balance": "Amper-sarım dengesi",
        "impedance_screening": "Geometrik uk% taraması",
        "hot_spot_temperature": "Hot-spot sınırı",
    }
    check_columns = st.columns(4)
    for column, (key, label) in zip(check_columns, labels.items(), strict=True):
        column.metric(label, "Geçti" if result["design_checks"][key] else "Kontrol")
    st.caption(
        "Kontroller ön tasarım toleranslarıdır. IEC uygunluğu ancak ayrıntılı tasarım, üretici verileri "
        "ve ilgili deneylerle doğrulanabilir."
    )

with tabs[1]:
    electrical_columns = st.columns(4)
    electrical_columns[0].metric("HV hat akımı", f"{result['line_currents']['i_hv_line'].to('A').magnitude:.2f} A")
    electrical_columns[1].metric("LV hat akımı", f"{result['line_currents']['i_lv_line'].to('A').magnitude:.2f} A")
    electrical_columns[2].metric("Tur başına gerilim", f"{result['turn_voltage'].to('V').magnitude:.3f} V")
    electrical_columns[3].metric("Gerçek akı", f"{result['actual_flux_density'].to('T').magnitude:.3f} T")
    geometry_columns = st.columns(4)
    geometry_columns[0].metric("Çekirdek çapı", f"{result['core_geom']['d_physical'].to('mm').magnitude:.1f} mm")
    geometry_columns[1].metric("HV tur", f"{result['hv_turns']['n_selected']}")
    geometry_columns[2].metric("LV tur", f"{result['lv_turns']['n_selected']}")
    geometry_columns[3].metric(
        "Fiziksel uk%",
        f"%{result['physical_uk_percent']:.2f}",
        delta=f"{result['physical_uk_percent'] - result['inputs'].electrical.rated_short_circuit_impedance_percent:+.2f} puan",
        delta_color="inverse",
    )
    st.divider()
    mechanical_columns = st.columns(4)
    mechanical_columns[0].metric("Tepe kısa devre akımı", f"{result['mechanical']['i_sc_peak_A']:,.0f} A")
    mechanical_columns[1].metric("Radyal kuvvet", f"{result['mechanical']['f_radial_kN']:,.2f} kN")
    mechanical_columns[2].metric("Faz-toprak açıklığı", f"{result['dielectric']['phase_to_ground_mm']:.1f} mm")
    mechanical_columns[3].metric("Ses gücü tahmini", f"{result['acoustics']['sound_power_db_a']:.1f} dB(A)")

with tabs[2]:
    st.subheader("24 saatlik yük profili")
    if "thermal_profile" not in st.session_state:
        loads = [55, 50, 48, 47, 50, 60, 72, 82, 78, 70, 66, 64, 62, 65, 70, 78, 92, 105, 110, 100, 88, 76, 66, 60]
        ambient = [22, 21, 20, 20, 20, 21, 23, 25, 27, 29, 31, 33, 34, 35, 35, 34, 33, 31, 29, 27, 26, 25, 24, 23]
        st.session_state["thermal_profile"] = pd.DataFrame(
            {"Saat": list(range(24)), "Yük (%)": loads, "Ortam (°C)": ambient}
        )
    profile = st.data_editor(
        st.session_state["thermal_profile"],
        hide_index=True,
        use_container_width=True,
        disabled=["Saat"],
        num_rows="fixed",
        key="thermal_profile_editor",
    )
    if st.button("Termal profili simüle et", type="primary"):
        try:
            load_ratio = result["p_ll_w"] / result["p_nl_w"]
            thermal_rows = simulate_dynamic_thermal(
                (profile["Yük (%)"].astype(float) / 100.0).tolist(),
                profile["Ortam (°C)"].astype(float).tolist(),
                rated_top_oil_rise_k=result["inputs"].insulation.top_oil_temp_rise_limit_K,
                rated_hot_spot_gradient_k=(
                    result["hot_spot"]["hot_spot_rise_k"]
                    - result["inputs"].insulation.top_oil_temp_rise_limit_K
                ),
                load_to_no_load_loss_ratio=load_ratio,
            )
            st.session_state["thermal_result"] = pd.DataFrame(thermal_rows)
            st.session_state["thermal_profile"] = profile
        except (ValueError, TypeError) as exc:
            st.error(f"Termal profil geçersiz: {exc}")

    thermal_frame = st.session_state.get("thermal_result")
    if thermal_frame is not None:
        chart = thermal_frame.set_index("time_hours")[[
            "ambient_temperature_c",
            "top_oil_temperature_c",
            "hot_spot_temperature_c",
        ]]
        chart.columns = ["Ortam", "Üst yağ", "Hot-spot"]
        st.line_chart(chart, x_label="Saat", y_label="Sıcaklık (°C)")
        peak_index = int(thermal_frame["hot_spot_temperature_c"].idxmax())
        selected_index = st.slider("Isı haritası zamanı", 0, len(thermal_frame) - 1, peak_index)
        selected = thermal_frame.iloc[selected_index]
        st.components.v1.html(
            generate_thermal_heatmap_svg(
                selected["ambient_temperature_c"],
                selected["top_oil_temperature_c"],
                selected["hot_spot_temperature_c"],
            ),
            height=430,
        )
        thermal_metrics = st.columns(3)
        thermal_metrics[0].metric("Tepe hot-spot", f"{thermal_frame['hot_spot_temperature_c'].max():.1f} °C")
        thermal_metrics[1].metric("Tepe üst yağ", f"{thermal_frame['top_oil_temperature_c'].max():.1f} °C")
        thermal_metrics[2].metric("Eşdeğer yaşlanma toplamı", f"{thermal_frame['aging_acceleration_factor'].sum():.2f} saat")
    else:
        st.info("Profili düzenleyip simülasyonu başlatın.")

with tabs[3]:
    costs = result["cost_weight"]
    weight_frame = pd.DataFrame(
        {
            "Bileşen": ["Çekirdek", "HV sargı", "LV sargı", "Tank", "Yağ"],
            "Ağırlık (kg)": [
                costs["weights_kg"]["core"],
                costs["weights_kg"]["hv_winding"],
                costs["weights_kg"]["lv_winding"],
                costs["weights_kg"]["tank"],
                costs["weights_kg"]["oil"],
            ],
            "Maliyet ($)": [
                costs["costs_usd"]["core"],
                costs["costs_usd"]["hv_winding"],
                costs["costs_usd"]["lv_winding"],
                costs["costs_usd"]["tank"],
                costs["costs_usd"]["oil"],
            ],
        }
    )
    st.dataframe(weight_frame.style.format({"Ağırlık (kg)": "{:,.1f}", "Maliyet ($)": "${:,.2f}"}), hide_index=True, use_container_width=True)
    st.bar_chart(weight_frame.set_index("Bileşen")["Maliyet ($)"], y_label="USD")
    st.caption("Fiyatlar hesap anında sol panelde girilen sabit USD/kg değerleridir; ağdan veri çekilmez.")

with tabs[4]:
    st.subheader("Çekirdek sac kesim listesi")
    core_steps = pd.DataFrame(result["core_steps"]).rename(
        columns={
            "step_no": "Kademe",
            "width_mm": "Kesim genişliği (mm)",
            "packet_thickness_mm": "Paket kalınlığı (mm)",
            "num_sheets": "Sac adedi",
        }
    )
    st.dataframe(core_steps, hide_index=True, use_container_width=True)
    recipe_columns = st.columns(2)
    for column, title, recipe, turns in (
        (recipe_columns[0], "HV sargısı", result["hv_winding_recipe"], result["hv_turns"]["n_selected"]),
        (recipe_columns[1], "LV sargısı", result["lv_winding_recipe"], result["lv_turns"]["n_selected"]),
    ):
        with column:
            st.markdown(f"#### {title}")
            st.write(f"Toplam tur: **{turns}**")
            st.write(f"Kat başına tur: **{recipe['turns_per_layer']}**")
            st.write(f"Katman sayısı: **{recipe['num_layers']}**")
            st.write(f"Radyal kalınlık: **{recipe['radial_build_mm']:.1f} mm**")

with tabs[5]:
    inputs = result["inputs"]
    transformer_svg = generate_transformer_svg(
        inputs.winding.hv_conductor_material,
        inputs.winding.lv_conductor_material,
        result["hv_turns"]["n_selected"],
        result["lv_turns"]["n_selected"],
        result["hv_cond"]["a_selected_total"].to("mm**2").magnitude,
        result["lv_cond"]["a_selected_total"].to("mm**2").magnitude,
        result["core_geom"]["d_physical"].to("mm").magnitude,
    )
    st.components.v1.html(transformer_svg, height=720)
    try:
        pdf_bytes = generate_engineering_pdf_bytes(result)
        st.download_button(
            "Mühendislik ön tasarım raporunu indir",
            data=pdf_bytes,
            file_name="transformer_pre_design_report.pdf",
            mime="application/pdf",
            type="primary",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        st.error(f"PDF raporu üretilemedi: {exc}")

with tabs[6]:
    history = st.session_state.get("design_history", [])
    if history:
        history_frame = pd.DataFrame(history)
        st.dataframe(history_frame, hide_index=True, use_container_width=True)
        if len(history_frame) > 1:
            st.line_chart(history_frame.set_index("Tasarım")[["TOC ($)", "İmalat ($)"]])
        if st.button("Karşılaştırma geçmişini temizle"):
            st.session_state["design_history"] = []
            st.rerun()
    else:
        st.info("Her hesaplama son on tasarımlık karşılaştırma geçmişine eklenir.")

st.markdown(
    '<p class="screening-note">Ön tasarım sonuçları; üretici malzeme eğrileri, ayrıntılı kaçak alan analizi, FEA/CFD ve tip testleriyle doğrulanmalıdır.</p>',
    unsafe_allow_html=True,
)
