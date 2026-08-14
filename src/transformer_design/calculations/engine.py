import math
from typing import Dict, Any

from .core import calculate_turn_voltage, calculate_net_core_area, calculate_core_geometry, verify_flux_density, calculate_core_steps
from .winding import calculate_turns, check_ampere_turns, calculate_conductor_dimensions, calculate_winding_layers
from .connection import parse_connection_group, get_phase_voltage, get_phase_current
from .electrical import calculate_rated_currents, calculate_short_circuit, calculate_efficiency, calculate_leakage_impedance
from .acoustics import calculate_acoustic_noise
from .thermal import calculate_required_cooling_area, estimate_tank_surface_area, calculate_tank_and_radiator_needs, calculate_hot_spot_and_fins
from .costing import calculate_weights_and_costs
from .mechanical import calculate_short_circuit_forces
from .dielectric import calculate_clearances
from ..models.inputs import OrderInput
from ..models.enums import ConductorMaterial
from ..units import Q_

def synthesize_transformer(
    inputs: OrderInput,
    custom_prices: Dict[str, float] = None,
    a_factor: float = 8.0,
    b_factor: float = 2.0
) -> Dict[str, Any]:
    
    power_kva = inputs.general.rated_power_kVA
    v_hv_line_v = inputs.electrical.hv_voltage_V
    v_lv_line_v = inputs.electrical.lv_voltage_V
    freq_hz = inputs.general.rated_frequency_Hz
    
    s_rated = Q_(power_kva, 'kVA')
    v_hv_line = Q_(v_hv_line_v, 'V')
    v_lv_line = Q_(v_lv_line_v, 'V')
    freq = Q_(freq_hz, 'Hz')
    
    b_target = Q_(inputs.core.target_max_flux_density_T, 'T')
    e_turn_initial = calculate_turn_voltage("empirical", freq, s_rated=s_rated, empirical_coefficient=0.45)
    a_core_net = calculate_net_core_area(e_turn_initial, 1.11, freq, b_target)
    core_geom = calculate_core_geometry(a_core_net, inputs.core.stacking_factor, k_shape=0.85)
    
    line_currents = calculate_rated_currents(s_rated, v_hv_line, v_lv_line)
    i_hv_line = line_currents["i_hv_line"]
    i_lv_line = line_currents["i_lv_line"]
    
    # Dinamik Faz/Hat Dönüşümü (Dyn11, Yyn0 vb.)
    cg_info = parse_connection_group(inputs.electrical.connection_group)
    
    v_hv_phase = get_phase_voltage(v_hv_line, cg_info["hv_connection"])
    v_lv_phase = get_phase_voltage(v_lv_line, cg_info["lv_connection"])
    
    i_hv_phase = get_phase_current(i_hv_line, cg_info["hv_connection"])
    i_lv_phase = get_phase_current(i_lv_line, cg_info["lv_connection"])
    
    hv_turns = calculate_turns(v_hv_phase, e_turn_initial)
    lv_turns = calculate_turns(v_lv_phase, e_turn_initial)
    
    a_hv_min = i_hv_phase / Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2')
    hv_d = math.sqrt(4 * a_hv_min.magnitude / math.pi)
    a_lv_min = i_lv_phase / Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2')
    lv_w = 100.0
    lv_t = a_lv_min.magnitude / lv_w
    
    hv_cond = calculate_conductor_dimensions(i_hv_phase, Q_(inputs.winding.hv_target_current_density_A_mm2, 'A/mm**2'), "Round", {"diameter": Q_(hv_d, 'mm')}, 1)
    lv_cond = calculate_conductor_dimensions(i_lv_phase, Q_(inputs.winding.lv_target_current_density_A_mm2, 'A/mm**2'), "Foil", {"width": Q_(lv_w, 'mm'), "thickness": Q_(lv_t, 'mm')}, 1)
    
    p_nl = Q_(inputs.electrical.no_load_loss_W, 'W')
    p_ll = Q_(inputs.electrical.load_loss_W, 'W')
    eff = calculate_efficiency(s_rated, p_nl, p_ll)
    p_total = p_nl + p_ll
    
    tank_w_mm = core_geom['d_physical'].magnitude + 200
    tank_d_mm = core_geom['d_physical'].magnitude * 3
    tank_h_mm = core_geom['d_physical'].magnitude + 100
    tank_surface = estimate_tank_surface_area(Q_(tank_w_mm, 'mm'), Q_(tank_d_mm, 'mm'), Q_(tank_h_mm, 'mm'))
    tank_volume_m3 = (tank_w_mm / 1000.0) * (tank_d_mm / 1000.0) * (tank_h_mm / 1000.0)
    
    req_area = calculate_required_cooling_area(p_total, Q_(60.0, 'kelvin'), Q_(12.5, 'W/(m**2 * kelvin)'))
    cooling_needs = calculate_tank_and_radiator_needs(req_area, tank_surface)
    
    avg_j = (hv_cond['j_actual'].magnitude + lv_cond['j_actual'].magnitude) / 2.0
    hot_spot = calculate_hot_spot_and_fins(
        radiator_area_needed_m2=cooling_needs['radiator_area_needed'].magnitude,
        top_oil_temp_rise=60.0,
        j_avg=avg_j
    )
    
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
        oil_type_str="Mineral Yağ (0.89 kg/L)",
        custom_prices=custom_prices
    )
    
    # Fiziksel uk% Hesaplama
    # Ortalama çap ve mesafeler için yaklaşık kabuller (Basitleştirilmiş geometri)
    lv_radial = (lv_cond['a_min'].magnitude / 100.0)
    hv_radial = (hv_cond['a_min'].magnitude / 2.0)
    gap_width = 15.0 # mm
    mean_diameter_gap = core_geom['d_physical'].magnitude + 10.0 + lv_radial + (gap_width / 2.0)
    
    physical_uk = calculate_leakage_impedance(
        freq_hz=freq_hz,
        turns=hv_turns['n_selected'],
        v_phase=v_hv_phase.magnitude,
        s_rated_va_per_phase=(power_kva * 1000) / 3.0,
        h_winding_mm=380.0, # Yaklaşık aktif pencere yüksekliği
        mean_diameter_gap_mm=mean_diameter_gap,
        gap_width_mm=gap_width,
        lv_thickness_mm=lv_radial,
        hv_thickness_mm=hv_radial
    )
    
    # Akustik Gürültü Hesaplama
    acoustics = calculate_acoustic_noise(cost_weight["weights_kg"]["core"], inputs.core.target_max_flux_density_T)
    
    total_factory_cost = cost_weight["costs_usd"]["total"]
    toc_usd = total_factory_cost + (p_nl.magnitude * a_factor) + (p_ll.magnitude * b_factor)
    
    return {
        "toc_usd": toc_usd,
        "total_factory_cost": total_factory_cost,
        "total_weight": cost_weight["weights_kg"]["total"],
        "cost_weight": cost_weight,
        "core_geom": core_geom,
        "hv_turns": hv_turns,
        "lv_turns": lv_turns,
        "hv_cond": hv_cond,
        "lv_cond": lv_cond,
        "line_currents": line_currents,
        "eff": eff,
        "hot_spot": hot_spot,
        "tank_surface": tank_surface,
        "p_nl_w": p_nl.magnitude,
        "p_ll_w": p_ll.magnitude,
        "physical_uk_percent": physical_uk,
        "acoustics": acoustics
    }
