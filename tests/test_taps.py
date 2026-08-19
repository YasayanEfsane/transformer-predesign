"""Unit tests for tap and voltage regulation calculations."""
from __future__ import annotations

import math
from transformer_design.calculations.taps import calculate_tap_turns, calculate_voltage_regulation

def test_calculate_tap_turns_basic():
    taps = [5.0, 0.0, -5.0]
    nominal_turns = 1000
    
    result = calculate_tap_turns(nominal_turns, taps)
    
    assert "5.0%" in result
    assert result["5.0%"]["ideal_turns"] == 1050
    assert result["5.0%"]["actual_turns"] == 1050
    assert result["5.0%"]["error_percent"] == 0.0
    
    assert "0.0%" in result
    assert result["0.0%"]["ideal_turns"] == 1000
    assert result["0.0%"]["actual_turns"] == 1000
    
    assert "-5.0%" in result
    assert result["-5.0%"]["ideal_turns"] == 950
    assert result["-5.0%"]["actual_turns"] == 950

def test_calculate_tap_turns_rounding():
    taps = [2.5]
    nominal_turns = 100
    # ideal = 102.5 -> actual = 102 (or 103 depending on round)
    # Python round(102.5) -> 102 (round to even)
    result = calculate_tap_turns(nominal_turns, taps)
    assert result["2.5%"]["actual_turns"] == 102
    assert math.isclose(result["2.5%"]["error_percent"], -0.4878, abs_tol=0.01)

def test_voltage_regulation():
    uk = 6.0
    ur = 1.0
    result = calculate_voltage_regulation(uk, ur, [1.0, 0.8])
    
    assert "1.0" in result
    # For pf=1.0: Reg = ur + (ux^2)/200 = 1.0 + 35/200 = 1.0 + 0.175 = 1.175
    assert math.isclose(result["1.0"]["inductive_percent"], 1.175, abs_tol=0.01)
    
    assert "0.8" in result
    # pf=0.8, sin=0.6, ux = sqrt(35) = 5.916
    # Reg_ind = 1.0*0.8 + 5.916*0.6 + ... = 0.8 + 3.5496 = 4.3496 + ...
    assert result["0.8"]["inductive_percent"] > 4.0
    
def test_voltage_regulation_invalid():
    # uk < ur is impossible physically
    result = calculate_voltage_regulation(1.0, 6.0)
    assert result == {}
