"""Public validated models and enumerations."""

from .assumptions import DesignAssumptions
from .enums import (
    ConductorMaterial,
    ConductorShape,
    CoolingMethod,
    CoreTopology,
    DataSource,
    DesignStatus,
    PhaseSystem,
)
from .inputs import (
    CoreInfo,
    ElectricalInfo,
    GeneralInfo,
    InsulationThermalInfo,
    OrderInput,
    WindingInfo,
)
from .results import CalculatedValue

__all__ = [
    "CalculatedValue",
    "ConductorMaterial",
    "ConductorShape",
    "CoolingMethod",
    "CoreInfo",
    "CoreTopology",
    "DataSource",
    "DesignAssumptions",
    "DesignStatus",
    "ElectricalInfo",
    "GeneralInfo",
    "InsulationThermalInfo",
    "OrderInput",
    "PhaseSystem",
    "WindingInfo",
]
