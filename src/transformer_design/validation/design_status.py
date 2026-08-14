
from ..models.enums import DesignStatus
from ..models.inputs import OrderInput


def evaluate_design_status(inputs: OrderInput, checks_passed: dict[str, bool]) -> DesignStatus:
    """Tasarım durumunu değerlendirir."""
    if inputs.core.core_steel_grade is None or \
       inputs.insulation.hv_insulation_level_kV is None or \
       inputs.insulation.winding_temp_rise_limit_K is None or \
       inputs.general.altitude_m is None or \
       inputs.insulation.pollution_level is None or \
       inputs.winding.hv_winding_height_mm is None:
        return DesignStatus.INPUT_INCOMPLETE
        
    if not checks_passed.get("electrical", False):
        return DesignStatus.ELECTRICAL_PRE_DESIGN
        
    if not checks_passed.get("geometry", False):
        return DesignStatus.GEOMETRY_PRE_DESIGN
        
    if not checks_passed.get("loss", False):
        return DesignStatus.LOSS_CHECK_PENDING
        
    if not checks_passed.get("impedance", False):
        return DesignStatus.IMPEDANCE_CHECK_PENDING
        
    if not checks_passed.get("thermal", False):
        return DesignStatus.THERMAL_CHECK_PENDING
        
    if not checks_passed.get("mechanical", False):
        return DesignStatus.MECHANICAL_CHECK_PENDING
        
    if not checks_passed.get("insulation", False):
        return DesignStatus.INSULATION_CHECK_PENDING
        
    if not checks_passed.get("manufacturing", False):
        return DesignStatus.MANUFACTURING_REVIEW_REQUIRED
        
    return DesignStatus.PRODUCTION_READY
