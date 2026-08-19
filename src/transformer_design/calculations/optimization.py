"""Deterministic Pareto optimization over a parameter grid for pre-design comparisons."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from typing import Any

from ..models.enums import LossEvaluationMode
from ..models.inputs import OrderInput
from .engine import synthesize_transformer
from .losses import calculate_dc_resistance, calculate_i2r_losses, calculate_load_losses


def _get_load_loss(result: dict[str, Any]) -> float:
    """Calculate load loss based on evaluation mode."""
    inputs: OrderInput = result["inputs"]
    
    if inputs.electrical.loss_evaluation_mode == LossEvaluationMode.CALCULATED:
        hv_turns = result["hv_turns"]["n_selected"]
        lv_turns = result["lv_turns"]["n_selected"]
        
        hv_len = result["cost_weight"]["geometry_assumptions"]["hv_mean_turn_length_m"]
        lv_len = result["cost_weight"]["geometry_assumptions"]["lv_mean_turn_length_m"]
        
        hv_area = result["hv_cond"]["a_selected_total"].to("mm**2").magnitude
        lv_area = result["lv_cond"]["a_selected_total"].to("mm**2").magnitude
        
        hv_r = calculate_dc_resistance(hv_turns, hv_len, hv_area, inputs.winding.hv_conductor_material)
        lv_r = calculate_dc_resistance(lv_turns, lv_len, lv_area, inputs.winding.lv_conductor_material)
        
        hv_i2r = calculate_i2r_losses(result["phase_values"]["hv_current"].magnitude, hv_r)
        lv_i2r = calculate_i2r_losses(result["phase_values"]["lv_current"].magnitude, lv_r)
        
        load_losses = calculate_load_losses(hv_i2r, lv_i2r, inputs.winding.additional_load_loss_factor)
        return load_losses["calculated_load_loss_W"]
        
    return inputs.electrical.load_loss_W


def _dominates(a: tuple[float, float, float], b: tuple[float, float, float]) -> bool:
    """Return True if a strictly dominates b in a minimization problem."""
    return (a[0] <= b[0] and a[1] <= b[1] and a[2] <= b[2]) and \
           (a[0] < b[0] or a[1] < b[1] or a[2] < b[2])


def run_pareto_optimization(
    inputs: OrderInput,
    *,
    flux_values: Sequence[float] = (1.50, 1.60, 1.65, 1.70),
    hv_current_density_values: Sequence[float] = (2.0, 2.5, 3.0),
    lv_current_density_values: Sequence[float] = (2.0, 2.5, 3.0),
    custom_prices: Mapping[str, float] | None = None,
    require_feasible: bool = True,
) -> dict[str, Any]:
    """Evaluate candidate parameter grid, filter invalid, and calculate Pareto front."""
    ranges = (flux_values, hv_current_density_values, lv_current_density_values)
    if any(not values for values in ranges):
        raise ValueError("Optimizasyon aralıkları boş olamaz.")
    if any(value <= 0 for values in ranges for value in values):
        raise ValueError("Optimizasyon değerleri pozitif olmalıdır.")

    valid_designs = []
    rejected_designs = []

    for flux, hv_j, lv_j in itertools.product(*ranges):
        # Create a deep copy to safely modify target values
        current_inputs = inputs.model_copy(deep=True)
        current_inputs.core.target_max_flux_density_T = flux
        current_inputs.winding.hv_target_current_density_A_mm2 = hv_j
        current_inputs.winding.lv_target_current_density_A_mm2 = lv_j
        
        params = {"flux_T": flux, "hv_j": hv_j, "lv_j": lv_j}
        
        try:
            result = synthesize_transformer(current_inputs, custom_prices=custom_prices)
            
            if require_feasible and not result.get("is_feasible", False):
                warnings = result.get("warnings", ["Bilinmeyen hata"])
                rejected_designs.append({
                    "parameters": params,
                    "reason": f"Tasarım geçerli değil: {', '.join(warnings)}"
                })
                continue
                
            # Extract objectives: total_cost, total_weight, load_loss
            total_cost = float(result["total_factory_cost"])
            total_weight = float(result["total_weight"])
            load_loss = float(_get_load_loss(result))
            
            result["_objectives"] = (total_cost, total_weight, load_loss)
            result["parameters"] = params
            valid_designs.append(result)
            
        except Exception as exc:
            rejected_designs.append({
                "parameters": params,
                "reason": str(exc)
            })

    # Calculate Pareto optimal set
    for i, design_i in enumerate(valid_designs):
        obj_i = design_i["_objectives"]
        is_pareto = True
        for j, design_j in enumerate(valid_designs):
            if i == j:
                continue
            obj_j = design_j["_objectives"]
            if _dominates(obj_j, obj_i):
                is_pareto = False
                break
        
        design_i["is_pareto_optimal"] = is_pareto
        # Clean up temporary objective tuple
        del design_i["_objectives"]

    return {
        "valid_designs": valid_designs,
        "rejected_designs": rejected_designs,
    }
