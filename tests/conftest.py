import pytest

from transformer_design.units import ureg


@pytest.fixture
def u():
    return ureg
