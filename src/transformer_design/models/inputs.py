"""Validated inputs used by the transformer pre-design engine."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import ConductorMaterial, ConductorShape, CoolingMethod, CoreTopology, PhaseSystem, LossEvaluationMode


class InputModel(BaseModel):
    """Common strictness and whitespace rules for engineering inputs."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)


class GeneralInfo(InputModel):
    standard: str = Field(min_length=1, description="Uygulanan standart")
    standard_edition: str = Field(min_length=1, description="Standardın baskısı")
    application_type: str = Field(min_length=1, description="Transformatör uygulama türü")
    phase_system: PhaseSystem = Field(description="Faz sistemi")
    rated_power_kVA: float = Field(gt=0, description="Anma görünür gücü (kVA)")
    rated_frequency_Hz: float = Field(gt=0, le=400, description="Anma frekansı (Hz)")
    cooling_method: CoolingMethod = Field(description="Soğutma yöntemi")
    indoor_outdoor: str = Field(min_length=1, description="İç veya dış ortam kullanımı")
    ambient_temperature_C: float = Field(ge=-50, le=80, description="Ortam sıcaklığı (°C)")
    altitude_m: float = Field(ge=0, description="Rakım (m)")
    protection_degree: str = Field(min_length=1, description="Koruma derecesi")
    certification: str | None = Field(None, description="Sertifikasyon")
    tank_type: str = Field(min_length=1, description="Tank ve koruyucu yapı türü")
    paint_properties: str | None = Field(None, description="Boya ve yüzey özellikleri")


class ElectricalInfo(InputModel):
    hv_voltage_V: float = Field(gt=0, description="Yüksek gerilim hat gerilimi (V)")
    lv_voltage_V: float = Field(gt=0, description="Alçak gerilim hat gerilimi (V)")
    connection_group: str = Field(min_length=3, description="Bağlantı grubu")
    tap_percentages: list[float] | None = Field(None, description="Kademe yüzdeleri")
    tap_voltages_V: list[float] | None = Field(None, description="Kademe anma gerilimleri (V)")
    tap_changer_side: str = Field(min_length=2, description="Kademe değiştiricinin tarafı")
    tap_changer_type: str = Field(min_length=1, description="Kademe değiştirici türü")
    rated_short_circuit_impedance_percent: float = Field(
        gt=0, le=30, description="Anma kısa devre empedansı (%)"
    )
    impedance_reference_temperature_C: float = Field(
        ge=-50, le=250, description="Empedansın referans sıcaklığı (°C)"
    )
    no_load_loss_W: float = Field(gt=0, description="Boşta kayıp (W)")
    load_loss_W: float = Field(gt=0, description="Yük kaybı (W)")
    load_loss_reference_temperature_C: float = Field(
        ge=-50, le=250, description="Yük kaybının referans sıcaklığı (°C)"
    )
    load_loss_definition: str = Field(min_length=1, description="Yük kaybının tanımı")
    no_load_current_percent: float | None = Field(None, ge=0, le=100)
    allowed_voltage_regulation_percent: float | None = Field(None, ge=0, le=100)
    loss_tolerance_percent: float | None = Field(None, ge=0, le=100)
    impedance_tolerance_percent: float | None = Field(None, ge=0, le=100)
    loss_evaluation_mode: LossEvaluationMode = Field(LossEvaluationMode.GUARANTEED, description="Hesaplarda kullanilacak kayip kaynagi")

    @field_validator("connection_group")
    @classmethod
    def validate_connection_group(cls, value: str) -> str:
        match = re.fullmatch(r"([YD])([ydz])(n?)(\d{1,2})", value)
        if match is None or int(match.group(4)) > 11:
            raise ValueError("Bağlantı grubu Dyn11, Yyn0 veya YNd5 biçiminde olmalıdır.")
        return value

    @model_validator(mode="after")
    def validate_voltage_levels(self) -> "ElectricalInfo":
        if self.hv_voltage_V <= self.lv_voltage_V:
            raise ValueError("HV gerilimi LV geriliminden büyük olmalıdır.")
        return self


class WindingInfo(InputModel):
    hv_conductor_material: ConductorMaterial
    lv_conductor_material: ConductorMaterial
    hv_target_current_density_A_mm2: float = Field(3.0, gt=0, le=10)
    lv_target_current_density_A_mm2: float = Field(2.5, gt=0, le=10)
    hv_conductor_shape: ConductorShape | None = None
    lv_conductor_shape: ConductorShape | None = None
    hv_parallel_conductors: int = Field(1, ge=1)
    lv_parallel_conductors: int = Field(1, ge=1)
    hv_bare_conductor_width_mm: float | None = Field(None, gt=0)
    hv_bare_conductor_thickness_mm: float | None = Field(None, gt=0)
    hv_bare_conductor_diameter_mm: float | None = Field(None, gt=0)
    lv_bare_conductor_width_mm: float | None = Field(None, gt=0)
    lv_bare_conductor_thickness_mm: float | None = Field(None, gt=0)
    lv_bare_conductor_diameter_mm: float | None = Field(None, gt=0)
    hv_insulation_thickness_mm: float | None = Field(None, ge=0)
    lv_insulation_thickness_mm: float | None = Field(None, ge=0)
    hv_winding_height_mm: float = Field(380.0, gt=0)
    lv_winding_height_mm: float = Field(380.0, gt=0)
    hv_inner_diameter_mm: float | None = Field(None, gt=0)
    hv_outer_diameter_mm: float | None = Field(None, gt=0)
    lv_inner_diameter_mm: float | None = Field(None, gt=0)
    lv_outer_diameter_mm: float | None = Field(None, gt=0)
    hv_cooling_channels: int | None = Field(None, ge=0)
    lv_cooling_channels: int | None = Field(None, ge=0)
    hv_mean_turn_length_m: float | None = Field(None, gt=0)
    lv_mean_turn_length_m: float | None = Field(None, gt=0)
    additional_load_loss_factor: float = Field(1.15, ge=1.0, description="Eddy/stray kayiplari katsayisi")


class CoreInfo(InputModel):
    core_topology: CoreTopology
    number_of_legs: int = Field(ge=1)
    number_of_windows: int = Field(ge=1)
    core_steel_grade: str | None = None
    steel_thickness_mm: float | None = Field(None, gt=0)
    stacking_factor: float = Field(0.96, gt=0, le=1)
    stepped_core_fill_factor: float | None = Field(None, gt=0, le=1)
    target_max_flux_density_T: float = Field(1.60, gt=0, le=2.2)
    window_fill_factor: float | None = Field(None, gt=0, le=1)
    window_height_mm: float | None = Field(None, gt=0)
    window_width_mm: float | None = Field(None, gt=0)
    additional_no_load_loss_factor: float = Field(1.05, ge=1.0, description="Uretim isciligi cekirdek kayip artisi")


class InsulationThermalInfo(InputModel):
    hv_insulation_level_kV: float | None = Field(None, ge=0)
    lv_insulation_level_kV: float | None = Field(None, ge=0)
    lightning_impulse_withstand_kV: float | None = Field(None, ge=0)
    power_frequency_withstand_kV: float | None = Field(None, ge=0)
    winding_temp_rise_limit_K: float | None = Field(None, gt=0)
    top_oil_temp_rise_limit_K: float = Field(60.0, gt=0)
    insulation_thermal_class: str | None = None
    oil_type: str | None = None
    allowed_hot_spot_temp_C: float = Field(110.0, gt=0)
    pollution_level: str | None = None


class OrderInput(InputModel):
    general: GeneralInfo
    electrical: ElectricalInfo
    winding: WindingInfo
    core: CoreInfo
    insulation: InsulationThermalInfo

    @model_validator(mode="after")
    def validate_loss_and_impedance_consistency(self) -> "OrderInput":
        rated_va = self.general.rated_power_kVA * 1000.0
        resistance_pu = self.electrical.load_loss_W / rated_va
        impedance_pu = self.electrical.rated_short_circuit_impedance_percent / 100.0
        if resistance_pu > impedance_pu:
            raise ValueError(
                "Yük kaybından türetilen direnç bileşeni kısa devre empedansını aşamaz."
            )
        return self
