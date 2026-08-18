from typing import Any

from pydantic import BaseModel, Field

from .enums import DataSource


class CalculatedValue(BaseModel):
    name: str
    symbol: str
    value: Any
    display_value: Any
    unit: str
    source: DataSource
    formula: str = ""
    inputs_used: dict[str, Any] = Field(default_factory=dict)
    unit_conversions: str = ""
    rounding_method: str = ""
    dependent_assumptions: list[str] = Field(default_factory=list)
    reliability_status: str = "confirmed"
    warnings: list[str] = Field(default_factory=list)
