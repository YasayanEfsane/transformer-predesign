"""Numaralandırılmış tip tanımları."""
from enum import Enum


class DataSource(Enum):
    """Verinin kaynağını belirtir."""
    ORDER_INPUT = "order_input"
    ENGINEERING_ASSUMPTION = "engineering_assumption"
    CALCULATED = "calculated"
    SELECTED_STANDARD_SIZE = "selected_standard_size"
    MANUFACTURER_DATA = "manufacturer_data"
    UNCONFIRMED = "unconfirmed"

class PhaseSystem(Enum):
    THREE_PHASE = "3-phase"
    SINGLE_PHASE = "1-phase"

class CoolingMethod(Enum):
    ONAN = "ONAN"
    ONAF = "ONAF"
    KNAN = "KNAN"
    KNAF = "KNAF"
    DRY_TYPE = "DRY_TYPE"

class ConductorMaterial(Enum):
    COPPER = "Copper"
    ALUMINUM = "Aluminum"
    
class ConductorShape(Enum):
    ROUND = "Round"
    RECTANGULAR = "Rectangular"
    FOIL = "Foil"

class CoreTopology(Enum):
    THREE_LEG = "3-leg"
    FIVE_LEG = "5-leg"
    
class DesignStatus(Enum):
    INPUT_INCOMPLETE = "input_incomplete"
    ELECTRICAL_PRE_DESIGN = "electrical_pre_design"
    GEOMETRY_PRE_DESIGN = "geometry_pre_design"
    LOSS_CHECK_PENDING = "loss_check_pending"
    IMPEDANCE_CHECK_PENDING = "impedance_check_pending"
    THERMAL_CHECK_PENDING = "thermal_check_pending"
    MECHANICAL_CHECK_PENDING = "mechanical_check_pending"
    INSULATION_CHECK_PENDING = "insulation_check_pending"
    MANUFACTURING_REVIEW_REQUIRED = "manufacturing_review_required"
    PRODUCTION_READY = "production_ready"
