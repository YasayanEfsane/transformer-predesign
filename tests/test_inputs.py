import pytest
from pydantic import ValidationError


def test_rejects_hv_below_lv(order_input):
    with pytest.raises(ValidationError, match="HV gerilimi"):
        order_input.electrical.hv_voltage_V = 230.0


def test_rejects_invalid_connection_clock(order_input):
    with pytest.raises(ValidationError, match="Bağlantı grubu"):
        order_input.electrical.connection_group = "Dyn12"


def test_rejects_loss_component_above_impedance(order_input):
    payload = order_input.model_dump()
    payload["electrical"]["load_loss_W"] = 60000.0

    with pytest.raises(ValidationError, match="direnç bileşeni"):
        type(order_input).model_validate(payload)
