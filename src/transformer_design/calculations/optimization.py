"""Small deterministic grid-search optimizer for pre-design comparisons."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from typing import Any


def run_grid_search_optimizer(
    base_calc_func: Callable[[float, float, float], dict[str, Any]],
    objective: str = "toc",
    *,
    flux_values: Sequence[float] = (1.50, 1.60, 1.65, 1.70),
    hv_current_density_values: Sequence[float] = (2.0, 2.5, 3.0),
    lv_current_density_values: Sequence[float] = (2.0, 2.5, 3.0),
    require_feasible: bool = False,
) -> dict[str, Any]:
    """Evaluate every candidate and return the lowest valid objective value."""
    objective_keys = {"toc": "toc_usd", "factory_cost": "total_factory_cost"}
    if objective not in objective_keys:
        raise ValueError("Amaç 'toc' veya 'factory_cost' olmalıdır.")
    ranges = (flux_values, hv_current_density_values, lv_current_density_values)
    if any(not values for values in ranges):
        raise ValueError("Optimizasyon aralıkları boş olamaz.")
    if any(value <= 0 for values in ranges for value in values):
        raise ValueError("Optimizasyon değerleri pozitif olmalıdır.")

    best_value = float("inf")
    best_parameters: dict[str, float] | None = None
    best_result: dict[str, Any] | None = None
    evaluated_count = 0
    rejected_count = 0
    rejection_messages: list[str] = []

    for flux, hv_j, lv_j in itertools.product(*ranges):
        evaluated_count += 1
        try:
            result = base_calc_func(flux, hv_j, lv_j)
            if require_feasible and not result.get("is_feasible", False):
                rejected_count += 1
                continue
            value = float(result[objective_keys[objective]])
            if value < best_value:
                best_value = value
                best_parameters = {"flux_T": flux, "hv_j": hv_j, "lv_j": lv_j}
                best_result = result
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            rejected_count += 1
            if len(rejection_messages) < 5:
                rejection_messages.append(str(exc))

    if best_parameters is None or best_result is None:
        detail = f" İlk hatalar: {'; '.join(rejection_messages)}" if rejection_messages else ""
        raise ValueError(f"Hiçbir geçerli tasarım bulunamadı.{detail}")

    return {
        "best_value": best_value,
        "best_parameters": best_parameters,
        "best_result": best_result,
        "evaluated_count": evaluated_count,
        "rejected_count": rejected_count,
        "rejection_messages": rejection_messages,
    }
