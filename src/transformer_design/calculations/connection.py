import re
from typing import Dict, Any
from ..exceptions import UnsupportedConnectionGroupError

def parse_connection_group(connection_group: str) -> Dict[str, Any]:
    """Bağlantı grubunu ayrıştırır (örneğin: Dyn11)."""
    if not connection_group:
        raise UnsupportedConnectionGroupError("Bağlantı grubu boş olamaz.")
        
    pattern = r'^([A-Z])([a-z])([zn]?)([0-9]{1,2})$'
    match = re.match(pattern, connection_group)
    if not match:
        raise UnsupportedConnectionGroupError(f"Geçersiz veya desteklenmeyen bağlantı grubu formatı: {connection_group}")
        
    hv_conn = match.group(1)
    lv_conn = match.group(2)
    lv_neutral = match.group(3) == 'n'
    clock = int(match.group(4))
    
    if hv_conn not in ['Y', 'D']:
        raise UnsupportedConnectionGroupError(f"Desteklenmeyen HV bağlantısı: {hv_conn}")
    if lv_conn not in ['y', 'd', 'z']:
        raise UnsupportedConnectionGroupError(f"Desteklenmeyen LV bağlantısı: {lv_conn}")
    if clock < 0 or clock > 11:
        raise UnsupportedConnectionGroupError(f"Geçersiz saat değeri: {clock}")
        
    phase_shift_deg = clock * 30
    
    return {
        "hv_connection": hv_conn,
        "lv_connection": lv_conn,
        "lv_neutral_brought_out": lv_neutral,
        "clock_number": clock,
        "phase_shift_deg": phase_shift_deg
    }

def get_phase_voltage(v_line: Any, connection: str) -> Any:
    """Hat gerilimini faz gerilimine dönüştürür."""
    if connection.upper() == 'Y':
        return v_line / (3 ** 0.5)
    elif connection.upper() == 'D':
        return v_line
    elif connection.upper() == 'Z':
        return v_line / (3 ** 0.5)
    raise UnsupportedConnectionGroupError(f"Desteklenmeyen bağlantı tipi: {connection}")

def get_phase_current(i_line: Any, connection: str) -> Any:
    """Hat akımını faz akımına dönüştürür."""
    if connection.upper() == 'Y':
        return i_line
    elif connection.upper() == 'D':
        return i_line / (3 ** 0.5)
    elif connection.upper() == 'Z':
        return i_line
    raise UnsupportedConnectionGroupError(f"Desteklenmeyen bağlantı tipi: {connection}")
