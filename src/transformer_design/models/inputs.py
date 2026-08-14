
from pydantic import BaseModel, Field

from .enums import ConductorMaterial, ConductorShape, CoolingMethod, CoreTopology, PhaseSystem


class GeneralInfo(BaseModel):
    standard: str = Field(description="Uygulanan standart")
    standard_edition: str = Field(description="Standardın baskısı")
    application_type: str = Field(description="Transformatör uygulama türü")
    phase_system: PhaseSystem = Field(description="Faz sistemi")
    rated_power_kVA: float = Field(description="Anma görünür gücü (kVA)")
    rated_frequency_Hz: float = Field(description="Anma frekansı (Hz)")
    cooling_method: CoolingMethod = Field(description="Soğutma yöntemi")
    indoor_outdoor: str = Field(description="İç veya dış ortam kullanımı")
    ambient_temperature_C: float = Field(description="Ortam sıcaklığı (°C)")
    altitude_m: float = Field(description="Rakım (m)")
    protection_degree: str = Field(description="Koruma derecesi")
    certification: str | None = Field(None, description="Sertifikasyon")
    tank_type: str = Field(description="Tank ve koruyucu yapı türü")
    paint_properties: str | None = Field(None, description="Boya ve yüzey özellikleri")

class ElectricalInfo(BaseModel):
    hv_voltage_V: float = Field(description="Yüksek gerilim hat gerilimi (V)")
    lv_voltage_V: float = Field(description="Alçak gerilim hat gerilimi (V)")
    connection_group: str = Field(description="Bağlantı grubu")
    tap_percentages: list[float] | None = Field(None, description="Kademe yüzdeleri")
    tap_voltages_V: list[float] | None = Field(None, description="Kademe anma gerilimleri (V)")
    tap_changer_side: str = Field(description="Kademe değiştiricinin bulunduğu taraf (HV/LV)")
    tap_changer_type: str = Field(description="Kademe değiştirici türü")
    rated_short_circuit_impedance_percent: float = Field(description="Anma kısa devre empedansı (%)")
    impedance_reference_temperature_C: float = Field(description="Empedansın referans sıcaklığı (°C)")
    no_load_loss_W: float = Field(description="Boşta kayıp (W)")
    load_loss_W: float = Field(description="Yük kaybı (W)")
    load_loss_reference_temperature_C: float = Field(description="Yük kaybının referans sıcaklığı (°C)")
    load_loss_definition: str = Field(description="Yük kaybının tanımı (toplam/DC)")
    no_load_current_percent: float | None = Field(None, description="Boşta akım (%)")
    allowed_voltage_regulation_percent: float | None = Field(None, description="İzin verilen gerilim regülasyonu (%)")
    loss_tolerance_percent: float | None = Field(None, description="Kayıp toleransları (%)")
    impedance_tolerance_percent: float | None = Field(None, description="Empedans toleransları (%)")

class WindingInfo(BaseModel):
    hv_conductor_material: ConductorMaterial
    lv_conductor_material: ConductorMaterial
    hv_target_current_density_A_mm2: float | None = None
    lv_target_current_density_A_mm2: float | None = None
    hv_conductor_shape: ConductorShape | None = None
    lv_conductor_shape: ConductorShape | None = None
    hv_parallel_conductors: int = 1
    lv_parallel_conductors: int = 1
    hv_bare_conductor_width_mm: float | None = None
    hv_bare_conductor_thickness_mm: float | None = None
    hv_bare_conductor_diameter_mm: float | None = None
    lv_bare_conductor_width_mm: float | None = None
    lv_bare_conductor_thickness_mm: float | None = None
    lv_bare_conductor_diameter_mm: float | None = None
    hv_insulation_thickness_mm: float | None = None
    lv_insulation_thickness_mm: float | None = None
    hv_winding_height_mm: float | None = None
    lv_winding_height_mm: float | None = None
    hv_inner_diameter_mm: float | None = None
    hv_outer_diameter_mm: float | None = None
    lv_inner_diameter_mm: float | None = None
    lv_outer_diameter_mm: float | None = None
    hv_cooling_channels: int | None = None
    lv_cooling_channels: int | None = None
    hv_mean_turn_length_m: float | None = None
    lv_mean_turn_length_m: float | None = None

class CoreInfo(BaseModel):
    core_topology: CoreTopology
    number_of_legs: int
    number_of_windows: int
    core_steel_grade: str | None = None
    steel_thickness_mm: float | None = None
    stacking_factor: float | None = None
    stepped_core_fill_factor: float | None = None
    target_max_flux_density_T: float | None = None
    window_fill_factor: float | None = None
    window_height_mm: float | None = None
    window_width_mm: float | None = None

class InsulationThermalInfo(BaseModel):
    hv_insulation_level_kV: float | None = None
    lv_insulation_level_kV: float | None = None
    lightning_impulse_withstand_kV: float | None = None
    power_frequency_withstand_kV: float | None = None
    winding_temp_rise_limit_K: float | None = None
    top_oil_temp_rise_limit_K: float | None = None
    insulation_thermal_class: str | None = None
    oil_type: str | None = None
    allowed_hot_spot_temp_C: float | None = None
    pollution_level: str | None = None

class OrderInput(BaseModel):
    general: GeneralInfo
    electrical: ElectricalInfo
    winding: WindingInfo
    core: CoreInfo
    insulation: InsulationThermalInfo
