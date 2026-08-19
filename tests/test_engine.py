
import pytest

from transformer_design.calculations.engine import synthesize_transformer
from transformer_design.calculations.optimization import run_pareto_optimization


def test_engine_uses_shared_turn_voltage_assumption(order_input):
    result = synthesize_transformer(order_input)

    assert result["turn_voltage"].to("V").magnitude == pytest.approx(1.423, rel=0.01)
    assert result["hv_turns"]["n_selected"] > result["lv_turns"]["n_selected"]
    assert result["total_factory_cost"] > 0
    assert result["total_weight"] > 0
    assert result["toc_usd"] > result["total_factory_cost"]
    assert set(result["design_checks"]) == {
        "flux_density",
        "ampere_turn_balance",
        "impedance_screening",
        "hot_spot_temperature",
    }


def test_engine_is_deterministic_for_explicit_prices(order_input):
    prices = {"COPPER": 10.0, "ALUMINUM": 3.0, "STEEL": 2.5}
    first = synthesize_transformer(order_input, prices)
    second = synthesize_transformer(order_input, prices)

    assert first["total_factory_cost"] == pytest.approx(second["total_factory_cost"])
    assert first["total_weight"] == pytest.approx(second["total_weight"])


def test_optimizer_reports_candidate_counts(order_input):
    optimized = run_pareto_optimization(
        order_input,
        flux_values=(1.5, 1.6),
        hv_current_density_values=(2.5,),
        lv_current_density_values=(2.0, 2.5),
    )

    assert len(optimized["valid_designs"]) + len(optimized["rejected_designs"]) == 4
