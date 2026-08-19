"""Calculations for transformer taps and voltage regulation."""
from __future__ import annotations

import math
from typing import Any

def calculate_tap_turns(
    nominal_hv_turns: int,
    tap_percentages: list[float]
) -> dict[str, Any]:
    """Hesaplanan HV tur sayisina gore her kademenin gercek sarim sayisini ve sapmasini hesaplar."""
    if not tap_percentages:
        return {}
        
    results = {}
    for tap in tap_percentages:
        factor = 1.0 + (tap / 100.0)
        ideal_turns = nominal_hv_turns * factor
        actual_turns = round(ideal_turns)
        error_percent = 0.0
        if ideal_turns > 0:
            error_percent = ((actual_turns - ideal_turns) / ideal_turns) * 100.0
        
        results[f"{tap}%"] = {
            "ideal_turns": ideal_turns,
            "actual_turns": actual_turns,
            "error_percent": error_percent
        }
    return results

def calculate_voltage_regulation(
    u_k_percent: float,
    u_r_percent: float,
    power_factors: list[float] | None = None
) -> dict[str, dict[str, float]]:
    """Belirtilen guc faktorlerinde gerilim regülasyonunu hesaplar.
    
    Formula:
    u_x = sqrt(u_k^2 - u_r^2)
    Reg = u_r * cos_phi +/- u_x * sin_phi + ((u_x * cos_phi -/+ u_r * sin_phi)^2) / 200
    """
    if power_factors is None:
        power_factors = [1.0, 0.9, 0.8]
        
    if u_k_percent < u_r_percent:
        return {}
        
    u_x_percent = math.sqrt(u_k_percent**2 - u_r_percent**2)
    
    results = {}
    for pf in power_factors:
        cos_phi = pf
        sin_phi = math.sqrt(1.0 - cos_phi**2)
        
        # Inductive load (+sin_phi)
        reg_ind = u_r_percent * cos_phi + u_x_percent * sin_phi + ((u_x_percent * cos_phi - u_r_percent * sin_phi)**2) / 200.0
        
        # Capacitive load (-sin_phi)
        reg_cap = u_r_percent * cos_phi - u_x_percent * sin_phi + ((u_x_percent * cos_phi + u_r_percent * sin_phi)**2) / 200.0
        
        results[str(pf)] = {
            "inductive_percent": reg_ind,
            "capacitive_percent": reg_cap
        }
        
    return results
