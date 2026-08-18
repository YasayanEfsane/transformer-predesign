"""Deterministic mass and material-cost screening calculations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from ..models.enums import ConductorMaterial


DEFAULT_MATERIAL_PRICES_USD_KG: dict[str, float] = {
    "COPPER": 10.50,
    "ALUMINUM": 3.20,
    "STEEL": 2.80,
}

OIL_TYPES: dict[str, dict[str, float]] = {
    "Mineral Yağ (0.89 kg/L)": {"density_kg_l": 0.89, "price_usd_kg": 1.50},
    "Doğal Ester (Bitkisel) (0.92 kg/L)": {
        "density_kg_l": 0.92,
        "price_usd_kg": 3.50,
    },
    "Sentetik Ester (0.97 kg/L)": {"density_kg_l": 0.97, "price_usd_kg": 5.00},
    "Silikon Yağ (0.96 kg/L)": {"density_kg_l": 0.96, "price_usd_kg": 6.00},
}

DENSITIES_KG_M3 = {
    "COPPER": 8900.0,
    "ALUMINUM": 2700.0,
    "STEEL": 7650.0,
}


def _material_key(material: ConductorMaterial) -> str:
    return "COPPER" if material == ConductorMaterial.COPPER else "ALUMINUM"


def _validated_prices(custom_prices: Mapping[str, float] | None) -> dict[str, float]:
    prices = {**DEFAULT_MATERIAL_PRICES_USD_KG, **(custom_prices or {})}
    missing = set(DEFAULT_MATERIAL_PRICES_USD_KG) - prices.keys()
    if missing:
        raise ValueError(f"Eksik malzeme fiyatları: {', '.join(sorted(missing))}")
    for material in DEFAULT_MATERIAL_PRICES_USD_KG:
        value = float(prices[material])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{material} fiyatı pozitif ve sonlu olmalıdır.")
        prices[material] = value
    return prices


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
    custom_prices: Mapping[str, float] | None = None,
    lv_radial_build_mm: float | None = None,
    hv_radial_build_mm: float | None = None,
) -> dict[str, Any]:
    """Estimate active-part, tank and oil mass plus direct material cost.

    The routine deliberately uses explicit user-supplied or deterministic default
    prices. Network market data is not fetched inside an engineering calculation.
    """
    if hv_turns <= 0 or lv_turns <= 0:
        raise ValueError("Sargı tur sayıları pozitif olmalıdır.")
    if window_height_mm <= 0 or leg_spacing_mm <= 0 or tank_volume_m3 < 0:
        raise ValueError("Geometri girdileri fiziksel olarak geçerli olmalıdır.")
    if oil_type_str not in OIL_TYPES:
        raise ValueError(f"Desteklenmeyen yağ türü: {oil_type_str}")

    prices = _validated_prices(custom_prices)
    hv_area = hv_area_mm2.to("mm**2").magnitude
    lv_area = lv_area_mm2.to("mm**2").magnitude
    core_area_m2 = core_gross_area_mm2.to("m**2").magnitude
    core_diameter_m = core_diameter_mm.to("m").magnitude
    tank_area = tank_area_m2.to("m**2").magnitude
    if min(hv_area, lv_area, core_area_m2, core_diameter_m, tank_area) <= 0:
        raise ValueError("Alan ve çap değerleri pozitif olmalıdır.")

    leg_length_m = window_height_mm / 1000.0 + core_diameter_m
    yoke_length_m = 2 * leg_spacing_mm / 1000.0 + core_diameter_m
    core_length_m = 3 * leg_length_m + 2 * yoke_length_m
    core_volume_m3 = core_area_m2 * core_length_m
    core_weight_kg = core_volume_m3 * DENSITIES_KG_M3["STEEL"]

    lv_radial_m = (
        lv_radial_build_mm / 1000.0
        if lv_radial_build_mm is not None
        else (lv_area / 50.0) / 1000.0
    )
    hv_radial_m = (
        hv_radial_build_mm / 1000.0
        if hv_radial_build_mm is not None
        else (hv_area / 2.0) / 1000.0
    )
    if lv_radial_m <= 0 or hv_radial_m <= 0:
        raise ValueError("Sargı radyal kalınlıkları pozitif olmalıdır.")

    lv_inner_diameter_m = core_diameter_m + 0.010
    lv_mean_turn_length_m = math.pi * (lv_inner_diameter_m + lv_radial_m)
    lv_total_length_m = lv_mean_turn_length_m * lv_turns * 3
    lv_volume_m3 = lv_total_length_m * lv_area * 1e-6

    hv_inner_diameter_m = lv_inner_diameter_m + 2 * lv_radial_m + 0.020
    hv_mean_turn_length_m = math.pi * (hv_inner_diameter_m + hv_radial_m)
    hv_total_length_m = hv_mean_turn_length_m * hv_turns * 3
    hv_volume_m3 = hv_total_length_m * hv_area * 1e-6

    lv_key = _material_key(lv_mat)
    hv_key = _material_key(hv_mat)
    lv_weight_kg = lv_volume_m3 * DENSITIES_KG_M3[lv_key]
    hv_weight_kg = hv_volume_m3 * DENSITIES_KG_M3[hv_key]

    tank_sheet_thickness_m = 0.005
    tank_metal_volume_m3 = tank_area * tank_sheet_thickness_m
    tank_weight_kg = tank_metal_volume_m3 * DENSITIES_KG_M3["STEEL"]

    active_volume_m3 = core_volume_m3 + lv_volume_m3 + hv_volume_m3
    if tank_volume_m3 > 0:
        # Ten per cent headspace is retained for thermal expansion.
        usable_oil_volume_m3 = max(0.05, (tank_volume_m3 - active_volume_m3) * 0.90)
        oil_volume_liters = usable_oil_volume_m3 * 1000.0
    else:
        oil_volume_liters = 500.0 + 0.12 * core_weight_kg + 10.0 * tank_area

    oil = OIL_TYPES[oil_type_str]
    oil_weight_kg = oil_volume_liters * oil["density_kg_l"]

    costs = {
        "core": core_weight_kg * prices["STEEL"] * 1.05,
        "lv_winding": lv_weight_kg * prices[lv_key] * 1.03,
        "hv_winding": hv_weight_kg * prices[hv_key] * 1.03,
        "tank": tank_weight_kg * prices["STEEL"] * 1.05,
        "oil": oil_weight_kg * oil["price_usd_kg"] * 1.05,
    }
    active_part_weight_kg = core_weight_kg + lv_weight_kg + hv_weight_kg
    weights = {
        "core": core_weight_kg,
        "lv_winding": lv_weight_kg,
        "hv_winding": hv_weight_kg,
        "active_part_untanked": active_part_weight_kg,
        "tank": tank_weight_kg,
        "oil": oil_weight_kg,
        "total": active_part_weight_kg + tank_weight_kg + oil_weight_kg,
    }
    return {
        "weights_kg": weights,
        "oil_stats": {"volume_L": oil_volume_liters, "type": oil_type_str},
        "costs_usd": {**costs, "total": sum(costs.values())},
        "geometry_assumptions": {
            "core_length_m": core_length_m,
            "lv_mean_turn_length_m": lv_mean_turn_length_m,
            "hv_mean_turn_length_m": hv_mean_turn_length_m,
            "tank_sheet_thickness_mm": tank_sheet_thickness_m * 1000.0,
        },
        "prices_usd_kg": {**prices, "OIL": oil["price_usd_kg"]},
    }
