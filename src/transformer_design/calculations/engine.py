"""Single orchestration layer for a complete transformer pre-design run."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from ..models.assumptions import DesignAssumptions
from ..models.enums import CoreTopology, PhaseSystem, LossEvaluationMode
from ..models.inputs import OrderInput
from ..units import Q_
from .acoustics import calculate_acoustic_noise
from .connection import get_phase_current, get_phase_voltage, parse_connection_group
from .core import (
    calculate_core_geometry,
    calculate_core_steps,
    calculate_net_core_area,
    calculate_turn_voltage,
    verify_flux_density,
)
from .costing import OIL_TYPES, calculate_weights_and_costs
from .dielectric import calculate_clearances
from .electrical import (
    calculate_efficiency,
    calculate_leakage_impedance,
    calculate_rated_currents,
    calculate_short_circuit,
)
from .mechanical import calculate_short_circuit_forces
from .losses import (
    calculate_dc_resistance,
    calculate_i2r_losses,
    calculate_load_losses,
    estimate_core_losses,
)
from .taps import calculate_tap_turns, calculate_voltage_regulation

from .thermal import (
    calculate_hot_spot_and_fins,
    calculate_required_cooling_area,
    calculate_tank_and_radiator_needs,
    estimate_tank_surface_area,
)
from .winding import (
    calculate_conductor_dimensions,
    calculate_turns,
    calculate_winding_layers,
    check_ampere_turns,
)


def synthesize_transformer(
    inputs: OrderInput,
    custom_prices: Mapping[str, float] | None = None,
    a_factor: float = 8.0,
    b_factor: float = 2.0,
    *,
    assumptions: DesignAssumptions | None = None,
    oil_type_str: str | None = None,
    heat_dissipation_w_m2k: float = 12.5,
) -> dict[str, Any]:
    """Run the complete deterministic screening calculation.

    All front ends use this function so the web UI, optimizer and programmatic API
    cannot silently apply different engineering constants.
    """
    if inputs.general.phase_system != PhaseSystem.THREE_PHASE:
        raise ValueError("Bu sürüm yalnızca üç fazlı tasarımları destekler.")
    if inputs.core.core_topology != CoreTopology.THREE_LEG:
        raise ValueError("Bu sürümün geometri motoru yalnızca üç bacaklı çekirdeği destekler.")
    if a_factor < 0 or b_factor < 0:
        raise ValueError("TOC A/B faktörleri negatif olamaz.")
    if heat_dissipation_w_m2k <= 0:
        raise ValueError("Isı yayılım katsayısı pozitif olmalıdır.")

    assumptions = assumptions or DesignAssumptions()
    oil_type = oil_type_str or inputs.insulation.oil_type or next(iter(OIL_TYPES))
    power_kva = inputs.general.rated_power_kVA
    frequency_hz = inputs.general.rated_frequency_Hz
    winding_height_mm = min(
        inputs.winding.hv_winding_height_mm,
        inputs.winding.lv_winding_height_mm,
    )

    rated_power = Q_(power_kva, "kVA")
    hv_line_voltage = Q_(inputs.electrical.hv_voltage_V, "V")
    lv_line_voltage = Q_(inputs.electrical.lv_voltage_V, "V")
    frequency = Q_(frequency_hz, "Hz")
    target_flux = Q_(inputs.core.target_max_flux_density_T, "T")

    connection = parse_connection_group(inputs.electrical.connection_group)
    hv_phase_voltage = get_phase_voltage(hv_line_voltage, connection["hv_connection"])
    lv_phase_voltage = get_phase_voltage(lv_line_voltage, connection["lv_connection"])
    line_currents = calculate_rated_currents(rated_power, hv_line_voltage, lv_line_voltage)
    hv_phase_current = get_phase_current(
        line_currents["i_hv_line"], connection["hv_connection"]
    )
    lv_phase_current = get_phase_current(
        line_currents["i_lv_line"], connection["lv_connection"]
    )

    turn_voltage = calculate_turn_voltage(
        assumptions.turn_voltage_selection_method,
        frequency,
        s_rated=rated_power,
        empirical_coefficient=assumptions.turn_voltage_empirical_coefficient,
    )
    net_core_area = calculate_net_core_area(
        turn_voltage,
        assumptions.emf_waveform_factor,
        frequency,
        target_flux,
    )
    core_geometry = calculate_core_geometry(
        net_core_area,
        inputs.core.stacking_factor,
        assumptions.stepped_core_shape_factor,
    )
    hv_turns = calculate_turns(hv_phase_voltage, turn_voltage)
    lv_turns = calculate_turns(lv_phase_voltage, turn_voltage)
    actual_flux = verify_flux_density(
        lv_turns["e_turn_actual"],
        assumptions.emf_waveform_factor,
        frequency,
        net_core_area,
    )
    ampere_turns = check_ampere_turns(
        hv_turns["n_selected"],
        hv_phase_current,
        lv_turns["n_selected"],
        lv_phase_current,
    )

    hv_current_density = Q_(
        inputs.winding.hv_target_current_density_A_mm2, "A/mm**2"
    )
    lv_current_density = Q_(
        inputs.winding.lv_target_current_density_A_mm2, "A/mm**2"
    )
    hv_area = hv_phase_current / hv_current_density
    hv_single_area_mm2 = (
        hv_area.to("mm**2").magnitude / inputs.winding.hv_parallel_conductors
    )
    hv_diameter_mm = math.sqrt(4.0 * hv_single_area_mm2 / math.pi)
    lv_area = lv_phase_current / lv_current_density
    lv_foil_width_mm = min(100.0, winding_height_mm - 30.0)
    if lv_foil_width_mm <= 0:
        raise ValueError("Sargı yüksekliği üretim kenar paylarından büyük olmalıdır.")
    lv_foil_thickness_mm = (
        lv_area.to("mm**2").magnitude
        / inputs.winding.lv_parallel_conductors
        / lv_foil_width_mm
    )

    hv_conductor = calculate_conductor_dimensions(
        hv_phase_current,
        hv_current_density,
        "Round",
        {"diameter": Q_(hv_diameter_mm, "mm")},
        inputs.winding.hv_parallel_conductors,
    )
    lv_conductor = calculate_conductor_dimensions(
        lv_phase_current,
        lv_current_density,
        "Foil",
        {
            "width": Q_(lv_foil_width_mm, "mm"),
            "thickness": Q_(lv_foil_thickness_mm, "mm"),
        },
        inputs.winding.lv_parallel_conductors,
    )
    hv_winding_recipe = calculate_winding_layers(
        hv_turns["n_selected"],
        inputs.winding.hv_winding_height_mm,
        hv_diameter_mm,
        hv_diameter_mm,
    )
    lv_winding_recipe = calculate_winding_layers(
        lv_turns["n_selected"],
        inputs.winding.lv_winding_height_mm,
        lv_foil_width_mm,
        lv_foil_thickness_mm,
    )

    impedance_pu = inputs.electrical.rated_short_circuit_impedance_percent / 100.0
    short_circuit = calculate_short_circuit(
        line_currents["i_hv_line"], rated_power, impedance_pu
    )

    core_diameter_mm = core_geometry["d_physical"].to("mm").magnitude
    lv_radial_build_mm = lv_winding_recipe["radial_build_mm"]
    hv_radial_build_mm = hv_winding_recipe["radial_build_mm"]
    winding_gap_mm = 15.0
    active_width_mm = 3 * core_diameter_mm + 2 * 240.0
    active_height_mm = core_diameter_mm + winding_height_mm
    active_depth_mm = (
        core_diameter_mm
        + 2 * (10.0 + lv_radial_build_mm + winding_gap_mm + hv_radial_build_mm)
    )
    tank_surface = estimate_tank_surface_area(
        Q_(active_width_mm, "mm"),
        Q_(active_height_mm, "mm"),
        Q_(active_depth_mm, "mm"),
    )
    tank_volume_m3 = (
        (active_width_mm + 200.0)
        * (active_height_mm + 200.0)
        * (active_depth_mm + 200.0)
        * 1e-9
    )

    costs = calculate_weights_and_costs(
        inputs.winding.hv_conductor_material,
        inputs.winding.lv_conductor_material,
        hv_turns["n_selected"],
        lv_turns["n_selected"],
        hv_conductor["a_selected_total"],
        lv_conductor["a_selected_total"],
        core_geometry["a_core_gross"],
        core_geometry["d_physical"],
        tank_surface,
        tank_volume_m3=tank_volume_m3,
        oil_type_str=oil_type,
        window_height_mm=winding_height_mm,
        custom_prices=custom_prices,
        lv_radial_build_mm=lv_radial_build_mm,
        hv_radial_build_mm=hv_radial_build_mm,
    )

    mean_gap_diameter_mm = (
        core_diameter_mm + 20.0 + 2 * lv_radial_build_mm + winding_gap_mm
    )
    physical_impedance_percent = calculate_leakage_impedance(
        frequency_hz,
        hv_turns["n_selected"],
        hv_phase_voltage.magnitude,
        power_kva * 1000.0 / 3.0,
        winding_height_mm,
        mean_gap_diameter_mm,
        winding_gap_mm,
        lv_radial_build_mm,
        hv_radial_build_mm,
    )
    lv_mtl = inputs.winding.lv_mean_turn_length_m
    if lv_mtl is None:
        lv_mtl = math.pi * (core_diameter_mm + 20.0 + lv_radial_build_mm) / 1000.0
    hv_mtl = inputs.winding.hv_mean_turn_length_m
    if hv_mtl is None:
        hv_mtl = math.pi * (core_diameter_mm + 20.0 + 2 * lv_radial_build_mm + 2 * winding_gap_mm + hv_radial_build_mm) / 1000.0

    lv_r_dc = calculate_dc_resistance(
        lv_turns["n_selected"], lv_mtl, lv_conductor["a_selected_total"].to("mm**2").magnitude, inputs.winding.lv_conductor_material
    )
    hv_r_dc = calculate_dc_resistance(
        hv_turns["n_selected"], hv_mtl, hv_conductor["a_selected_total"].to("mm**2").magnitude, inputs.winding.hv_conductor_material
    )

    lv_i2r = calculate_i2r_losses(lv_phase_current.magnitude, lv_r_dc)
    hv_i2r = calculate_i2r_losses(hv_phase_current.magnitude, hv_r_dc)

    calc_load_losses_dict = calculate_load_losses(
        hv_i2r, lv_i2r, inputs.winding.additional_load_loss_factor
    )
    calc_no_load_loss_W = estimate_core_losses(
        costs["weights_kg"]["core"],
        actual_flux.to("T").magnitude,
        frequency_hz,
        inputs.core.core_steel_grade,
        inputs.core.additional_no_load_loss_factor
    )

    calculated_losses = {
        "lv_mean_turn_length_m": lv_mtl,
        "hv_mean_turn_length_m": hv_mtl,
        "lv_r_dc_ohms": lv_r_dc,
        "hv_r_dc_ohms": hv_r_dc,
        **calc_load_losses_dict,
        "calculated_no_load_loss_W": calc_no_load_loss_W,
    }

    if inputs.electrical.loss_evaluation_mode == LossEvaluationMode.CALCULATED:
        eval_no_load_loss_W = calc_no_load_loss_W
        eval_load_loss_W = calc_load_losses_dict["calculated_load_loss_W"]
    else:
        eval_no_load_loss_W = inputs.electrical.no_load_loss_W
        eval_load_loss_W = inputs.electrical.load_loss_W

    no_load_loss = Q_(eval_no_load_loss_W, "W")
    load_loss = Q_(eval_load_loss_W, "W")
    total_loss = no_load_loss + load_loss
    efficiency = calculate_efficiency(rated_power, no_load_loss, load_loss)

    required_cooling_area = calculate_required_cooling_area(
        total_loss,
        Q_(inputs.insulation.top_oil_temp_rise_limit_K, "kelvin"),
        Q_(heat_dissipation_w_m2k, "W/(m**2 * kelvin)"),
    )
    cooling = calculate_tank_and_radiator_needs(required_cooling_area, tank_surface)
    average_current_density = (
        hv_conductor["j_actual"].magnitude + lv_conductor["j_actual"].magnitude
    ) / 2.0
    hot_spot = calculate_hot_spot_and_fins(
        cooling["radiator_area_needed"].magnitude,
        inputs.insulation.top_oil_temp_rise_limit_K,
        average_current_density,
    )
    hot_spot_temperature_c = (
        inputs.general.ambient_temperature_C + hot_spot["hot_spot_rise_k"]
    )

    tap_results = {}
    if inputs.electrical.tap_percentages is not None:
        tap_results = calculate_tap_turns(hv_turns["n_selected"], inputs.electrical.tap_percentages)
    
    u_r_percent = (eval_load_loss_W / (power_kva * 1000.0)) * 100.0
    voltage_regulation = calculate_voltage_regulation(physical_impedance_percent, u_r_percent)

    mechanical = calculate_short_circuit_forces(
        power_kva,
        inputs.electrical.hv_voltage_V,
        impedance_pu,
        hv_turns["n_selected"],
        winding_height_mm,
        mean_gap_diameter_mm,
    )
    dielectric = calculate_clearances(
        inputs.electrical.hv_voltage_V, inputs.electrical.lv_voltage_V
    )
    acoustics = calculate_acoustic_noise(
        costs["weights_kg"]["core"], actual_flux.to("T").magnitude
    )

    target_impedance = inputs.electrical.rated_short_circuit_impedance_percent
    impedance_tolerance = max(0.5, target_impedance * 0.15)
    design_checks = {
        "flux_density": actual_flux.to("T").magnitude <= 1.75,
        "ampere_turn_balance": ampere_turns["relative_difference"] <= 0.02,
        "impedance_screening": abs(physical_impedance_percent - target_impedance)
        <= impedance_tolerance,
        "hot_spot_temperature": hot_spot_temperature_c
        <= inputs.insulation.allowed_hot_spot_temp_C,
    }
    warning_messages = {
        "flux_density": "Gerçek akı yoğunluğu 1.75 T tarama sınırını aşıyor.",
        "ampere_turn_balance": "HV/LV amper-sarım farkı %2 sınırını aşıyor.",
        "impedance_screening": "Geometrik uk% tahmini hedef toleransın dışında.",
        "hot_spot_temperature": "Tahmini hot-spot sıcaklığı izin verilen sınırı aşıyor.",
    }
    warnings = [message for key, message in warning_messages.items() if not design_checks[key]]

    if inputs.electrical.no_load_loss_W > 0:
        if abs(calc_no_load_loss_W - inputs.electrical.no_load_loss_W) / inputs.electrical.no_load_loss_W > 0.10:
            warnings.append(f"Hesaplanan boşta kayıp ({calc_no_load_loss_W:.1f} W) garanti edilenden %10'dan fazla sapıyor.")
    
    if inputs.electrical.load_loss_W > 0:
        if abs(calc_load_losses_dict["calculated_load_loss_W"] - inputs.electrical.load_loss_W) / inputs.electrical.load_loss_W > 0.10:
            warnings.append(f"Hesaplanan yük kaybı ({calc_load_losses_dict['calculated_load_loss_W']:.1f} W) garanti edilenden %10'dan fazla sapıyor.")


    factory_cost = costs["costs_usd"]["total"]
    toc_usd = (
        factory_cost
        + eval_no_load_loss_W * a_factor
        + eval_load_loss_W * b_factor
    )
    return {
        "inputs": inputs,
        "assumptions": assumptions,
        "connection": connection,
        "phase_values": {
            "hv_voltage": hv_phase_voltage,
            "lv_voltage": lv_phase_voltage,
            "hv_current": hv_phase_current,
            "lv_current": lv_phase_current,
        },
        "line_currents": line_currents,
        "turn_voltage": turn_voltage,
        "net_core_area": net_core_area,
        "core_geom": core_geometry,
        "actual_flux_density": actual_flux,
        "core_steps": calculate_core_steps(core_diameter_mm),
        "hv_turns": hv_turns,
        "lv_turns": lv_turns,
        "ampere_turns": ampere_turns,
        "hv_cond": hv_conductor,
        "lv_cond": lv_conductor,
        "hv_winding_recipe": hv_winding_recipe,
        "lv_winding_recipe": lv_winding_recipe,
        "eff": efficiency,
        "short_circuit": short_circuit,
        "physical_uk_percent": physical_impedance_percent,
        "tank_surface": tank_surface,
        "tank_volume_m3": tank_volume_m3,
        "cooling": cooling,
        "hot_spot": hot_spot,
        "hot_spot_temperature_c": hot_spot_temperature_c,
        "cost_weight": costs,
        "total_factory_cost": factory_cost,
        "toc_usd": toc_usd,
        "total_weight": costs["weights_kg"]["total"],
        "mechanical": mechanical,
        "dielectric": dielectric,
        "acoustics": acoustics,
        "p_nl_w": eval_no_load_loss_W,
        "p_ll_w": eval_load_loss_W,
        "oil_type": oil_type,
        "design_checks": design_checks,
        "is_feasible": all(design_checks.values()),
        "warnings": warnings,
        "calculated_losses": calculated_losses,
        "taps": tap_results,
        "voltage_regulation": voltage_regulation,
    }
