import sys
import math
from transformer_design.units import Q_
from transformer_design.models.enums import PhaseSystem, CoolingMethod, ConductorMaterial, CoreTopology, DesignStatus, DataSource
from transformer_design.models.inputs import OrderInput, GeneralInfo, ElectricalInfo, WindingInfo, CoreInfo, InsulationThermalInfo
from transformer_design.models.assumptions import DesignAssumptions
from transformer_design.models.results import CalculatedValue
from transformer_design.calculations.connection import parse_connection_group, get_phase_voltage, get_phase_current
from transformer_design.calculations.electrical import calculate_rated_currents, calculate_short_circuit, calculate_efficiency
from transformer_design.calculations.core import calculate_turn_voltage, calculate_net_core_area, calculate_core_geometry, verify_flux_density
from transformer_design.calculations.winding import calculate_turns, check_ampere_turns, calculate_conductor_dimensions
from transformer_design.reporting.report_generator import generate_report

def get_float(prompt: str, default: float) -> float:
    user_input = input(f"{prompt} [Varsayılan: {default}]: ").strip()
    if not user_input:
        return default
    try:
        return float(user_input)
    except ValueError:
        print("Lütfen geçerli bir sayı girin.")
        return get_float(prompt, default)

def get_str(prompt: str, default: str) -> str:
    user_input = input(f"{prompt} [Varsayılan: {default}]: ").strip()
    return user_input if user_input else default

def get_material(prompt: str, default: str) -> ConductorMaterial:
    user_input = input(f"{prompt} (B: Bakır, A: Alüminyum) [Varsayılan: {default}]: ").strip().upper()
    if not user_input:
        user_input = default
    if user_input == 'B':
        return ConductorMaterial.COPPER
    elif user_input == 'A':
        return ConductorMaterial.ALUMINUM
    else:
        print("Hatalı giriş, B veya A giriniz.")
        return get_material(prompt, default)

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print("="*60)
    print("TRANSFORMATÖR ÖN TASARIM UYGULAMASI (CLI)")
    print("="*60)
    
    print("\n--- 1. GENEL VE ELEKTRİKSEL VERİLER ---")
    power_kva = get_float("Anma Gücü (kVA)", 1000.0)
    v_hv_line_v = get_float("Yüksek Gerilim Hat (V)", 33000.0)
    v_lv_line_v = get_float("Alçak Gerilim Hat (V)", 400.0)
    conn_group = get_str("Bağlantı Grubu (Örn: Dyn11, YNd5, Yyn0)", "Dyn11")
    uk_percent = get_float("Kısa Devre Empedansı (%)", 5.0)
    p_no_load_w = get_float("Boşta Kayıp (W)", 1700.0)
    p_load_w = get_float("Yükte Kayıp (W)", 10500.0)
    
    print("\n--- 2. ÇEKİRDEK VE TASARIM KABULLERİ ---")
    target_flux_T = get_float("Hedef Akı Yoğunluğu (T)", 1.6)
    k_stack = get_float("Saç İstifleme Faktörü", 0.96)
    
    print("\n--- 3. SARGI MALZEME VE AKIM YOĞUNLUĞU ---")
    hv_mat = get_material("HV Sargı Malzemesi", "B")
    lv_mat = get_material("LV Sargı Malzemesi", "A")
    hv_j = get_float("HV Hedef Akım Yoğunluğu (A/mm2)", 3.0)
    lv_j = get_float("LV Hedef Akım Yoğunluğu (A/mm2)", 2.5)

    print("\nHesaplamalar yapılıyor...\n")
    
    # Girdileri modeillere aktar
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
            connection_group=conn_group,
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

    assumptions = DesignAssumptions()
    calc_results = []
    
    # 1. Bağlantı Grubunu Çözümle
    cg = parse_connection_group(inputs.electrical.connection_group)
    hv_conn_type = cg["hv_connection"]
    lv_conn_type = cg["lv_connection"]
    
    # 2. Hat -> Faz Gerilim ve Akım Dönüşümleri
    s_rated = Q_(inputs.general.rated_power_kVA, 'kVA')
    v_hv_line = Q_(inputs.electrical.hv_voltage_V, 'V')
    v_lv_line = Q_(inputs.electrical.lv_voltage_V, 'V')
    
    v_hv_phase = get_phase_voltage(v_hv_line, hv_conn_type)
    v_lv_phase = get_phase_voltage(v_lv_line, lv_conn_type)
    
    # 3. Güçten Hat Akımlarını Bul ve Faza Çevir
    line_currents = calculate_rated_currents(s_rated, v_hv_line, v_lv_line)
    i_hv_phase = get_phase_current(line_currents["i_hv_line"], hv_conn_type)
    i_lv_phase = get_phase_current(line_currents["i_lv_line"], lv_conn_type)
    
    # 4. Tur Başına Gerilim (Ampirik) ve Çekirdek Kesiti
    freq = Q_(inputs.general.rated_frequency_Hz, 'Hz')
    b_target = Q_(inputs.core.target_max_flux_density_T, 'T')
    e_turn_initial = calculate_turn_voltage("empirical", freq, s_rated=s_rated, empirical_coefficient=assumptions.turn_voltage_empirical_coefficient)
    a_core_net = calculate_net_core_area(e_turn_initial, assumptions.emf_waveform_factor, freq, b_target)
    core_geom = calculate_core_geometry(a_core_net, inputs.core.stacking_factor, k_shape=0.85)

    # 5. Tur Sayıları
    hv_turns = calculate_turns(v_hv_phase, e_turn_initial)
    lv_turns = calculate_turns(v_lv_phase, e_turn_initial)
    
    # 6. Gerçek E_turn ve Gerçek Akı Yoğunluğu (LV Sargısı baz alınarak)
    e_turn_actual = lv_turns["e_turn_actual"]
    b_actual = verify_flux_density(e_turn_actual, assumptions.emf_waveform_factor, freq, a_core_net)

    # 7. Amper-Sarım Kontrolü
    at_check = check_ampere_turns(hv_turns["n_selected"], i_hv_phase, lv_turns["n_selected"], i_lv_phase)
    
    # 8. İletken Min. Kesitleri
    a_hv_min = i_hv_phase / Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2')
    hv_d = math.sqrt(4 * a_hv_min.magnitude / math.pi)
    
    a_lv_min = i_lv_phase / Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2')
    lv_w = 100.0
    lv_t = a_lv_min.magnitude / lv_w
    
    hv_cond = calculate_conductor_dimensions(i_hv_phase, Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2'), "Round", {"diameter": Q_(hv_d, 'mm')}, 1)
    lv_cond = calculate_conductor_dimensions(i_lv_phase, Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2'), "Foil", {"width": Q_(lv_w, 'mm'), "thickness": Q_(lv_t, 'mm')}, 1)

    # 9. Kısa Devre & Verim
    z_pu = inputs.electrical.rated_short_circuit_impedance_percent / 100.0
    sc = calculate_short_circuit(line_currents["i_hv_line"], s_rated, z_pu)
    
    p_nl = Q_(inputs.electrical.no_load_loss_W, 'W')
    p_ll = Q_(inputs.electrical.load_loss_W, 'W')
    eff = calculate_efficiency(s_rated, p_nl, p_ll)

    # Sonucları Listeye Ekle
    def add_res(name, sym, val, unit=""):
        calc_results.append(CalculatedValue(name=name, symbol=sym, value=None, display_value=val, unit=unit, source=DataSource.CALCULATED, formula=""))

    add_res("Bağlantı Faz Kayması (Derece)", "theta_shift", cg["phase_shift_deg"], "derece")
    add_res("HV Faz Gerilimi", "V_hv_phase", round(v_hv_phase.to('V').magnitude, 1), "V")
    add_res("LV Faz Gerilimi", "V_lv_phase", round(v_lv_phase.to('V').magnitude, 1), "V")
    add_res("HV Faz Akımı", "I_hv_phase", round(i_hv_phase.to('A').magnitude, 2), "A")
    add_res("LV Faz Akımı", "I_lv_phase", round(i_lv_phase.to('A').magnitude, 2), "A")
    
    add_res("Çekirdek Net Kesiti", "A_core_net", round(a_core_net.to('cm**2').magnitude, 2), "cm2")
    add_res("Çekirdek Dış Çapı", "D_core", round(core_geom["d_physical"].to('mm').magnitude, 1), "mm")
    add_res("Gerçek Akı Yoğunluğu", "B_actual", round(b_actual.to('T').magnitude, 4), "T")
    
    add_res("HV Tur Sayısı", "N_hv", hv_turns["n_selected"], "Tur")
    add_res("LV Tur Sayısı", "N_lv", lv_turns["n_selected"], "Tur")
    add_res("Amper-Sarım Farkı", "AT_diff", round(at_check["absolute_difference"].to('A').magnitude, 2), "A-Tur")
    
    add_res("HV İletken Min. Kesit", "A_hv_min", round(hv_cond["a_min"].to('mm**2').magnitude, 2), "mm2")
    add_res("LV İletken Min. Kesit", "A_lv_min", round(lv_cond["a_min"].to('mm**2').magnitude, 2), "mm2")
    
    add_res("Tam Yükte Verim", "eta", round(eff["efficiency"] * 100, 3), "%")
    add_res("Maksimum Kısa Devre Gücü", "S_sc", round(sc["s_sc"].to('MVA').magnitude, 2), "MVA")
        
    # Rapor
    report = generate_report(inputs, assumptions, DesignStatus.ELECTRICAL_PRE_DESIGN, calc_results)
    print("\n" + "="*60)
    print(report)
    print("="*60)
    print("\nTasarım başarıyla tamamlandı.")
    
    # Kullanıcı uygulamayı çift tıklayarak açtıysa pencerenin hemen kapanmaması için bekleme ekliyoruz.
    input("\nÇıkmak için Enter tuşuna basın...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("crash.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"\nBeklenmeyen bir hata oluştu! Hata detayı 'crash.log' dosyasına kaydedildi.")
        print(f"Hata: {e}")
