import math
from typing import Dict, Any, Optional
from ..units import Q_
from ..exceptions import MissingDataError

def calculate_turn_voltage(
    method: str, 
    f: Any, 
    s_rated: Optional[Any] = None, 
    empirical_coefficient: Optional[float] = None, 
    b_max: Optional[Any] = None, 
    a_core_net: Optional[Any] = None, 
    k_emf: float = 4.44, 
    direct_v_turn: Optional[Any] = None
) -> Any:
    """Tur başına gerilimi hesaplar."""
    if method == "empirical":
        if s_rated is None or empirical_coefficient is None:
            raise MissingDataError("Ampirik yöntem için güç ve katsayı gereklidir.")
        return empirical_coefficient * math.sqrt(s_rated.to('kVA').magnitude) * Q_(1, 'V')
    elif method == "direct_calculation":
        if b_max is None or a_core_net is None:
            raise MissingDataError("Doğrudan hesap için akı yoğunluğu ve net kesit gereklidir.")
        return k_emf * f * b_max * a_core_net
    elif method == "user_defined":
        if direct_v_turn is None:
            raise MissingDataError("Kullanıcı tanımlı yöntem için değer girilmelidir.")
        return direct_v_turn
    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

def calculate_net_core_area(e_turn: Any, k_emf: float, f: Any, b_max: Any) -> Any:
    """Net çekirdek kesitini hesaplar."""
    return (e_turn / (k_emf * f * b_max)).to('mm**2')

def calculate_core_geometry(
    a_core_net: Any, 
    k_stack: float, 
    k_shape: float
) -> Dict[str, Any]:
    """Çekirdeğin fiziksel geometrisini hesaplar."""
    a_core_gross = a_core_net / k_stack
    d_eq = math.sqrt(4 * a_core_gross.to('mm**2').magnitude / math.pi) * Q_(1, 'mm')
    d_physical = math.sqrt(4 * a_core_gross.to('mm**2').magnitude / (math.pi * k_shape)) * Q_(1, 'mm')
    
    return {
        "a_core_gross": a_core_gross,
        "d_equivalent": d_eq,
        "d_physical": d_physical
    }

def verify_flux_density(e_turn_actual: Any, k_emf: float, f: Any, a_core_net_actual: Any) -> Any:
    """Gerçek tur başına gerilim ile akı yoğunluğunu yeniden doğrular."""
    b_actual = e_turn_actual / (k_emf * f * a_core_net_actual)
    return b_actual.to('T')

def calculate_window_area(
    turns_hv: int, 
    a_cond_hv: Any, 
    turns_lv: int, 
    a_cond_lv: Any, 
    topology_factor: float, 
    k_u_target: float
) -> Dict[str, Any]:
    """Pencere alanını hesaplar."""
    q_winding_hv = turns_hv * a_cond_hv
    q_winding_lv = turns_lv * a_cond_lv
    q_leg = q_winding_hv + q_winding_lv
    q_window = topology_factor * q_leg
    
    a_window_required = q_window / k_u_target
    return {
        "q_window": q_window.to('mm**2'),
        "a_window_required": a_window_required.to('mm**2')
    }

def calculate_core_steps(d_physical_mm: float, n_steps: int = 6) -> list:
    """
    Yuvarlak çekirdek (core) kesitini oluşturmak için silisli sacların
    kademe (step) genişliklerini ve o kademeye dizilecek paket kalınlıklarını hesaplar.
    """
    steps = []
    R = d_physical_mm / 2.0
    
    # Eşit açısal dağılım (basitleştirilmiş)
    for i in range(1, n_steps + 1):
        theta_prev = (i - 1) * (math.pi / 2) / n_steps
        theta_curr = i * (math.pi / 2) / n_steps
        
        width = 2 * R * math.cos(theta_curr)
        thickness = R * (math.sin(theta_curr) - math.sin(theta_prev))
        
        # Sac kalınlığı genelde 0.23, 0.27, 0.30mm olur.
        # Toplam sac adedi:
        sheet_thickness = 0.27
        num_sheets = math.floor(thickness / sheet_thickness)
        
        steps.append({
            "step_no": i,
            "width_mm": round(width, 1),
            "packet_thickness_mm": round(thickness, 1),
            "num_sheets": num_sheets * 2  # x2 (çünkü simetrik, üst/alt veya sağ/sol)
        })
        
    return steps
