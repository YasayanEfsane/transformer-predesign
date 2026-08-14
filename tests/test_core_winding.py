import pytest

from transformer_design.calculations.core import calculate_turn_voltage, calculate_window_area
from transformer_design.calculations.winding import calculate_resistance_and_loss, calculate_turns
from transformer_design.units import Q_


def test_calculate_turn_voltage():
    v = calculate_turn_voltage(method="empirical", f=Q_(50, 'Hz'), s_rated=Q_(1000, 'kVA'), empirical_coefficient=0.045)
    assert pytest.approx(v.magnitude, 0.01) == 1.423
    
def test_calculate_turns():
    v_phase = Q_(230.94, 'V')
    e_turn_init = Q_(1.423, 'V')
    
    res = calculate_turns(v_phase, e_turn_init)
    
    assert res["n_selected"] == 162
    assert pytest.approx(res["e_turn_actual"].magnitude, 0.001) == 230.94 / 162
    
def test_resistance_and_loss():
    rho = Q_(0.017241, 'ohm * mm**2 / m')
    t_ref = Q_(20, 'degC')
    t_target = Q_(75, 'degC')
    alpha = 0.00393
    turns = 100
    mean_length = Q_(1.5, 'm')
    a_cond = Q_(10, 'mm**2')
    i_phase = Q_(50, 'A')
    
    res = calculate_resistance_and_loss(rho, t_ref, t_target, alpha, turns, mean_length, a_cond, i_phase)
    
    r_expected = 0.017241 * (1 + 0.00393 * 55) * 150 / 10
    
    assert pytest.approx(res["r_dc"].magnitude, 0.01) == r_expected
    
    p_dc_expected = 3 * (50**2) * r_expected
    assert pytest.approx(res["p_dc_winding"].magnitude, 0.01) == p_dc_expected

def test_window_area():
    turns_hv = 1000
    a_cond_hv = Q_(5, 'mm**2')
    turns_lv = 100
    a_cond_lv = Q_(50, 'mm**2')
    
    res = calculate_window_area(turns_hv, a_cond_hv, turns_lv, a_cond_lv, topology_factor=1.0, k_u_target=0.35)
    
    q_window = 1000 * 5 + 100 * 50
    a_req = 10000 / 0.35
    
    assert pytest.approx(res["q_window"].magnitude, 0.1) == 10000
    assert pytest.approx(res["a_window_required"].magnitude, 0.1) == 28571.4
