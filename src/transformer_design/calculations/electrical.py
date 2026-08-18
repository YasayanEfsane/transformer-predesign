from typing import Dict, Any, Optional
from ..exceptions import PhysicallyInconsistentDataError
import math

def calculate_rated_currents(s_rated: Any, v_hv_line: Any, v_lv_line: Any) -> Dict[str, Any]:
    """Hat akımlarını hesaplar."""
    if s_rated.to("VA").magnitude <= 0:
        raise ValueError("Anma gücü pozitif olmalıdır.")
    if v_hv_line.to("V").magnitude <= 0 or v_lv_line.to("V").magnitude <= 0:
        raise ValueError("Hat gerilimleri pozitif olmalıdır.")
    i_hv_line = s_rated / (v_hv_line * (3 ** 0.5))
    i_lv_line = s_rated / (v_lv_line * (3 ** 0.5))
    return {
        "i_hv_line": i_hv_line,
        "i_lv_line": i_lv_line
    }

def calculate_impedance_components(
    s_rated: Any, 
    v_phase: Any, 
    i_phase: Any, 
    p_load_rated: Any, 
    u_k_percent: float,
    is_load_loss_total: bool = True
) -> Dict[str, Any]:
    """Empedans bileşenlerini hesaplar (pu ve ohm olarak)."""
    z_pu = u_k_percent / 100.0
    if not 0 < u_k_percent <= 100:
        raise ValueError("Kısa devre empedansı 0 ile 100 yüzde arasında olmalıdır.")
    if s_rated.to("VA").magnitude <= 0:
        raise ValueError("Anma gücü pozitif olmalıdır.")
    total_load_loss_w = p_load_rated.to('W').magnitude
    if not is_load_loss_total:
        total_load_loss_w *= 3
    if total_load_loss_w < 0:
        raise ValueError("Yük kaybı negatif olamaz.")
    r_pu = total_load_loss_w / s_rated.to('VA').magnitude
        
    if r_pu > z_pu:
        raise PhysicallyInconsistentDataError(f"Direnç bileşeni ({r_pu}) toplam empedanstan ({z_pu}) büyük olamaz.")
        
    x_pu = math.sqrt(z_pu**2 - r_pu**2)
    z_base = v_phase / i_phase
    
    r_eq = r_pu * z_base
    x_eq = x_pu * z_base
    z_eq = z_pu * z_base
    
    return {
        "z_pu": z_pu,
        "r_pu": r_pu,
        "x_pu": x_pu,
        "z_base": z_base,
        "r_eq": r_eq,
        "x_eq": x_eq,
        "z_eq": z_eq
    }

def calculate_short_circuit(i_rated_line: Any, s_rated: Any, z_pu: float) -> Dict[str, Any]:
    """Sonsuz güçlü şebeke kabulüyle kısa devre akımını ve gücünü hesaplar."""
    if z_pu <= 0:
        raise ValueError("Birim kısa devre empedansı pozitif olmalıdır.")
    i_sc_line = i_rated_line / z_pu
    s_sc = s_rated / z_pu
    return {
        "i_sc_line": i_sc_line,
        "s_sc": s_sc
    }

def calculate_efficiency(
    s_rated: Any, 
    p_no_load: Any, 
    p_load_rated: Any, 
    load_fraction: float = 1.0, 
    power_factor: float = 1.0
) -> Dict[str, Any]:
    """Verim hesaplar."""
    if not 0 < load_fraction <= 2:
        raise ValueError("Yük katsayısı 0 ile 2 arasında olmalıdır.")
    if not 0 < power_factor <= 1:
        raise ValueError("Güç faktörü 0 ile 1 arasında olmalıdır.")
    if p_no_load.to("W").magnitude < 0 or p_load_rated.to("W").magnitude <= 0:
        raise ValueError("Kayıplar fiziksel olarak geçerli olmalıdır.")
    p_output = s_rated.to('W') * load_fraction * power_factor
    p_load_at_fraction = p_load_rated * (load_fraction ** 2)
    
    total_losses = p_no_load + p_load_at_fraction
    eta = p_output / (p_output + total_losses)
    
    load_fraction_max_eta = math.sqrt(p_no_load.to('W').magnitude / p_load_rated.to('W').magnitude)
    
    return {
        "efficiency": eta.magnitude,
        "p_output": p_output,
        "p_total_loss": total_losses,
        "load_fraction_max_eta": load_fraction_max_eta
    }

def calculate_voltage_regulation(
    r_pu: float, 
    x_pu: float, 
    power_factor: float = 1.0, 
    is_inductive: bool = True
) -> float:
    """Gerilim regülasyonunu (pu) hesaplar."""
    if not 0 <= power_factor <= 1:
        raise ValueError("Güç faktörü 0 ile 1 arasında olmalıdır.")
    sin_phi = math.sqrt(1 - power_factor**2)
    if is_inductive:
        regulation_pu = r_pu * power_factor + x_pu * sin_phi
    else:
        regulation_pu = r_pu * power_factor - x_pu * sin_phi
    return regulation_pu

def calculate_no_load_equivalent(
    p_no_load_total: Any, 
    v_excitation_phase: Any, 
    phase_count: int = 3, 
    i_no_load_phase: Optional[Any] = None
) -> Dict[str, Any]:
    """Boşta çalışma eşdeğer devresini hesaplar."""
    p_no_load_phase = p_no_load_total / phase_count
    r_core_phase = (v_excitation_phase ** 2) / p_no_load_phase
    
    res: Dict[str, Any] = {
        "p_no_load_phase": p_no_load_phase,
        "r_core_phase": r_core_phase
    }
    
    if i_no_load_phase is not None:
        i_active = p_no_load_phase / v_excitation_phase
        if i_no_load_phase > i_active:
            i_reactive = (i_no_load_phase**2 - i_active**2)**0.5
            x_m_phase = v_excitation_phase / i_reactive
            res["x_m_phase"] = x_m_phase
            res["i_active"] = i_active
            res["i_reactive"] = i_reactive
            
    return res

def calculate_leakage_impedance(
    freq_hz: float,
    turns: int,
    v_phase: float,
    s_rated_va_per_phase: float,
    h_winding_mm: float,
    mean_diameter_gap_mm: float,
    gap_width_mm: float,
    lv_thickness_mm: float,
    hv_thickness_mm: float
) -> float:
    """
    Rogowski katsayısı (K_r) dikkate alınarak IEC standartlarına 
    göre gerçek kısa devre empedansını (%uk) hesaplar.
    """
    positive_values = (
        freq_hz,
        turns,
        v_phase,
        s_rated_va_per_phase,
        h_winding_mm,
        mean_diameter_gap_mm,
        gap_width_mm,
        lv_thickness_mm,
        hv_thickness_mm,
    )
    if any(value <= 0 for value in positive_values):
        raise ValueError("Kaçak empedans girdileri pozitif olmalıdır.")
    mu_0 = 4 * math.pi * 1e-7
    
    # Metre cinsine çevir
    H_w = h_winding_mm / 1000.0
    D_m = mean_diameter_gap_mm / 1000.0
    a = gap_width_mm / 1000.0
    b1 = lv_thickness_mm / 1000.0
    b2 = hv_thickness_mm / 1000.0
    
    # Eşdeğer kaçak akı kanalı genişliği
    sigma = a + (b1 + b2) / 3.0
    
    # Rogowski Katsayısı (K_R)
    # K_R = 1 - (1 - e^(-pi * H_w / (b1+b2+a))) / ... (Basitleştirilmiş hali)
    k_r = 1.0 - (sigma / (math.pi * H_w))
    k_r = max(0.6, min(1.0, k_r))  # Pratik sınırlar
    
    # Reaktans (X_k) - Ohm/Faz
    x_k = (2 * math.pi * freq_hz * mu_0 * (turns**2) * math.pi * D_m * sigma * k_r) / H_w
    
    # Z_base = V^2 / S_phase
    z_base = (v_phase**2) / s_rated_va_per_phase
    
    uk_pu = x_k / z_base
    uk_percent = uk_pu * 100.0
    
    return uk_percent
