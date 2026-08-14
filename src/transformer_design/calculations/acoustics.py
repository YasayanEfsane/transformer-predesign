import math
from typing import Dict, Any

def calculate_acoustic_noise(
    core_weight_kg: float,
    flux_density_t: float
) -> Dict[str, float]:
    """
    Çekirdek ağırlığı ve akı yoğunluğu üzerinden IEC 60076-10 / NEMA TR-1'e benzer 
    temel bir ses gücü (Lw) ve ses basıncı (Lp) tahmin modeli (dBA) uygular.
    
    Yaklaşım:
    Baz Gürültü ~ 40 dBA (küçük trafolar için) + 10 * log10(Ağırlık)
    Akı Etkisi ~ Her 0.1T artış yaklaşık 2-3 dBA artış getirir. (Referans: 1.5 T)
    """
    if core_weight_kg <= 0:
        return {"sound_power_db_a": 0.0, "sound_pressure_db_a": 0.0}
        
    # Baz ses gücü (Lw)
    base_lw = 40.0 + 12.0 * math.log10(core_weight_kg)
    
    # Akı yoğunluğu faktörü (1.5 T baz alınmıştır)
    flux_factor = (flux_density_t - 1.5) * 30.0
    
    lw = base_lw + flux_factor
    
    # Ses basıncı, yaklaşık olarak ses gücünden 12-14 dB daha düşüktür (Ölçüm mesafesi 0.3m varsayımı)
    lp = lw - 13.0
    
    # Minimum sınırlar
    lw = max(45.0, lw)
    lp = max(35.0, lp)
    
    return {
        "sound_power_db_a": round(lw, 1),
        "sound_pressure_db_a": round(lp, 1)
    }
