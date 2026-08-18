import math
from typing import Dict, Any

# Manyetik Geçirgenlik
MU_0 = 4 * math.pi * 1e-7

def calculate_short_circuit_forces(
    s_rated_kva: float,
    v_line_v: float,
    z_pu: float,
    hv_turns: int,
    window_height_mm: float,
    mean_diameter_mm: float,
    k_asym: float = 1.8
) -> Dict[str, Any]:
    """
    Kısa devre anında sargılarda oluşan asimetrik tepe akımını ve
    bu akımın yarattığı yaklaşık radyal (patlatma/ezme) kuvvetini hesaplar.
    """
    # Nominal akım
    i_rated = (s_rated_kva * 1000) / (math.sqrt(3) * v_line_v)
    
    # Simetrik ve Asimetrik Tepe Kısa Devre Akımı
    i_sc_sym = i_rated / z_pu
    i_sc_peak = i_sc_sym * math.sqrt(2) * k_asym
    
    # Amper-Sarım (Kısa Devre Anında)
    ni_sc = hv_turns * i_sc_peak
    
    # Radyal Kuvvet (F = (µ0 * (NI)^2 * pi * Dm) / (2 * Hw))
    h_w = window_height_mm / 1000.0
    d_m = mean_diameter_mm / 1000.0
    f_radial_newton = (MU_0 * (ni_sc ** 2) * math.pi * d_m) / (2 * h_w)
    f_radial_kn = f_radial_newton / 1000.0
    
    # Eksenel kuvvet radyal kuvvetin genelde %15-25'i civarındadır (Ampirik yaklaşım)
    f_axial_kn = f_radial_kn * 0.20
    
    return {
        "i_sc_peak_A": i_sc_peak,
        "f_radial_kN": f_radial_kn,
        "f_axial_kN": f_axial_kn
    }
