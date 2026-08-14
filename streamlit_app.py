import streamlit as st
import math
from transformer_design.units import Q_
from transformer_design.models.enums import PhaseSystem, CoolingMethod, ConductorMaterial, CoreTopology
from transformer_design.models.inputs import OrderInput, GeneralInfo, ElectricalInfo, WindingInfo, CoreInfo, InsulationThermalInfo
from transformer_design.models.assumptions import DesignAssumptions
from transformer_design.models.results import CalculatedValue
from transformer_design.calculations.connection import parse_connection_group, get_phase_voltage, get_phase_current
from transformer_design.calculations.electrical import calculate_rated_currents, calculate_short_circuit, calculate_efficiency
from transformer_design.calculations.core import calculate_turn_voltage, calculate_net_core_area, calculate_core_geometry, verify_flux_density, calculate_core_steps
from transformer_design.calculations.winding import calculate_turns, check_ampere_turns, calculate_conductor_dimensions, calculate_winding_layers
from transformer_design.calculations.thermal import calculate_required_cooling_area, estimate_tank_surface_area, calculate_tank_and_radiator_needs, calculate_hot_spot_and_fins
from transformer_design.calculations.costing import calculate_weights_and_costs
from transformer_design.calculations.mechanical import calculate_short_circuit_forces
from transformer_design.calculations.optimization import run_grid_search_optimizer
import pandas as pd
from transformer_design.calculations.dielectric import calculate_clearances
from transformer_design.reporting.visualizer import generate_transformer_svg
from transformer_design.reporting.pdf_generator import generate_engineering_pdf

st.set_page_config(page_title="Transformatör Ön Tasarım", layout="wide", page_icon="⚙️")
st.title("⚙️ 3 Fazlı Dağıtım Transformatörü Ön Tasarım Motoru")
st.markdown("Elektromanyetik fizik motorunu kullanarak sargı, çekirdek, termodinamik ve mekanik parametreleri analiz edin.")

if 'saved_designs' not in st.session_state:
    st.session_state['saved_designs'] = []

# Sidebar Girdileri
with st.sidebar:
    st.header("📋 Sipariş Girdileri")
    power_kva = st.number_input("Anma Gücü (kVA)", value=1000.0, step=100.0, help="Transformatörün verebileceği maksimum güç.")
    v_hv_line_v = st.number_input("Yüksek Gerilim (V)", value=33000.0, step=1000.0, help="Şebeke (primer) tarafındaki hatlar arası gerilim (Örn: 33kV).")
    v_lv_line_v = st.number_input("Alçak Gerilim (V)", value=400.0, step=10.0, help="Tüketici (sekonder) tarafındaki hatlar arası gerilim (Örn: 400V).")
    uk_percent = st.number_input("Kısa Devre Empedansı (%)", value=5.0, step=0.1, help="Kısa devre anında akan akımı sınırlandıran iç empedans (Genelde %4 ile %6 arasıdır).")
    p_no_load_w = st.number_input("Boşta Kayıp (W)", value=1700.0, step=10.0, help="Çekirdekte (silisli sacda) sürekli olarak harcanan sabit demir kayıpları.")
    p_load_w = st.number_input("Yükte Kayıp (W)", value=10500.0, step=100.0, help="Tam yükte çalışırken sargılarda ısıya dönüşen bakır/alüminyum kayıpları.")
    
    st.header("⚙️ Tasarım Kabulleri")
    target_flux_T = st.number_input("Hedef Akı Yoğunluğu (T)", value=1.60, step=0.01, help="Çekirdek doygunluğunu belirler. Genelde 1.55T ile 1.70T arası seçilir.")
    k_stack = st.number_input("Sac İstifleme Faktörü", value=0.96, step=0.01, help="Silisli sacların arasındaki yalıtım boşluklarını çıkaran net metal doluluk oranı.")
    
    st.header("🧵 Sargı Seçimleri")
    hv_mat_str = st.selectbox("Yüksek Gerilim İletkeni", ["Bakır", "Alüminyum"], index=0, help="Daha yüksek iletkenlik için Bakır, daha düşük maliyet için Alüminyum.")
    lv_mat_str = st.selectbox("Alçak Gerilim İletkeni", ["Bakır", "Alüminyum"], index=1, help="Daha yüksek iletkenlik için Bakır, daha düşük maliyet için Alüminyum.")
    hv_j = st.number_input("HV Hedef Akım Yoğunluğu (A/mm2)", value=3.0, step=0.1, help="Telin mm²'sinden geçmesine izin verilen akım. Düşük değerler telin kalınlaşmasına ama trafonun büyümesine neden olur.")
    lv_j = st.number_input("LV Hedef Akım Yoğunluğu (A/mm2)", value=2.5, step=0.1, help="Telin mm²'sinden geçmesine izin verilen akım. Düşük değerler telin kalınlaşmasına ama trafonun büyümesine neden olur.")
    
    st.header("🌡️ Soğutma ve İzolasyon Yağı")
    oil_type_str = st.selectbox("İzolasyon Yağı Tipi", [
        "Mineral Yağ (0.89 kg/L)", 
        "Doğal Ester (Bitkisel) (0.92 kg/L)", 
        "Sentetik Ester (0.97 kg/L)", 
        "Silikon Yağ (0.96 kg/L)"
    ], index=0, help="Farklı yağ tiplerinin yalıtım, soğutma, parlama noktası ve çevre dostu olma özellikleri değişir. Özkütle ağırlığı etkiler.")
    target_oil_rise = st.number_input("Hedef Yağ Sıcaklık Artışı (K)", value=60.0, step=1.0, help="IEC 60076-2'ye göre standart üst yağ sıcaklık artışı 60K'dir.")
    heat_dissipation = st.number_input("Tank Isı Yayılım Katsayısı (W/m²K)", value=12.5, step=0.5, help="Işınım + Taşınım bileşik ısı transfer katsayısı (Genelde 11-13 arası).")
    
    st.header("💼 İhale & TOC Faktörleri")
    a_factor = st.number_input("Boşta Kayıp (A) Faktörü ($/W)", value=8.0, step=0.5, help="Müşterinin 1 Watt boşta kayıp için ödemeye razı olduğu ceza bedeli.")
    b_factor = st.number_input("Yükte Kayıp (B) Faktörü ($/W)", value=2.0, step=0.5, help="Müşterinin 1 Watt yükte kayıp için ödemeye razı olduğu ceza bedeli.")
    
    st.header("⚙️ Canlı Fiyat Ayarları")
    with st.expander("Manuel Fiyat / Kur Güncelle (LME)", expanded=False):
        st.info("Eğer güncel LME kurları otomatik çekilemezse buradaki sabit değerler kullanılır. İstediğiniz gibi değiştirebilirsiniz.")
        custom_cu_price = st.number_input("Bakır Fiyatı ($/kg)", value=10.50, step=0.10)
        custom_al_price = st.number_input("Alüminyum Fiyatı ($/kg)", value=3.20, step=0.10)
        custom_steel_price = st.number_input("Silisli Sac Fiyatı ($/kg)", value=2.80, step=0.10)
        
        custom_prices = {
            "COPPER": custom_cu_price,
            "ALUMINUM": custom_al_price,
            "STEEL": custom_steel_price
        }

    c1, c2 = st.columns(2)
    with c1:
        calc_button = st.button("🚀 Hesapla", type="primary", use_container_width=True)
    with c2:
        opt_button = st.button("🤖 AI Çözücü", type="secondary", use_container_width=True)

    hv_mat = ConductorMaterial.COPPER if hv_mat_str == "Bakır" else ConductorMaterial.ALUMINUM
    lv_mat = ConductorMaterial.COPPER if lv_mat_str == "Bakır" else ConductorMaterial.ALUMINUM
    
    inputs = OrderInput(
        general=GeneralInfo(
            standard="IEC 60076",
            standard_edition="2011",
            application_type="Dağıtım",
            phase_system=PhaseSystem.THREE_PHASE,
            rated_power_kVA=power_kva,
            rated_frequency_Hz=50.0,
            cooling_method=CoolingMethod.ONAN,
            indoor_outdoor="Outdoor",
            ambient_temperature_C=40.0,
            altitude_m=1000.0,
            protection_degree="IP54",
            tank_type="Corrugated",
        ),
        electrical=ElectricalInfo(
            hv_voltage_V=v_hv_line_v,
            lv_voltage_V=v_lv_line_v,
            connection_group="Dyn11",
            tap_changer_side="HV",
            tap_changer_type="Off-Circuit",
            rated_short_circuit_impedance_percent=uk_percent,
            impedance_reference_temperature_C=75.0,
            no_load_loss_W=p_no_load_w,
            load_loss_W=p_load_w,
            load_loss_reference_temperature_C=75.0,
            load_loss_definition="total",
        ),
        winding=WindingInfo(
            hv_conductor_material=hv_mat,
            lv_conductor_material=lv_mat,
            hv_target_current_density_A_mm2=hv_j,
            lv_target_current_density_A_mm2=lv_j
        ),
        core=CoreInfo(
            core_topology=CoreTopology.THREE_LEG,
            number_of_legs=3,
            number_of_windows=2,
            target_max_flux_density_T=target_flux_T,
            stacking_factor=k_stack
        ),
        insulation=InsulationThermalInfo()
    )

if opt_button:
    st.info("🤖 AI Çözücü başlatıldı! Farklı Tesla ve Akım Yoğunluğu (A/mm²) kombinasyonları taranıyor...")
    with st.spinner("Grid Search optimizasyonu çalışıyor... Lütfen bekleyin."):
        import copy
        from transformer_design.calculations.engine import synthesize_transformer

        def eval_func(flux_t, hv_j_test, lv_j_test):
            test_inputs = copy.deepcopy(inputs)
            test_inputs.core.target_max_flux_density_T = flux_t
            test_inputs.winding.hv_target_current_density_A_mm2 = hv_j_test
            test_inputs.winding.lv_target_current_density_A_mm2 = lv_j_test
            return synthesize_transformer(test_inputs, custom_prices, a_factor, b_factor)
            
        try:
            opt_res = run_grid_search_optimizer(eval_func, objective="toc")
            best = opt_res["best_parameters"]
            st.success(f"🏆 En İyi Tasarım Bulundu! \n\nOptimum Akı: **{best['flux_T']} T**, HV J: **{best['hv_j']} A/mm²**, LV J: **{best['lv_j']} A/mm²**")
            st.metric("Optimize Edilmiş TOC Maliyeti", f"${opt_res['best_value']:,.2f}")
            st.balloons()
        except Exception as e:
            st.error(f"Optimizasyon hatası: {str(e)}")

if calc_button:
    with st.spinner("Mühendislik hesaplamaları yapılıyor..."):
        try:
            assumptions = DesignAssumptions()
            
            cg = parse_connection_group(inputs.electrical.connection_group)
            hv_conn_type = cg["hv_connection"]
            lv_conn_type = cg["lv_connection"]
            
            s_rated = Q_(inputs.general.rated_power_kVA, 'kVA')
            v_hv_line = Q_(inputs.electrical.hv_voltage_V, 'V')
            v_lv_line = Q_(inputs.electrical.lv_voltage_V, 'V')
            
            v_hv_phase = get_phase_voltage(v_hv_line, hv_conn_type)
            v_lv_phase = get_phase_voltage(v_lv_line, lv_conn_type)
            
            line_currents = calculate_rated_currents(s_rated, v_hv_line, v_lv_line)
            i_hv_phase = get_phase_current(line_currents["i_hv_line"], hv_conn_type)
            i_lv_phase = get_phase_current(line_currents["i_lv_line"], lv_conn_type)
            
            freq = Q_(inputs.general.rated_frequency_Hz, 'Hz')
            b_target = Q_(inputs.core.target_max_flux_density_T, 'T')
            e_turn_initial = calculate_turn_voltage("empirical", freq, s_rated=s_rated, empirical_coefficient=assumptions.turn_voltage_empirical_coefficient)
            a_core_net = calculate_net_core_area(e_turn_initial, assumptions.emf_waveform_factor, freq, b_target)
            core_geom = calculate_core_geometry(a_core_net, inputs.core.stacking_factor, k_shape=0.85)

            hv_turns = calculate_turns(v_hv_phase, e_turn_initial)
            lv_turns = calculate_turns(v_lv_phase, e_turn_initial)
            
            e_turn_actual = lv_turns["e_turn_actual"]
            b_actual = verify_flux_density(e_turn_actual, assumptions.emf_waveform_factor, freq, a_core_net)
            
            at_check = check_ampere_turns(hv_turns["n_selected"], i_hv_phase, lv_turns["n_selected"], i_lv_phase)
            
            a_hv_min = i_hv_phase / Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2')
            hv_d = math.sqrt(4 * a_hv_min.magnitude / math.pi)
            a_lv_min = i_lv_phase / Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2')
            lv_w = 100.0
            lv_t = a_lv_min.magnitude / lv_w
            
            hv_cond = calculate_conductor_dimensions(i_hv_phase, Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2'), "Round", {"diameter": Q_(hv_d, 'mm')}, 1)
            lv_cond = calculate_conductor_dimensions(i_lv_phase, Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2'), "Foil", {"width": Q_(lv_w, 'mm'), "thickness": Q_(lv_t, 'mm')}, 1)

            # İmalat Çıktıları
            core_steps = calculate_core_steps(core_geom['d_physical'].to('mm').magnitude, n_steps=6)
            # HV için Yuvarlak tel reçetesi
            hv_winding_recipe = calculate_winding_layers(
                total_turns=hv_turns['n_selected'],
                winding_height_mm=380.0,
                wire_dimension_axial_mm=hv_cond['a_min'].to('mm**2').magnitude ** 0.5,
                wire_dimension_radial_mm=hv_cond['a_min'].to('mm**2').magnitude ** 0.5
            )
            # LV için Folyo reçetesi
            lv_winding_recipe = calculate_winding_layers(
                total_turns=lv_turns['n_selected'],
                winding_height_mm=380.0,
                wire_dimension_axial_mm=lv_w,
                wire_dimension_radial_mm=lv_t
            )

            z_pu = inputs.electrical.rated_short_circuit_impedance_percent / 100.0
            sc = calculate_short_circuit(line_currents["i_hv_line"], s_rated, z_pu)
            
            p_nl = Q_(inputs.electrical.no_load_loss_W, 'W')
            p_ll = Q_(inputs.electrical.load_loss_W, 'W')
            eff = calculate_efficiency(s_rated, p_nl, p_ll)
            
            # --- SOĞUTMA VE TERMODİNAMİK ---
            p_total = p_nl + p_ll
            target_dt = Q_(target_oil_rise, 'kelvin')
            k_disp = Q_(heat_dissipation, 'W/(m**2 * kelvin)')
            
            c_w = core_geom['d_physical'] * 3 + Q_(240*2, 'mm')
            c_h = core_geom['d_physical'] + Q_(380, 'mm')
            c_d = core_geom['d_physical'] + Q_(150, 'mm')
            tank_w_mm = core_geom['d_physical'].magnitude + 200
            tank_d_mm = core_geom['d_physical'].magnitude * 3
            tank_h_mm = core_geom['d_physical'].magnitude + 100
            tank_surface = estimate_tank_surface_area(Q_(tank_w_mm, 'mm'), Q_(tank_d_mm, 'mm'), Q_(tank_h_mm, 'mm'))
            tank_volume_m3 = (tank_w_mm / 1000.0) * (tank_d_mm / 1000.0) * (tank_h_mm / 1000.0)
            
            req_area = calculate_required_cooling_area(p_total, target_dt, k_disp)
            cooling_needs = calculate_tank_and_radiator_needs(req_area, tank_surface)
            
            # --- HOT SPOT & RADYATÖR DİLİMLERİ ---
            avg_j = (hv_cond['j_actual'].magnitude + lv_cond['j_actual'].magnitude) / 2.0
            hot_spot = calculate_hot_spot_and_fins(
                radiator_area_needed_m2=cooling_needs['radiator_area_needed'].magnitude,
                top_oil_temp_rise=target_oil_rise,
                j_avg=avg_j
            )
            
            # --- MALIYET VE AĞIRLIK (LME) ---
            cost_weight = calculate_weights_and_costs(
                hv_mat=inputs.winding.hv_conductor_material,
                lv_mat=inputs.winding.lv_conductor_material,
                hv_turns=hv_turns['n_selected'],
                lv_turns=lv_turns['n_selected'],
                hv_area_mm2=hv_cond['a_min'],
                lv_area_mm2=lv_cond['a_min'],
                core_gross_area_mm2=core_geom['a_core_gross'],
                core_diameter_mm=core_geom['d_physical'],
                tank_area_m2=tank_surface,
                tank_volume_m3=tank_volume_m3,
                oil_type_str=oil_type_str,
                custom_prices=custom_prices
            )
            
            # --- TOC HESAPLAMASI ---
            total_factory_cost = cost_weight["costs_usd"]["total"]
            toc_usd = total_factory_cost + (p_no_load_w * a_factor) + (p_load_w * b_factor)
            
            # --- PDF RAPORU ---
            total_weight = cost_weight["weights_kg"]["total"]
            
            # --- MEKANIK (KISA DEVRE KUVVETI) ---
            # Ortalama çap ve mesafeler (Basitleştirilmiş geometri)
            lv_radial = (lv_cond['a_min'].magnitude / 100.0)
            hv_radial = (hv_cond['a_min'].magnitude / 2.0)
            gap_width = 15.0 # mm
            mean_diameter_gap = core_geom['d_physical'].magnitude + 10.0 + lv_radial + (gap_width / 2.0)
            
            mech = calculate_short_circuit_forces(
                s_rated_kva=power_kva,
                v_line_v=v_hv_line_v,
                z_pu=z_pu,
                hv_turns=hv_turns['n_selected'],
                window_height_mm=380.0,
                mean_diameter_mm=mean_diameter_gap
            )
            
            from transformer_design.calculations.electrical import calculate_leakage_impedance
            physical_uk_percent = calculate_leakage_impedance(
                freq_hz=inputs.general.rated_frequency_Hz,
                turns=hv_turns['n_selected'],
                v_phase=v_hv_phase.magnitude,
                s_rated_va_per_phase=(power_kva * 1000) / 3.0,
                h_winding_mm=380.0,
                mean_diameter_gap_mm=mean_diameter_gap,
                gap_width_mm=gap_width,
                lv_thickness_mm=lv_radial,
                hv_thickness_mm=hv_radial
            )
            
            from transformer_design.calculations.acoustics import calculate_acoustic_noise
            acoustics = calculate_acoustic_noise(cost_weight["weights_kg"]["core"], target_flux_T)
            
            # --- DIELEKTRIK (GÜVENLİK BOŞLUKLARI) ---
            dielectric = calculate_clearances(v_hv_line_v, v_lv_line_v)
            
            # --- PDF RAPORU ---
            hv_mat_name = "Bakır" if inputs.winding.hv_conductor_material == ConductorMaterial.COPPER else "Alüminyum"
            lv_mat_name = "Bakır" if inputs.winding.lv_conductor_material == ConductorMaterial.COPPER else "Alüminyum"
            
            pdf_data = {
                "s_rated_kva": power_kva,
                "v_hv": v_hv_line_v,
                "v_lv": v_lv_line_v,
                "uk_percent": uk_percent,
                "p_load_w": p_load_w,
                "p_no_load_w": p_no_load_w,
                "hv_mat": hv_mat_name,
                "lv_mat": lv_mat_name,
                "oil_type": oil_type_str,
                "target_flux_T": target_flux_T,
                "eff": eff['efficiency'],
                "i_hv": line_currents['i_hv_line'].magnitude,
                "i_lv": line_currents['i_lv_line'].magnitude,
                "core_d_mm": core_geom['d_physical'].magnitude,
                "core_a_cm2": core_geom['a_core_gross'].to('cm**2').magnitude,
                "hv_turns": hv_turns['n_selected'],
                "lv_turns": lv_turns['n_selected'],
                "hv_j": hv_cond['j_actual'].magnitude,
                "lv_j": lv_cond['j_actual'].magnitude,
                "rad_fins": hot_spot['num_radiator_fins'],
                "hot_spot_rise": hot_spot['hot_spot_rise_k'],
                "oil_volume": cost_weight['oil_stats']['volume_L'],
                "weight_active": cost_weight['weights_kg']['active_part_untanked'],
                "weight_tank": cost_weight['weights_kg']['tank'],
                "weight_oil": cost_weight['weights_kg']['oil'],
                "weight_total": total_weight,
                "cost_total": total_factory_cost,
                "toc_total": toc_usd,
                "f_radial": mech['f_radial_kN'],
                "clearance": dielectric['phase_to_phase_mm']
            }
            pdf_path = generate_engineering_pdf(pdf_data)

            # --- ARAYÜZ ---
            st.success("Tasarım başarıyla sentezlendi!")
            
            # --- TASARIM KAYDETME (A/B Testi) ---
            design_name = f"{int(power_kva)}kVA {hv_mat_name}-{lv_mat_name}"
            new_design = {
                "Tasarım Adı": design_name,
                "TOC ($)": round(toc_usd, 0),
                "İmalat ($)": round(total_factory_cost, 0),
                "Ağırlık (kg)": round(total_weight, 0),
                "Verim (%)": round(eff['efficiency']*100, 2),
                "Hot-Spot (K)": round(hot_spot['hot_spot_rise_k'], 1)
            }
            # Eğer son kaydedilen tasarımla aynı değilse kaydet
            if not st.session_state['saved_designs'] or st.session_state['saved_designs'][-1] != new_design:
                st.session_state['saved_designs'].append(new_design)
            if len(st.session_state['saved_designs']) > 10:
                st.session_state['saved_designs'].pop(0)

            with open(pdf_path, "rb") as pdf_file:
                st.download_button(label="📄 Mühendislik PDF Raporunu İndir", data=pdf_file, file_name="Trafo_Muhendislik_Raporu.pdf", mime="application/pdf", type="primary")

            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["⚡ Elektriksel", "📐 Geometri", "🔥 Mekanik & Isıl", "💵 Ağırlık & LME Maliyet", "🎨 Görsel Şema", "🖨️ İmalat Reçetesi", "🔄 A/B Kıyaslama"])
            
            with tab1:
                st.subheader("⚡ Akım ve Verim Değerleri")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("HV Anma Akımı", f"{line_currents['i_hv_line'].to('A').magnitude:.2f} A")
                c2.metric("LV Anma Akımı", f"{line_currents['i_lv_line'].to('A').magnitude:.2f} A")
                c3.metric("Spir Başına Gerilim", f"{e_turn_actual.magnitude:.2f} V")
                c4.metric("Tam Yük Verimi", f"%{eff['efficiency']*100:.2f}")
                
                st.subheader("⚡ Fiziksel Empedans")
                c5, c6 = st.columns(2)
                c5.metric("Fiziksel Kısa Devre Empedansı (uk%)", f"%{physical_uk_percent:.2f}", delta=f"{physical_uk_percent - uk_percent:.2f}% FARK", delta_color="inverse", help="Girilen nominal uk% değerine kıyasla, sargı geometrisine (Rogowski katsayısı) göre oluşan gerçek fiziksel kısa devre empedansıdır.")

            with tab2:
                st.subheader("Çekirdek ve Sargı")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Fiziksel Çap (D)", f"{core_geom['d_physical'].to('mm').magnitude:.1f} mm")
                c2.metric("Brüt Çekirdek Alanı", f"{core_geom['a_core_gross'].to('cm**2').magnitude:.1f} cm²")
                c3.metric("HV Sarım Sayısı", f"{hv_turns['n_selected']} tur")
                c4.metric("LV Sarım Sayısı", f"{lv_turns['n_selected']} tur")

            with tab3:
                st.subheader("🔥 Termal İhtiyaçlar")
                t1, t2, t3 = st.columns(3)
                t1.metric("Gerekli Soğutma Alanı", f"{cooling_needs['required_cooling_area'].to('m**2').magnitude:.2f} m²")
                t2.metric("Çıplak Tank Yüzeyi", f"{cooling_needs['tank_surface_area'].to('m**2').magnitude:.2f} m²")
                t3.metric("Ekstra Radyatör İhtiyacı", f"{cooling_needs['radiator_area_needed'].to('m**2').magnitude:.2f} m²")
                
                st.subheader("Dalgalı Duvar (Radyatör) & En Sıcak Nokta")
                h1, h2, h3 = st.columns(3)
                h1.metric("Radyatör Dilim Sayısı", f"{hot_spot['num_radiator_fins']} Adet", help=f"1 dilim yüzey alanı {hot_spot['fin_area_m2']} m² kabul edilmiştir.")
                h2.metric("Sargı-Yağ Sıcaklık Gradyanı", f"{hot_spot['winding_gradient_k']:.1f} K", help="Sargı içi sıcaklığın yağa göre ne kadar daha sıcak olduğu.")
                h3.metric("Sargı İçi En Sıcak Nokta (Hot-Spot)", f"{hot_spot['hot_spot_rise_k']:.1f} K", delta="Kritik Isı Limitine Yakınlık", delta_color="inverse", help="Trafonun izolasyon ömrünü belirleyen en sıcak noktanın ortam sıcaklığına göre artışıdır (IEC 60076-2).")
                
                st.subheader("⚖️ Kısa Devre Mekaniği")
                m1, m2, m3 = st.columns(3)
                m1.metric("Maks Asimetrik Tepe Akımı", f"{mech['i_sc_peak_A']:.0f} A")
                m2.metric("Maks Radyal Kuvvet", f"{mech['f_radial_kN']:.2f} kN", delta="Sargı İtme Kuvveti", delta_color="inverse")
                m3.metric("HV Faz-Toprak Boşluğu", f"{dielectric['phase_to_ground_mm']} mm")
                
                st.subheader("🔊 Akustik Gürültü Seviyesi")
                a1, a2 = st.columns(2)
                a1.metric("Tahmini Ses Gücü (Lw)", f"{acoustics['sound_power_db_a']} dB(A)")
                a2.metric("Tahmini Ses Basıncı (Lp)", f"{acoustics['sound_pressure_db_a']} dB(A)")

            with tab4:
                st.subheader("⚖️ Üretim ve Taşıma Ağırlığı (Kg/Litre)")
                w1, w2, w3, w4 = st.columns(4)
                w1.metric("Aktif Kısım (Çekirdek+Sargı)", f"{cost_weight['weights_kg']['active_part_untanked']:,.1f} kg")
                w2.metric("Dış Tank / Karkas", f"{cost_weight['weights_kg']['tank']:,.1f} kg")
                w3.metric(f"İzolasyon Yağı ({cost_weight['oil_stats']['type']})", f"{cost_weight['weights_kg']['oil']:,.1f} kg", f"{cost_weight['oil_stats']['volume_L']:,.1f} Litre", delta_color="normal")
                w4.metric("Toplam Nakliye Ağırlığı", f"{cost_weight['weights_kg']['total']:,.1f} kg")
                
                st.subheader("💵 Canlı Borsa Üretim Maliyeti (USD)")
                c5, c6, c7, c8 = st.columns(4)
                c5.metric(f"HV Sargı ({hv_mat_str})", f"${cost_weight['costs_usd']['hv_winding']:,.2f}")
                c6.metric(f"LV Sargı ({lv_mat_str})", f"${cost_weight['costs_usd']['lv_winding']:,.2f}")
                c7.metric("Çelik (Tank+Çekirdek)", f"${cost_weight['costs_usd']['core'] + cost_weight['costs_usd']['tank']:,.2f}")
                c8.metric(f"Yağ ({cost_weight['oil_stats']['type']})", f"${cost_weight['costs_usd']['oil']:,.2f}")
                
                c_cost1, c_cost2 = st.columns(2)
                c_cost1.metric("TOPLAM FABRİKA MALİYETİ", f"${total_factory_cost:,.2f}", delta="İmalat Maliyeti")
                c_cost2.metric("TOC (TOPLAM SAHİP OLMA MALİYETİ)", f"${toc_usd:,.2f}", delta=f"+${(p_no_load_w * a_factor) + (p_load_w * b_factor):,.2f} Kayıp Cezası", delta_color="inverse", help="İhale tekliflerinde fiyat avantajı sağlamak için baz alınan 20 yıllık faturası dahil toplam değerdir.")

            with tab5:
                svg_str = generate_transformer_svg(
                    hv_mat=inputs.winding.hv_conductor_material,
                    lv_mat=inputs.winding.lv_conductor_material,
                    hv_turns=hv_turns['n_selected'],
                    lv_turns=lv_turns['n_selected'],
                    hv_area_mm2=hv_cond['a_min'].to('mm**2').magnitude,
                    lv_area_mm2=lv_cond['a_min'].to('mm**2').magnitude,
                    core_diameter_mm=core_geom['d_physical'].to('mm').magnitude
                )
                
                c_svg1, c_svg2, c_svg3 = st.columns([1, 6, 1])
                with c_svg2:
                    st.components.v1.html(svg_str, height=750, scrolling=False)
                    st.markdown("<p style='text-align: center; font-size: 0.9em; color: #666;'><i>(Malzeme rengi, tel kalınlığı ve tur yoğunluğu girdilerinize göre otomatik çizilir)</i></p>", unsafe_allow_html=True)

            with tab6:
                st.subheader("Üretim: Sac Kesim Listesi (Çekirdek)")
                import pandas as pd
                df_core = pd.DataFrame(core_steps)
                df_core.columns = ["Kademe No", "Kesim Genişliği (mm)", "Paket Kalınlığı (mm)", "Tahmini Sac Adeti"]
                st.table(df_core)
                
                st.subheader("Üretim: Sarıcı Ustası İçin Sarım Reçetesi")
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    st.markdown("#### Yüksek Gerilim (HV) Sargısı")
                    st.markdown(f"- **Toplam Tur:** {hv_turns['n_selected']}")
                    st.markdown(f"- **Bir Kata Sığan Tur:** {hv_winding_recipe['turns_per_layer']}")
                    st.markdown(f"- **Toplam Katman (Layer) Sayısı:** {hv_winding_recipe['num_layers']}")
                    st.markdown(f"- **Son Katta Kalan Tur:** {hv_winding_recipe['actual_turns_last_layer']}")
                    st.markdown(f"- **Sargı Et Kalınlığı:** {hv_winding_recipe['radial_build_mm']:.1f} mm")
                
                with col_w2:
                    st.markdown("#### Alçak Gerilim (LV) Sargısı")
                    st.markdown(f"- **Toplam Tur:** {lv_turns['n_selected']}")
                    st.markdown(f"- **Bir Kata Sığan Tur:** {lv_winding_recipe['turns_per_layer']}")
                    st.markdown(f"- **Toplam Katman (Layer) Sayısı:** {lv_winding_recipe['num_layers']}")
                    st.markdown(f"- **Son Katta Kalan Tur:** {lv_winding_recipe['actual_turns_last_layer']}")
                    st.markdown(f"- **Sargı Et Kalınlığı:** {lv_winding_recipe['radial_build_mm']:.1f} mm")

            with tab7:
                st.subheader("🔄 Tasarım Karşılaştırma (A/B Testi)")
                st.markdown("Her 'Hesapla' butonuna bastığınızda tasarımınız buraya kaydedilir. Hangi materyalin veya parametrenin daha karlı olduğunu kıyaslayabilirsiniz.")
                
                if len(st.session_state['saved_designs']) > 0:
                    df_compare = pd.DataFrame(st.session_state['saved_designs'])
                    st.dataframe(df_compare, use_container_width=True)
                    
                    if len(st.session_state['saved_designs']) > 1:
                        st.line_chart(df_compare.set_index("Tasarım Adı")[["TOC ($)", "İmalat ($)"]], height=300)
                else:
                    st.info("Kıyaslama yapabilmek için en az bir kez hesaplama yapmalısınız.")

        except Exception as e:
            import traceback
            st.error(f"Hesaplama sırasında hata: {str(e)}")
            st.expander("Hata Detayı").code(traceback.format_exc())
else:
    st.info("Lütfen soldaki menüden parametreleri belirleyip 'Hesapla' butonuna tıklayın.")
