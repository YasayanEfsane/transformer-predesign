from typing import Dict, Any

def get_basic_insulation_level(voltage_v: float) -> float:
    """
    Nominal gerilime göre standart Darbe Dayanım Gerilimini (BIL - kV) döner.
    IEC standartlarına basitleştirilmiş yaklaşımdır.
    """
    kv = voltage_v / 1000.0
    if kv <= 1.1:
        return 0.0 # Sadece şebeke frekansına göre yalıtım
    elif kv <= 7.2:
        return 60.0
    elif kv <= 12.0:
        return 75.0
    elif kv <= 17.5:
        return 95.0
    elif kv <= 24.0:
        return 125.0
    elif kv <= 36.0:
        return 170.0
    else:
        return 200.0 # 36kV üstü için jenerik

def calculate_clearances(hv_voltage_v: float, lv_voltage_v: float) -> Dict[str, float]:
    """
    Yüksek Gerilim (HV) ve Alçak Gerilim (LV) değerlerine göre
    yağ içinde bırakılması gereken minimum dielektrik güvenlik boşluklarını (mm) hesaplar.
    """
    hv_bil = get_basic_insulation_level(hv_voltage_v)
    
    # Çok kaba endüstriyel ampirik kurallar:
    # HV fazından Toprağa (Çekirdek/Tank) mesafe ~ BIL (kV) * 0.25 (mm) + 10mm
    phase_to_ground_mm = max(15.0, hv_bil * 0.25 + 10.0)
    
    # HV fazından HV fazına mesafe ~ BIL (kV) * 0.30 (mm) + 15mm
    phase_to_phase_mm = max(20.0, hv_bil * 0.30 + 15.0)
    
    # HV'den LV'ye mesafe (LV tarafı topraklanmış kabul edilirse genelde faz-toprak kadar veya azı)
    hv_to_lv_mm = max(15.0, hv_bil * 0.22 + 5.0)
    
    return {
        "hv_bil_kv": hv_bil,
        "phase_to_ground_mm": phase_to_ground_mm,
        "phase_to_phase_mm": phase_to_phase_mm,
        "hv_to_lv_mm": hv_to_lv_mm
    }
