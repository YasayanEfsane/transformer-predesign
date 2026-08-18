import pytest

from transformer_design.calculations.connection import (
    get_phase_current,
    get_phase_voltage,
    parse_connection_group,
)
from transformer_design.calculations.electrical import (
    calculate_efficiency,
    calculate_impedance_components,
    calculate_rated_currents,
)
from transformer_design.exceptions import (
    PhysicallyInconsistentDataError,
    UnsupportedConnectionGroupError,
)
from transformer_design.units import Q_


def test_parse_connection_group():
    res = parse_connection_group("Dyn11")
    assert res["hv_connection"] == "D"
    assert res["lv_connection"] == "y"
    assert res["lv_neutral_brought_out"] is True
    assert res["clock_number"] == 11
    assert res["phase_shift_deg"] == 330
    
    with pytest.raises(UnsupportedConnectionGroupError):
        parse_connection_group("Ayn11")

def test_phase_conversions():
    v_line = Q_(400, 'V')
    assert get_phase_voltage(v_line, 'D') == v_line
    v_phase_y = get_phase_voltage(v_line, 'Y')
    assert pytest.approx(v_phase_y.magnitude, 0.01) == 230.94
    
    i_line = Q_(100, 'A')
    assert get_phase_current(i_line, 'Y') == i_line
    i_phase_d = get_phase_current(i_line, 'D')
    assert pytest.approx(i_phase_d.magnitude, 0.01) == 57.73

def test_calculate_rated_currents():
    s_rated = Q_(1000, 'kVA')
    v_hv_line = Q_(33000, 'V')
    v_lv_line = Q_(400, 'V')
    
    res = calculate_rated_currents(s_rated, v_hv_line, v_lv_line)
    assert pytest.approx(res["i_hv_line"].to('A').magnitude, 0.01) == 17.50
    assert pytest.approx(res["i_lv_line"].to('A').magnitude, 0.01) == 1443.37

def test_calculate_impedance_components():
    s_rated = Q_(1000, 'kVA')
    v_phase = Q_(400, 'V') / (3**0.5)
    i_phase = Q_(1443.37, 'A')
    p_load_rated = Q_(10, 'kW')
    u_k_percent = 5.0
    
    res = calculate_impedance_components(s_rated, v_phase, i_phase, p_load_rated, u_k_percent)
    
    assert pytest.approx(res["z_pu"], 0.01) == 0.05
    assert pytest.approx(res["r_pu"], 0.01) == 0.01
    assert pytest.approx(res["x_pu"], 0.01) == 0.0489
    
    with pytest.raises(PhysicallyInconsistentDataError):
        calculate_impedance_components(s_rated, v_phase, i_phase, Q_(60, 'kW'), u_k_percent)

def test_efficiency():
    s_rated = Q_(1000, 'kVA')
    p_no_load = Q_(2, 'kW')
    p_load = Q_(10, 'kW')
    
    res = calculate_efficiency(s_rated, p_no_load, p_load, load_fraction=0.5)
    
    assert pytest.approx(res["efficiency"], 0.001) == 0.991
    assert pytest.approx(res["load_fraction_max_eta"], 0.01) == (2/10)**0.5
