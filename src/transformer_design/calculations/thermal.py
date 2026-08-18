"""Steady-state and dynamic thermal screening calculations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from ..units import Q_


def _positive_magnitude(quantity: Any, unit: str, name: str) -> float:
    value = quantity.to(unit).magnitude
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} sıfırdan büyük ve sonlu olmalıdır.")
    return value


def calculate_required_cooling_area(
    p_total_w: Any,
    target_oil_rise_k: Any,
    heat_dissipation_coefficient_w_m2k: Any,
) -> Any:
    """Return the approximate surface needed to dissipate total losses."""
    p_w = _positive_magnitude(p_total_w, "W", "Toplam kayıp")
    dt_k = _positive_magnitude(target_oil_rise_k, "kelvin", "Yağ sıcaklık artışı")
    k_coef = _positive_magnitude(
        heat_dissipation_coefficient_w_m2k,
        "W/(m**2 * kelvin)",
        "Isı yayılım katsayısı",
    )
    return Q_(p_w / (k_coef * dt_k), "m**2")


def estimate_tank_surface_area(
    core_width_mm: Any,
    core_height_mm: Any,
    core_depth_mm: Any,
    clearance_mm: float = 100.0,
) -> Any:
    """Estimate four tank walls and the lid; the bottom is conservatively ignored."""
    if clearance_mm < 0:
        raise ValueError("Tank açıklığı negatif olamaz.")
    dimensions = [
        _positive_magnitude(value, "mm", name)
        for value, name in (
            (core_width_mm, "Aktif kısım genişliği"),
            (core_height_mm, "Aktif kısım yüksekliği"),
            (core_depth_mm, "Aktif kısım derinliği"),
        )
    ]
    w, h, d = ((value + 2 * clearance_mm) / 1000.0 for value in dimensions)
    return Q_(2 * w * h + 2 * d * h + w * d, "m**2")


def calculate_tank_and_radiator_needs(
    required_area_m2: Any, tank_surface_area_m2: Any
) -> dict[str, Any]:
    """Return the additional effective cooling surface required beyond the bare tank."""
    req_a = _positive_magnitude(required_area_m2, "m**2", "Gerekli soğutma alanı")
    tank_a = _positive_magnitude(tank_surface_area_m2, "m**2", "Tank yüzey alanı")
    radiator_area = max(0.0, req_a - tank_a)
    return {
        "required_cooling_area": required_area_m2,
        "tank_surface_area": tank_surface_area_m2,
        "radiator_area_needed": Q_(radiator_area, "m**2"),
        "is_radiator_needed": radiator_area > 0,
    }


def calculate_hot_spot_and_fins(
    radiator_area_needed_m2: float,
    top_oil_temp_rise: float,
    j_avg: float,
) -> dict[str, Any]:
    """Estimate corrugated-fin count and rated hot-spot rise.

    This is a screening correlation, not an IEC temperature-rise type test.
    """
    if radiator_area_needed_m2 < 0 or top_oil_temp_rise <= 0 or j_avg <= 0:
        raise ValueError("Termal tasarım girdileri fiziksel olarak pozitif olmalıdır.")
    fin_area_m2 = 0.32
    num_fins = math.ceil(radiator_area_needed_m2 / fin_area_m2)
    winding_gradient_k = max(8.0, 15.0 + (j_avg - 2.0) * 3.0)
    hot_spot_factor = 1.3
    hot_spot_rise_k = top_oil_temp_rise + hot_spot_factor * winding_gradient_k
    return {
        "num_radiator_fins": num_fins,
        "fin_area_m2": fin_area_m2,
        "winding_gradient_k": winding_gradient_k,
        "hot_spot_factor": hot_spot_factor,
        "hot_spot_rise_k": hot_spot_rise_k,
    }


def simulate_dynamic_thermal(
    load_factors: Sequence[float],
    ambient_temperatures_c: Sequence[float],
    *,
    time_step_minutes: float = 60.0,
    rated_top_oil_rise_k: float = 60.0,
    rated_hot_spot_gradient_k: float = 23.0,
    load_to_no_load_loss_ratio: float = 6.0,
    oil_time_constant_minutes: float = 180.0,
    winding_time_constant_minutes: float = 10.0,
    oil_exponent: float = 0.8,
    winding_exponent: float = 1.6,
    initial_top_oil_rise_k: float = 0.0,
    initial_hot_spot_gradient_k: float = 0.0,
) -> list[dict[str, float]]:
    """Simulate an IEC 60076-7-inspired first-order thermal response.

    Each profile row represents one interval. The returned temperature belongs to
    the end of that interval. The equations are intended for comparative
    pre-design work and do not assert standard compliance.
    """
    if len(load_factors) != len(ambient_temperatures_c) or not load_factors:
        raise ValueError("Yük ve ortam profilleri aynı, sıfırdan büyük uzunlukta olmalıdır.")

    positive_values = {
        "Zaman adımı": time_step_minutes,
        "Anma üst yağ artışı": rated_top_oil_rise_k,
        "Anma hot-spot gradyanı": rated_hot_spot_gradient_k,
        "Kayıp oranı": load_to_no_load_loss_ratio,
        "Yağ zaman sabiti": oil_time_constant_minutes,
        "Sargı zaman sabiti": winding_time_constant_minutes,
        "Yağ üssü": oil_exponent,
        "Sargı üssü": winding_exponent,
    }
    if any(not math.isfinite(value) or value <= 0 for value in positive_values.values()):
        raise ValueError("Dinamik termal model katsayıları pozitif ve sonlu olmalıdır.")
    if initial_top_oil_rise_k < 0 or initial_hot_spot_gradient_k < 0:
        raise ValueError("Başlangıç sıcaklık artışları negatif olamaz.")

    oil_alpha = 1.0 - math.exp(-time_step_minutes / oil_time_constant_minutes)
    winding_alpha = 1.0 - math.exp(-time_step_minutes / winding_time_constant_minutes)
    top_oil_rise = initial_top_oil_rise_k
    hot_spot_gradient = initial_hot_spot_gradient_k
    results: list[dict[str, float]] = []

    for index, (raw_load, raw_ambient) in enumerate(
        zip(load_factors, ambient_temperatures_c, strict=True)
    ):
        load = float(raw_load)
        ambient = float(raw_ambient)
        if not math.isfinite(load) or load < 0 or load > 3:
            raise ValueError("Yük katsayıları 0 ile 3 pu arasında olmalıdır.")
        if not math.isfinite(ambient) or ambient < -50 or ambient > 80:
            raise ValueError("Ortam sıcaklıkları -50 ile 80 °C arasında olmalıdır.")

        ultimate_oil_rise = rated_top_oil_rise_k * (
            (load**2 * load_to_no_load_loss_ratio + 1.0)
            / (load_to_no_load_loss_ratio + 1.0)
        ) ** oil_exponent
        ultimate_gradient = rated_hot_spot_gradient_k * load ** (2.0 * winding_exponent)
        top_oil_rise += (ultimate_oil_rise - top_oil_rise) * oil_alpha
        hot_spot_gradient += (ultimate_gradient - hot_spot_gradient) * winding_alpha

        top_oil_temp = ambient + top_oil_rise
        hot_spot_temp = top_oil_temp + hot_spot_gradient
        aging_exponent = 15000.0 / 383.0 - 15000.0 / (hot_spot_temp + 273.0)
        aging_acceleration = math.exp(min(aging_exponent, 700.0))
        results.append(
            {
                "time_hours": (index + 1) * time_step_minutes / 60.0,
                "load_factor": load,
                "ambient_temperature_c": ambient,
                "top_oil_rise_k": top_oil_rise,
                "top_oil_temperature_c": top_oil_temp,
                "hot_spot_gradient_k": hot_spot_gradient,
                "hot_spot_temperature_c": hot_spot_temp,
                "aging_acceleration_factor": aging_acceleration,
            }
        )

    return results
