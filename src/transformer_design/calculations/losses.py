"""Calculations for physical losses of the transformer."""
from __future__ import annotations


from ..models.enums import ConductorMaterial

RHO_CU_75 = 0.0216
RHO_AL_75 = 0.0354

def calculate_dc_resistance(
    turns: float,
    mean_turn_length_m: float,
    area_mm2: float,
    material: ConductorMaterial
) -> float:
    """75C referans sicaklikta sarginin faz basina DC direncini hesaplar."""
    if area_mm2 <= 0:
        raise ValueError("Iletken kesit alani pozitif olmalidir.")
    rho = RHO_CU_75 if material == ConductorMaterial.COPPER else RHO_AL_75
    length_m = turns * mean_turn_length_m
    return (rho * length_m) / area_mm2

def calculate_i2r_losses(
    i_phase: float,
    r_phase: float,
    phases: int = 3
) -> float:
    """Joule (I^2R) kayiplarini hesaplar."""
    return phases * (i_phase ** 2) * r_phase

def calculate_load_losses(
    hv_i2r: float,
    lv_i2r: float,
    additional_factor: float = 1.15
) -> dict[str, float]:
    """Sargilarin toplam hesaplanan yuk kayiplarini dondurur."""
    total_i2r = hv_i2r + lv_i2r
    stray_losses = total_i2r * (additional_factor - 1.0)
    total_load_loss = total_i2r * additional_factor
    return {
        "hv_i2r_W": hv_i2r,
        "lv_i2r_W": lv_i2r,
        "total_i2r_W": total_i2r,
        "stray_losses_W": stray_losses,
        "calculated_load_loss_W": total_load_loss
    }

def estimate_core_losses(
    core_weight_kg: float,
    flux_density_t: float,
    frequency_hz: float,
    steel_grade: str | None,
    additional_factor: float = 1.05
) -> float:
    """Cekirdek bos kayiplarini ampirik sac egrilerinden hesaplar."""
    base_w_kg = 0.90
    if steel_grade:
        grade = steel_grade.upper()
        if "M4" in grade:
            base_w_kg = 0.89
        elif "M5" in grade:
            base_w_kg = 0.97
        elif "ZDKH" in grade or "H-B" in grade:
            base_w_kg = 0.75
            
    scaled_w_kg = base_w_kg * (frequency_hz / 50.0) * ((flux_density_t / 1.5) ** 2)
    return core_weight_kg * scaled_w_kg * additional_factor
