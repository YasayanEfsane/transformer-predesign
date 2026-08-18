"""Minimal programmatic example using the shared design engine."""

from transformer_design.calculations.engine import synthesize_transformer
from transformer_design.models.enums import (
    ConductorMaterial,
    CoolingMethod,
    CoreTopology,
    PhaseSystem,
)
from transformer_design.models.inputs import (
    CoreInfo,
    ElectricalInfo,
    GeneralInfo,
    InsulationThermalInfo,
    OrderInput,
    WindingInfo,
)


inputs = OrderInput(
    general=GeneralInfo(
        standard="IEC 60076",
        standard_edition="Proje baskısı",
        application_type="Dağıtım",
        phase_system=PhaseSystem.THREE_PHASE,
        rated_power_kVA=1000.0,
        rated_frequency_Hz=50.0,
        cooling_method=CoolingMethod.ONAN,
        indoor_outdoor="Outdoor",
        ambient_temperature_C=40.0,
        altitude_m=1000.0,
        protection_degree="IP54",
        tank_type="Corrugated",
    ),
    electrical=ElectricalInfo(
        hv_voltage_V=33000.0,
        lv_voltage_V=400.0,
        connection_group="Dyn11",
        tap_changer_side="HV",
        tap_changer_type="Off-Circuit",
        rated_short_circuit_impedance_percent=5.0,
        impedance_reference_temperature_C=75.0,
        no_load_loss_W=1700.0,
        load_loss_W=10500.0,
        load_loss_reference_temperature_C=75.0,
        load_loss_definition="total",
    ),
    winding=WindingInfo(
        hv_conductor_material=ConductorMaterial.COPPER,
        lv_conductor_material=ConductorMaterial.ALUMINUM,
    ),
    core=CoreInfo(
        core_topology=CoreTopology.THREE_LEG,
        number_of_legs=3,
        number_of_windows=2,
    ),
    insulation=InsulationThermalInfo(),
)

result = synthesize_transformer(inputs)
print(f"HV hat akımı: {result['line_currents']['i_hv_line'].to('A').magnitude:.2f} A")
print(f"Toplam ağırlık: {result['total_weight']:.1f} kg")
print(f"TOC: ${result['toc_usd']:,.2f}")
print("Uyarılar:", result["warnings"] or "yok")
