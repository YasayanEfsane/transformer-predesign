"""Birim kütüphanesi."""
from typing import Any

from pint import UnitRegistry

ureg: Any = UnitRegistry()
Q_ = ureg.Quantity
