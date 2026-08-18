from typing import Dict, Any, List
import math

def calculate_turns(v_phase: Any, e_turn_initial: Any) -> Dict[str, Any]:
    """Sargı tur sayısını hesaplar ve yuvarlar."""
    if v_phase.to("V").magnitude <= 0 or e_turn_initial.to("V").magnitude <= 0:
        raise ValueError("Gerilim değerleri pozitif olmalıdır.")
    n_raw = (v_phase / e_turn_initial).to_base_units().magnitude
    n_selected = round(n_raw)
    
    e_turn_actual = v_phase / n_selected
    
    v_actual = n_selected * e_turn_actual
    abs_error = v_actual - v_phase
    rel_error = abs_error / v_phase if v_phase.magnitude != 0 else 0
    
    return {
        "n_raw": n_raw,
        "n_selected": n_selected,
        "e_turn_actual": e_turn_actual,
        "v_actual": v_actual,
        "absolute_error": abs_error,
        "relative_error": rel_error
    }

def calculate_tap_turns(
    v_nominal_phase: Any, 
    e_turn_actual: Any, 
    tap_percentages: List[float], 
    nominal_turns: int
) -> List[Dict[str, Any]]:
    """Kademe tur sayılarını hesaplar."""
    results = []
    for tap in tap_percentages:
        v_tap_phase = v_nominal_phase * (1 + tap / 100.0)
        n_tap_raw = (v_tap_phase / e_turn_actual).to_base_units().magnitude
        n_tap = round(n_tap_raw)
        
        v_actual = n_tap * e_turn_actual
        abs_error = v_actual - v_tap_phase
        rel_error = abs_error / v_tap_phase
        
        results.append({
            "tap_percentage": tap,
            "v_target": v_tap_phase,
            "n_raw": n_tap_raw,
            "n_selected": n_tap,
            "v_actual": v_actual,
            "absolute_error": abs_error,
            "relative_error": rel_error,
            "turns_added_or_removed": n_tap - nominal_turns
        })
    return results

def check_ampere_turns(n_hv: int, i_hv_phase: Any, n_lv: int, i_lv_phase: Any) -> Dict[str, Any]:
    """Amper-sarım dengesini kontrol eder."""
    at_hv = n_hv * i_hv_phase
    at_lv = n_lv * i_lv_phase
    
    diff = at_hv - at_lv
    avg = (at_hv + at_lv) / 2
    rel_diff = abs(diff / avg).to_base_units().magnitude if avg.magnitude != 0 else 0
    
    return {
        "at_hv": at_hv,
        "at_lv": at_lv,
        "absolute_difference": diff,
        "relative_difference": rel_diff
    }

def calculate_conductor_dimensions(
    i_design: Any, 
    j_target: Any, 
    shape: str, 
    dims: Dict[str, Any], 
    parallel_count: int = 1
) -> Dict[str, Any]:
    """İletken kesitini ve gerçek akım yoğunluğunu hesaplar."""
    if i_design.to("A").magnitude <= 0 or j_target.to("A/mm**2").magnitude <= 0:
        raise ValueError("Akım ve akım yoğunluğu pozitif olmalıdır.")
    if parallel_count < 1:
        raise ValueError("Paralel iletken sayısı en az 1 olmalıdır.")
    a_min = i_design / j_target
    
    if shape == "Round":
        d = dims.get('diameter')
        if d is None or d.to("mm").magnitude <= 0:
            raise ValueError("Yuvarlak iletken çapı pozitif olmalıdır.")
        a_single = math.pi * (d ** 2) / 4
    elif shape in ["Rectangular", "Foil"]:
        w = dims.get('width')
        t = dims.get('thickness')
        if w is None or t is None or w.to("mm").magnitude <= 0 or t.to("mm").magnitude <= 0:
            raise ValueError("İletken genişlik ve kalınlığı pozitif olmalıdır.")
        a_single = w * t
    else:
        raise ValueError("Bilinmeyen iletken şekli")
        
    a_selected_total = parallel_count * a_single
    j_actual = i_design / a_selected_total
    
    return {
        "a_min": a_min.to('mm**2'),
        "a_single": a_single.to('mm**2'),
        "a_selected_total": a_selected_total.to('mm**2'),
        "j_actual": j_actual.to('A/mm**2')
    }

def calculate_resistance_and_loss(
    rho_ref: Any, 
    t_ref: Any, 
    t_target: Any, 
    alpha: float, 
    turns: int, 
    mean_length: Any, 
    a_conductor: Any, 
    i_phase: Any, 
    phase_count: int = 3
) -> Dict[str, Any]:
    """Özdirenç, direnç ve DC bakır kaybını hesaplar."""
    delta_t_val = t_target.to('degC').magnitude - t_ref.to('degC').magnitude
    
    rho_target = rho_ref * (1 + alpha * delta_t_val)
    length_total = turns * mean_length
    
    r_dc = rho_target * length_total / a_conductor
    p_dc_winding = phase_count * (i_phase ** 2) * r_dc
    
    return {
        "rho_target": rho_target,
        "length_total": length_total,
        "r_dc": r_dc.to('ohm'),
        "p_dc_winding": p_dc_winding.to('W')
    }

def calculate_winding_layers(
    total_turns: int,
    winding_height_mm: float,
    wire_dimension_axial_mm: float,
    wire_dimension_radial_mm: float,
    margin_mm: float = 15.0,
    paper_thickness_mm: float = 0.2
) -> Dict[str, Any]:
    """
    İmalat için sarım reçetesi (katman sayısı ve katman başına düşen tur) hesaplar.
    wire_dimension_axial: Telin yükseklik (sarım) yönündeki yalıtımlı ölçüsü.
    wire_dimension_radial: Telin kalınlık (radyal) yönündeki yalıtımlı ölçüsü.
    """
    if total_turns <= 0:
        raise ValueError("Toplam tur sayısı pozitif olmalıdır.")
    if min(winding_height_mm, wire_dimension_axial_mm, wire_dimension_radial_mm) <= 0:
        raise ValueError("Sargı geometrisi pozitif olmalıdır.")
    if margin_mm < 0 or paper_thickness_mm < 0:
        raise ValueError("Kenar payı ve kâğıt kalınlığı negatif olamaz.")
    effective_height = winding_height_mm - (2 * margin_mm)
    if effective_height <= 0:
        raise ValueError("Sargı yüksekliği toplam kenar payından büyük olmalıdır.")
    turns_per_layer = math.floor(effective_height / wire_dimension_axial_mm)
    
    if turns_per_layer <= 0:
        turns_per_layer = 1
        
    num_layers = math.ceil(total_turns / turns_per_layer)
    actual_turns_last_layer = total_turns % turns_per_layer
    if actual_turns_last_layer == 0:
        actual_turns_last_layer = turns_per_layer
        
    radial_build_mm = num_layers * (wire_dimension_radial_mm + paper_thickness_mm)
    
    return {
        "turns_per_layer": turns_per_layer,
        "num_layers": num_layers,
        "actual_turns_last_layer": actual_turns_last_layer,
        "radial_build_mm": radial_build_mm
    }
