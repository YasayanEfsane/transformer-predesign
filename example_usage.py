import json
from transformer_design.units import Q_
from transformer_design.models.enums import PhaseSystem, CoolingMethod, ConductorMaterial, CoreTopology, DesignStatus
from transformer_design.models.inputs import OrderInput, GeneralInfo, ElectricalInfo, WindingInfo, CoreInfo, InsulationThermalInfo
from transformer_design.models.assumptions import DesignAssumptions
from transformer_design.models.results import CalculatedValue
from transformer_design.calculations.electrical import calculate_rated_currents
from transformer_design.reporting.report_generator import generate_report

def main():
    # 1. Sipariş Girdilerini Oluştur (Örnek veriler)
    inputs = OrderInput(
        general=GeneralInfo(
            standard="IEC 60076",
            standard_edition="2011",
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
        insulation=InsulationThermalInfo(
            winding_temp_rise_limit_K=65.0,
            top_oil_temp_rise_limit_K=60.0,
            pollution_level="Heavy",
        )
    )

    # 2. Mühendislik Kabullerini Yükle (Varsayılanları kullanıyoruz)
    assumptions = DesignAssumptions()

    # 3. Hesaplamaları Çalıştır (Örnek olarak akım hesabını yapıyoruz)
    s_rated = Q_(inputs.general.rated_power_kVA, 'kVA')
    v_hv_line = Q_(inputs.electrical.hv_voltage_V, 'V')
    v_lv_line = Q_(inputs.electrical.lv_voltage_V, 'V')
    
    currents = calculate_rated_currents(s_rated, v_hv_line, v_lv_line)

    # Sonuçları listeye ekle
    results = [
        CalculatedValue(
            name="Yüksek Gerilim Hat Akımı",
            symbol="I_hv_line",
            value=currents["i_hv_line"],
            display_value=round(currents["i_hv_line"].to('A').magnitude, 2),
            unit="A",
            source="calculated",
            formula="S / (sqrt(3) * V_hv)"
        ),
        CalculatedValue(
            name="Alçak Gerilim Hat Akımı",
            symbol="I_lv_line",
            value=currents["i_lv_line"],
            display_value=round(currents["i_lv_line"].to('A').magnitude, 2),
            unit="A",
            source="calculated",
            formula="S / (sqrt(3) * V_lv)"
        )
    ]

    # 4. Rapor Üret
    status = DesignStatus.ELECTRICAL_PRE_DESIGN # Örnek durum
    report = generate_report(inputs, assumptions, status, results)
    
    print("="*60)
    print(report)
    print("="*60)

if __name__ == "__main__":
    main()
