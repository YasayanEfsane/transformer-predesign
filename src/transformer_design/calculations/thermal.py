from typing import Dict, Any
from ..units import Q_
import math

def calculate_required_cooling_area(p_total_w: Any, target_oil_rise_k: Any, heat_dissipation_coefficient_w_m2k: Any) -> Any:
    """
    Toplam ısı kaybını (Boşta + Yükte) hedeflenen yağ sıcaklık artışında atabilmek için 
    gereken toplam soğutma yüzey alanını hesaplar.
    
    A_gerekli = P_toplam / (k * ΔT)
    """
    p_w = p_total_w.to('W').magnitude
    dt_k = target_oil_rise_k.to('kelvin').magnitude
    k_coef = heat_dissipation_coefficient_w_m2k.to('W/(m**2 * kelvin)').magnitude
    
    area_m2 = p_w / (k_coef * dt_k)
    return Q_(area_m2, 'm**2')

def estimate_tank_surface_area(core_width_mm: Any, core_height_mm: Any, core_depth_mm: Any, clearance_mm: float = 100.0) -> Any:
    """
    Aktif kısmın (çekirdek + sargılar) etrafını saran çıplak tankın dış yüzey alanını yaklaşık olarak hesaplar.
    Sadece yan duvarlar ve kapak ısı atılımında etkilidir (Alt taban ihmal edilir).
    """
    w = (core_width_mm.to('mm').magnitude + 2 * clearance_mm) / 1000.0
    d = (core_depth_mm.to('mm').magnitude + 2 * clearance_mm) / 1000.0
    h = (core_height_mm.to('mm').magnitude + 2 * clearance_mm) / 1000.0
    
    # 2 x (Genişlik x Yükseklik) + 2 x (Derinlik x Yükseklik) + Kapak (Genişlik x Derinlik)
    area_m2 = 2 * (w * h) + 2 * (d * h) + (w * d)
    return Q_(area_m2, 'm**2')

def calculate_tank_and_radiator_needs(required_area_m2: Any, tank_surface_area_m2: Any) -> Dict[str, Any]:
    """
    Tankın kendi soğutma kapasitesinden artan ısıyı atmak için gereken radyatör 
    veya dalgalı sac (corrugated fin) alanını belirler.
    """
    req_a = required_area_m2.to('m**2').magnitude
    tank_a = tank_surface_area_m2.to('m**2').magnitude
    
    rad_needed = max(0.0, req_a - tank_a)
    
    return {
        "required_cooling_area": required_area_m2,
        "tank_surface_area": tank_surface_area_m2,
        "radiator_area_needed": Q_(rad_needed, 'm**2'),
        "is_radiator_needed": rad_needed > 0
    }

def calculate_hot_spot_and_fins(
    radiator_area_needed_m2: float, 
    top_oil_temp_rise: float, 
    j_avg: float
) -> Dict[str, Any]:
    """
    Radyatör (dalgalı duvar) dilim sayısını ve IEC'ye göre Hot-Spot (en sıcak nokta) 
    sıcaklık artışını hesaplar.
    
    Dalgalı sac parametreleri (örnek): 
    1 adet dilimin yüksekliği 800mm, derinliği 200mm olsun -> 2 * 0.8 * 0.2 = 0.32 m2 yüzey.
    """
    fin_area_m2 = 0.32 
    num_fins = math.ceil(radiator_area_needed_m2 / fin_area_m2) if radiator_area_needed_m2 > 0 else 0
    
    # Hot-spot tahmini (Basitleştirilmiş IEC yaklaşımı)
    # Winding-to-Oil gradient (g) akım yoğunluğu ile orantılıdır (yaklaşık 15K - 22K).
    gradient_g = 15.0 + (j_avg - 2.0) * 3.0  # j=3 A/mm2 için g=18K
    hot_spot_factor_H = 1.3
    
    hot_spot_rise = top_oil_temp_rise + (hot_spot_factor_H * gradient_g)
    
    return {
        "num_radiator_fins": num_fins,
        "fin_area_m2": fin_area_m2,
        "winding_gradient_k": gradient_g,
        "hot_spot_rise_k": hot_spot_rise
    }
