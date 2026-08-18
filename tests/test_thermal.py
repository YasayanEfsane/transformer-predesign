import pytest

from transformer_design.calculations.thermal import simulate_dynamic_thermal


def test_dynamic_thermal_converges_to_rated_rises():
    rows = simulate_dynamic_thermal(
        [1.0] * 200,
        [27.0] * 200,
        rated_top_oil_rise_k=60.0,
        rated_hot_spot_gradient_k=23.0,
    )
    final = rows[-1]

    assert final["top_oil_rise_k"] == pytest.approx(60.0, rel=1e-6)
    assert final["hot_spot_gradient_k"] == pytest.approx(23.0, rel=1e-6)
    assert final["hot_spot_temperature_c"] == pytest.approx(110.0, rel=1e-6)
    assert final["aging_acceleration_factor"] == pytest.approx(1.0, rel=1e-6)


def test_dynamic_thermal_responds_to_load_step():
    rows = simulate_dynamic_thermal([0.5, 0.5, 1.2, 1.2], [25.0] * 4)

    assert rows[1]["hot_spot_temperature_c"] < rows[2]["hot_spot_temperature_c"]
    assert rows[2]["top_oil_temperature_c"] < rows[3]["top_oil_temperature_c"]


@pytest.mark.parametrize(
    ("loads", "ambient", "message"),
    [
        ([1.0], [20.0, 21.0], "aynı"),
        ([], [], "uzunlukta"),
        ([3.1], [20.0], "0 ile 3"),
    ],
)
def test_dynamic_thermal_validates_profiles(loads, ambient, message):
    with pytest.raises(ValueError, match=message):
        simulate_dynamic_thermal(loads, ambient)
