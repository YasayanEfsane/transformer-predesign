from pydantic import BaseModel, Field


class DesignAssumptions(BaseModel):
    target_flux_density_T: float = Field(1.5, description="Hedef manyetik akı yoğunluğu (T)")
    turn_voltage_selection_method: str = Field("empirical", description="Tur başına gerilim seçim yöntemi")
    turn_voltage_empirical_coefficient: float = Field(0.045, description="Tur başına gerilim ampirik katsayısı")
    emf_waveform_factor: float = Field(4.44, description="EMK dalga şekli katsayısı (sinüzoidal için 4.44)")
    stacking_factor: float = Field(0.96, description="Sac paketleme faktörü")
    stepped_core_shape_factor: float = Field(0.9, description="Kademeli kesit şekil faktörü")
    hv_current_density_A_mm2: float = Field(3.0, description="HV sargısı akım yoğunluğu")
    lv_current_density_A_mm2: float = Field(3.0, description="LV sargısı akım yoğunluğu")
    window_fill_factor: float = Field(0.35, description="Pencere doluluk faktörü")
    copper_resistivity_ohm_mm2_m_20C: float = Field(0.017241, description="Bakır özdirenci (20°C)")
    aluminum_resistivity_ohm_mm2_m_20C: float = Field(0.028264, description="Alüminyum özdirenci (20°C)")
    resistivity_reference_temperature_C: float = Field(20.0, description="Özdirenç referans sıcaklığı")
    copper_resistance_temp_coefficient: float = Field(0.00393, description="Bakır direnç sıcaklık katsayısı (1/K)")
    aluminum_resistance_temp_coefficient: float = Field(0.00403, description="Alüminyum direnç sıcaklık katsayısı (1/K)")
