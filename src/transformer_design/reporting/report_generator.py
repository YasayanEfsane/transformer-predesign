
from ..models.assumptions import DesignAssumptions
from ..models.enums import DesignStatus
from ..models.inputs import OrderInput
from ..models.results import CalculatedValue


def generate_report(inputs: OrderInput, assumptions: DesignAssumptions, status: DesignStatus, results: list[CalculatedValue]) -> str:
    """Türkçe hesap raporu oluşturur."""
    lines = []
    lines.append("# Üç Fazlı Dağıtım Transformatörü Hesap Raporu\n")
    
    lines.append("## 1. Tasarım Durumu")
    lines.append(f"**Durum:** {status.value}\n")
    
    lines.append("## 2. Sipariş Girdileri")
    lines.append(f"- Güç: {inputs.general.rated_power_kVA} kVA")
    lines.append(f"- Yüksek Gerilim: {inputs.electrical.hv_voltage_V} V")
    lines.append(f"- Alçak Gerilim: {inputs.electrical.lv_voltage_V} V")
    lines.append(f"- Bağlantı Grubu: {inputs.electrical.connection_group}")
    lines.append("")
    
    lines.append("## 3. Mühendislik Kabulleri")
    lines.append(f"- Hedef Akı Yoğunluğu: {assumptions.target_flux_density_T} T")
    lines.append(f"- HV Akım Yoğunluğu: {assumptions.hv_current_density_A_mm2} A/mm2")
    lines.append(f"- LV Akım Yoğunluğu: {assumptions.lv_current_density_A_mm2} A/mm2")
    lines.append("")
    
    lines.append("## 4. Hesap Sonuçları")
    for res in results:
        lines.append(f"### {res.name} ({res.symbol})")
        lines.append(f"- Değer: {res.display_value} {res.unit}")
        lines.append(f"- Kaynak: {res.source.value}")
        if res.warnings:
            lines.append("- Uyarılar:")
            for w in res.warnings:
                lines.append(f"  - {w}")
        lines.append("")
        
    return "\n".join(lines)
