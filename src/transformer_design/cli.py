"""Interactive command-line client backed by the shared design engine."""

from __future__ import annotations

import sys

from pydantic import ValidationError

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


def get_float(prompt: str, default: float) -> float:
    while True:
        raw_value = input(f"{prompt} [Varsayılan: {default}]: ").strip()
        if not raw_value:
            return default
        try:
            return float(raw_value)
        except ValueError:
            print("Lütfen geçerli bir sayı girin.")


def get_text(prompt: str, default: str) -> str:
    return input(f"{prompt} [Varsayılan: {default}]: ").strip() or default


def get_material(prompt: str, default: str) -> ConductorMaterial:
    while True:
        value = get_text(f"{prompt} (B: Bakır, A: Alüminyum)", default).upper()
        if value == "B":
            return ConductorMaterial.COPPER
        if value == "A":
            return ConductorMaterial.ALUMINUM
        print("B veya A girin.")


def build_interactive_input() -> OrderInput:
    print("\n1 · Elektriksel sipariş")
    power_kva = get_float("Anma gücü (kVA)", 1000.0)
    hv_voltage = get_float("HV hat gerilimi (V)", 33000.0)
    lv_voltage = get_float("LV hat gerilimi (V)", 400.0)
    connection = get_text("Bağlantı grubu", "Dyn11")
    impedance = get_float("Kısa devre empedansı (%)", 5.0)
    no_load_loss = get_float("Boşta kayıp (W)", 1700.0)
    load_loss = get_float("Yükte kayıp (W)", 10500.0)

    print("\n2 · Aktif kısım")
    flux_density = get_float("Hedef akı yoğunluğu (T)", 1.60)
    stacking_factor = get_float("Sac istifleme faktörü", 0.96)
    hv_material = get_material("HV sargı malzemesi", "B")
    lv_material = get_material("LV sargı malzemesi", "A")
    hv_current_density = get_float("HV akım yoğunluğu (A/mm²)", 3.0)
    lv_current_density = get_float("LV akım yoğunluğu (A/mm²)", 2.5)

    return OrderInput(
        general=GeneralInfo(
            standard="IEC 60076",
            standard_edition="Proje baskısı",
            application_type="Dağıtım",
            phase_system=PhaseSystem.THREE_PHASE,
            rated_power_kVA=power_kva,
            rated_frequency_Hz=50.0,
            cooling_method=CoolingMethod.ONAN,
            indoor_outdoor="Outdoor",
            ambient_temperature_C=40.0,
            altitude_m=1000.0,
            protection_degree="IP54",
            tank_type="Corrugated",
        ),
        electrical=ElectricalInfo(
            hv_voltage_V=hv_voltage,
            lv_voltage_V=lv_voltage,
            connection_group=connection,
            tap_changer_side="HV",
            tap_changer_type="Off-Circuit",
            rated_short_circuit_impedance_percent=impedance,
            impedance_reference_temperature_C=75.0,
            no_load_loss_W=no_load_loss,
            load_loss_W=load_loss,
            load_loss_reference_temperature_C=75.0,
            load_loss_definition="total",
        ),
        winding=WindingInfo(
            hv_conductor_material=hv_material,
            lv_conductor_material=lv_material,
            hv_target_current_density_A_mm2=hv_current_density,
            lv_target_current_density_A_mm2=lv_current_density,
        ),
        core=CoreInfo(
            core_topology=CoreTopology.THREE_LEG,
            number_of_legs=3,
            number_of_windows=2,
            target_max_flux_density_T=flux_density,
            stacking_factor=stacking_factor,
        ),
        insulation=InsulationThermalInfo(),
    )


def print_result(result: dict[str, object]) -> None:
    status = "TARAMA UYGUN" if result["is_feasible"] else "MÜHENDİSLİK KONTROLÜ GEREKLİ"
    print("\n" + "=" * 64)
    print(f"SONUÇ · {status}")
    print("=" * 64)
    print(f"HV / LV hat akımı : {result['line_currents']['i_hv_line'].to('A').magnitude:.2f} A / "
          f"{result['line_currents']['i_lv_line'].to('A').magnitude:.2f} A")
    print(f"HV / LV tur       : {result['hv_turns']['n_selected']} / {result['lv_turns']['n_selected']}")
    print(f"Çekirdek çapı     : {result['core_geom']['d_physical'].to('mm').magnitude:.1f} mm")
    print(f"Gerçek akı        : {result['actual_flux_density'].to('T').magnitude:.3f} T")
    print(f"Fiziksel uk       : %{result['physical_uk_percent']:.2f}")
    print(f"Tam yük verimi    : %{result['eff']['efficiency'] * 100:.3f}")
    print(f"Hot-spot          : {result['hot_spot_temperature_c']:.1f} °C")
    print(f"Toplam ağırlık    : {result['total_weight']:,.1f} kg")
    print(f"İmalat / TOC      : ${result['total_factory_cost']:,.2f} / ${result['toc_usd']:,.2f}")
    for warning in result["warnings"]:
        print(f"UYARI              : {warning}")
    print("\nBu çıktı ön tasarım taramasıdır; üretim onayı veya tip testi değildir.")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    print("TRANSFORMATÖR ÖN TASARIM UYGULAMASI")
    try:
        print_result(synthesize_transformer(build_interactive_input()))
    except (ValidationError, ValueError, ArithmeticError) as exc:
        print(f"\nTasarım hesaplanamadı: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

