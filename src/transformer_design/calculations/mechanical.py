import math
from typing import Dict, Any

# Manyetik Geçirgenlik
MU_0 = 4 * math.pi * 1e-7

def get_yield_strength_mpa(material: str) -> float:
    """İletken malzemesine göre ortalama akma dayanımı (MPa) döndürür."""
    if material.lower() == "copper":
        return 200.0  # Work-hardened copper
    elif material.lower() == "aluminum":
        return 70.0
    return 150.0

def calculate_short_circuit_forces(
    s_rated_kva: float,
    v_line_v: float,
    z_pu: float,
    hv_turns: int,
    lv_turns: int,
    hv_conductor_area_mm2: float,
    lv_conductor_area_mm2: float,
    window_height_mm: float,
    mean_diameter_mm: float,
    hv_material: str = "copper",
    lv_material: str = "copper",
    k_asym: float = 1.8
) -> Dict[str, Any]:
    """
    Kısa devre anında sargılarda oluşan asimetrik tepe akımını ve
    bu akımın yarattığı radyal/eksenel kuvvetler ile sargı içi gerilmeleri (MPa) hesaplar.
    """
    # Nominal ve Tepe Kisa Devre Akimi (HV tarafi referansli)
    i_rated = (s_rated_kva * 1000) / (math.sqrt(3) * v_line_v)
    i_sc_sym = i_rated / z_pu
    i_sc_peak = i_sc_sym * math.sqrt(2) * k_asym
    
    # Amper-Sarim (Kisa Devre Aninda)
    ni_sc = hv_turns * i_sc_peak
    
    # Maksimum Asimetrik Radyal Kuvvet (F = (u0 * (NI)^2 * pi * Dm) / (2 * Hw))
    h_w = window_height_mm / 1000.0
    d_m = mean_diameter_mm / 1000.0
    f_radial_newton = (MU_0 * (ni_sc ** 2) * math.pi * d_m) / (2 * h_w)
    f_radial_kn = f_radial_newton / 1000.0
    
    # Eksenel kuvvet radyal kuvvetin genelde %20'si (Ampirik)
    f_axial_kn = f_radial_kn * 0.20
    
    # Hoop Stress (Halka Gerilmesi) - N/mm2 = MPa
    # sigma = F_radial / (2 * pi * N * A_cond)
    hv_stress_mpa = f_radial_newton / (2 * math.pi * hv_turns * hv_conductor_area_mm2) if hv_conductor_area_mm2 else 0.0
    lv_stress_mpa = f_radial_newton / (2 * math.pi * lv_turns * lv_conductor_area_mm2) if lv_conductor_area_mm2 else 0.0
    
    # Akma Dayanimi Kontrolleri
    hv_yield = get_yield_strength_mpa(hv_material)
    lv_yield = get_yield_strength_mpa(lv_material)
    
    hv_is_safe = hv_stress_mpa < (hv_yield * 0.9)  # %10 Guvenlik Payi
    lv_is_safe = lv_stress_mpa < (lv_yield * 0.9)
    
    return {
        "i_sc_peak_A": i_sc_peak,
        "f_radial_kN": f_radial_kn,
        "f_axial_kN": f_axial_kn,
        "hv_stress_mpa": hv_stress_mpa,
        "lv_stress_mpa": lv_stress_mpa,
        "hv_is_safe": hv_is_safe,
        "lv_is_safe": lv_is_safe,
        "is_mechanically_safe": hv_is_safe and lv_is_safe
    }
