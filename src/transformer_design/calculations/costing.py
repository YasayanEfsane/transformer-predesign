import math
import time
import yfinance as yf
from typing import Dict, Any
from ..units import Q_
from ..models.enums import ConductorMaterial

# Cache sistemi
_PRICE_CACHE = {}
_LAST_FETCH = 0

def get_live_lme_prices() -> Dict[str, float]:
    global _LAST_FETCH, _PRICE_CACHE
    now = time.time()
    
    # Her 1 saatte bir günceller, arayüzü kitlememek için
    if now - _LAST_FETCH < 3600 and _PRICE_CACHE:
        return _PRICE_CACHE
        
    try:
        cu_lb = yf.Ticker('HG=F').history(period='1d')['Close'].iloc[-1]
        al_t = yf.Ticker('ALI=F').history(period='1d')['Close'].iloc[-1]
        
        cu_kg = float(cu_lb) / 0.45359237
        al_kg = float(al_t) / 1000.0
        
        _PRICE_CACHE = {
            "COPPER": round(cu_kg, 2),
            "ALUMINUM": round(al_kg, 2),
            "STEEL": 3.00,  # Çelik sabit kabul
            "OIL": 1.50     # Yağ sabit kabul
        }
        _LAST_FETCH = now
    except Exception:
        # İnternet yoksa eski varsayılan fiyatlar
        _PRICE_CACHE = {
            "COPPER": 14.38,
            "ALUMINUM": 3.31,
            "STEEL": 3.00,
            "OIL": 1.50
        }
    return _PRICE_CACHE

# Canlı olmayan sabitler (Özkütle ve Tahmini birim fiyat)
OIL_TYPES = {
    "Mineral Yağ (0.89 kg/L)": {"density_kg_l": 0.89, "price_usd_kg": 1.50},
    "Doğal Ester (Bitkisel) (0.92 kg/L)": {"density_kg_l": 0.92, "price_usd_kg": 3.50},
    "Sentetik Ester (0.97 kg/L)": {"density_kg_l": 0.97, "price_usd_kg": 5.00},
    "Silikon Yağ (0.96 kg/L)": {"density_kg_l": 0.96, "price_usd_kg": 6.00}
}

# Yoğunluklar (kg/m^3)
DENSITIES = {
    "COPPER": 8900.0,
    "ALUMINUM": 2700.0,
    "STEEL": 7650.0
}

def calculate_weights_and_costs(
    hv_mat: ConductorMaterial,
    lv_mat: ConductorMaterial,
    hv_turns: int,
    lv_turns: int,
    hv_area_mm2: Any,
    lv_area_mm2: Any,
    core_gross_area_mm2: Any,
    core_diameter_mm: Any,
    tank_area_m2: Any,
    tank_volume_m3: float = 0.0,
    oil_type_str: str = "Mineral Yağ (0.89 kg/L)",
    window_height_mm: float = 380.0,
    leg_spacing_mm: float = 240.0,
    custom_prices: Dict[str, float] = None
) -> Dict[str, Any]:
    
    prices = custom_prices if custom_prices else get_live_lme_prices()
    
    # Çekirdek Ağırlığı
    a_core = core_gross_area_mm2.to('m**2').magnitude
    d_core = core_diameter_mm.to('m').magnitude
    
    # 3 Bacak + 2 Boyunduruk
    leg_length = (window_height_mm / 1000.0) + d_core
    yoke_length = (leg_spacing_mm * 2 / 1000.0) + d_core
    
    total_core_length = 3 * leg_length + 2 * yoke_length
    core_vol = a_core * total_core_length
    core_weight = core_vol * DENSITIES["STEEL"]
    core_cost = core_weight * prices["STEEL"] * 1.05  # %5 Fire payı
    
    # Sargı Çapları ve Uzunlukları
    # LV İç çap = Çekirdek çapı + yalıtım (10mm)
    lv_inner_d = d_core + 0.010
    lv_t = (lv_area_mm2.magnitude / 50.0) / 1000.0  # Yaklaşık kalınlık
    lv_mean_d = lv_inner_d + lv_t
    lv_mlt = math.pi * lv_mean_d  # Ortalama tur uzunluğu (m)
    
    lv_total_length = lv_mlt * lv_turns * 3  # 3 faz
    lv_vol = lv_total_length * (lv_area_mm2.to('m**2').magnitude)
    lv_dens = DENSITIES["COPPER"] if lv_mat == ConductorMaterial.COPPER else DENSITIES["ALUMINUM"]
    lv_price = prices["COPPER"] if lv_mat == ConductorMaterial.COPPER else prices["ALUMINUM"]
    lv_weight = lv_vol * lv_dens
    lv_cost = lv_weight * lv_price * 1.03  # %3 İletken firesi
    
    # HV İç çap = LV dış çap + yalıtım (20mm)
    hv_inner_d = lv_inner_d + 2 * lv_t + 0.020
    hv_t = (hv_area_mm2.magnitude / 2.0) / 1000.0 # Yaklaşık kalınlık
    hv_mean_d = hv_inner_d + hv_t
    hv_mlt = math.pi * hv_mean_d
    
    hv_total_length = hv_mlt * hv_turns * 3
    hv_vol = hv_total_length * (hv_area_mm2.to('m**2').magnitude)
    hv_dens = DENSITIES["COPPER"] if hv_mat == ConductorMaterial.COPPER else DENSITIES["ALUMINUM"]
    hv_price = prices["COPPER"] if hv_mat == ConductorMaterial.COPPER else prices["ALUMINUM"]
    hv_weight = hv_vol * hv_dens
    hv_cost = hv_weight * hv_price * 1.03  # %3 İletken firesi
    
    # Tank Ağırlığı (Yaklaşık 5mm çelik sac)
    tank_a = tank_area_m2.to('m**2').magnitude
    tank_vol_m3_metal = tank_a * 0.005
    tank_weight = tank_vol_m3_metal * DENSITIES["STEEL"]
    tank_cost = tank_weight * prices["STEEL"] * 1.05  # %5 Sac firesi
    
    # İzolasyon Yağı
    # Gerçek yağ hacmi = Tank İç Hacmi - Aktif Kısım Hacmi
    total_active_vol_m3 = core_vol + lv_vol + hv_vol
    if tank_volume_m3 > 0:
        oil_volume_liters = max(100.0, (tank_volume_m3 - total_active_vol_m3) * 1000.0)
    else:
        # Eğer tank volume gönderilmediyse fallback
        oil_volume_liters = 500.0 + (core_weight * 0.12) + (tank_a * 10.0)
        
    oil_dens = OIL_TYPES[oil_type_str]["density_kg_l"]
    oil_price = OIL_TYPES[oil_type_str]["price_usd_kg"]
    
    oil_weight = oil_volume_liters * oil_dens
    oil_cost = oil_weight * oil_price * 1.05  # %5 Yağ firesi
    
    # Ağırlık Kategorizasyonu
    active_part_weight = core_weight + lv_weight + hv_weight
    untanked_weight = active_part_weight
    total_weight = active_part_weight + tank_weight + oil_weight
    total_cost = core_cost + lv_cost + hv_cost + tank_cost + oil_cost
    
    return {
        "weights_kg": {
            "core": core_weight,
            "lv_winding": lv_weight,
            "hv_winding": hv_weight,
            "active_part_untanked": active_part_weight,
            "tank": tank_weight,
            "oil": oil_weight,
            "total": total_weight
        },
        "oil_stats": {
            "volume_L": oil_volume_liters,
            "type": oil_type_str
        },
        "costs_usd": {
            "core": core_cost,
            "lv_winding": lv_cost,
            "hv_winding": hv_cost,
            "tank": tank_cost,
            "oil": oil_cost,
            "total": total_cost
        }
    }
