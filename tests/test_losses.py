"""Unit tests for physical loss calculations."""
from __future__ import annotations

import math
from transformer_design.calculations.losses import (
    calculate_dc_resistance,
    calculate_i2r_losses,
    calculate_load_losses,
    estimate_core_losses
)
from transformer_design.models.enums import ConductorMaterial

def test_calculate_dc_resistance():
    # Copper 75C rho = 0.0216
    turns = 100
    mtl = 1.0
    area = 10.0
    # R = (0.0216 * 100 * 1.0) / 10 = 0.216
    res = calculate_dc_resistance(turns, mtl, area, ConductorMaterial.COPPER)
    assert math.isclose(res, 0.216, rel_tol=1e-4)
    
    # Aluminum 75C rho = 0.0354
    res_al = calculate_dc_resistance(turns, mtl, area, ConductorMaterial.ALUMINUM)
    assert math.isclose(res_al, 0.354, rel_tol=1e-4)

def test_calculate_i2r_losses():
    i_phase = 10.0
    r_phase = 0.5
    # 3 * 10^2 * 0.5 = 150
    loss = calculate_i2r_losses(i_phase, r_phase)
    assert loss == 150.0

def test_calculate_load_losses():
    hv = 100.0
    lv = 200.0
    res = calculate_load_losses(hv, lv, additional_factor=1.15)
    assert res["total_i2r_W"] == 300.0
    assert math.isclose(res["calculated_load_loss_W"], 345.0)
    assert math.isclose(res["stray_losses_W"], 45.0)

def test_estimate_core_losses():
    # Weight 1000kg, 1.5T, 50Hz, M4 -> ~0.89 * 1000 * 1.05 = 934.5
    res = estimate_core_losses(1000.0, 1.5, 50.0, "M4", 1.05)
    assert math.isclose(res, 934.5, rel_tol=1e-3)
    
    # ZDKH -> 0.75 * 1000 * 1.05 = 787.5
    res2 = estimate_core_losses(1000.0, 1.5, 50.0, "ZDKH", 1.05)
    assert math.isclose(res2, 787.5, rel_tol=1e-3)
