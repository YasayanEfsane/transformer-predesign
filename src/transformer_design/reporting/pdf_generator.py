from fpdf import FPDF
import datetime

def sanitize_text(text: str) -> str:
    charmap = {
        'ı': 'i', 'İ': 'I',
        'ş': 's', 'Ş': 'S',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C',
        '±': '+/-'
    }
    if not isinstance(text, str):
        text = str(text)
    for tr, eng in charmap.items():
        text = text.replace(tr, eng)
    return text

class TransformerReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 22)
        self.set_text_color(44, 75, 100)
        self.cell(0, 12, 'TRANSFORMATOR ON TASARIM RAPORU', border=False, align='C', ln=True)
        
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, 'MUHENDISLIK TARAMASI / SCREENING', border=False, align='C', ln=True)
        
        self.set_draw_color(46, 160, 67)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        self.set_line_width(0.2)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'Bu rapor, optimizasyon yazilimi tarafindan on tasarim araci olarak uretilmistir. Uretime hazir degildir.', align='C', ln=True)
        self.cell(0, 5, sanitize_text(f'Sayfa {self.page_no()} / {{nb}} - Uretim Tarihi: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}'), align='C')

def generate_engineering_pdf_bytes(result: dict) -> bytes:
    pdf = TransformerReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    col_w = [45, 45, 45, 55]
    row_h = 9
    
    def draw_header(title):
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.set_fill_color(44, 75, 100)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(190, 10, sanitize_text(title), border=1, align='C', fill=True, ln=True)

    def draw_row(label1, val1, label2, val2):
        if pdf.get_y() > 270:
            pdf.add_page()
        pdf.set_fill_color(245, 245, 245)
        pdf.set_draw_color(200, 200, 200)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(col_w[0], row_h, sanitize_text(label1), border=1, fill=True, align='L')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(col_w[1], row_h, sanitize_text(str(val1)), border=1, align='L')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(col_w[2], row_h, sanitize_text(label2), border=1, fill=True, align='L')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(col_w[3], row_h, sanitize_text(str(val2)), border=1, align='L')
        pdf.ln(row_h)
        
    def draw_full_row(label, val):
        pdf.set_fill_color(245, 245, 245)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(45, row_h, sanitize_text(label), border=1, fill=True, align='L')
        pdf.set_text_color(10, 10, 10)
        pdf.cell(145, row_h, sanitize_text(str(val)), border=1, align='L')
        pdf.ln(row_h)

    inputs = result.get('inputs')
    if not inputs:
        return bytes()

    # 1. Sipariş Girdileri
    draw_header('1. SIPARIS GIRDILERI')
    draw_row('Uygulama', inputs.general.application_type, 'Standart', inputs.general.standard)
    draw_row('Anma Gucu (kVA)', f'{inputs.general.rated_power_kVA:g}', 'Faz', inputs.general.phase_system.value)
    draw_row('Frekans (Hz)', f'{inputs.general.rated_frequency_Hz:g}', 'Sogutma', inputs.general.cooling_method.value)
    draw_row('Baglanti Grubu', inputs.electrical.connection_group, 'Rakim (m)', f'{inputs.general.altitude_m:g}')
    draw_row('HV Gerilim (V)', f'{inputs.electrical.hv_voltage_V:g}', 'LV Gerilim (V)', f'{inputs.electrical.lv_voltage_V:g}')
    pdf.ln(5)

    # 2. Kayıplar ve Karşılaştırma
    draw_header('2. HESAPLANAN VE GARANTI KAYIP KARSILASTIRMASI')
    load_mode = inputs.electrical.loss_evaluation_mode.value
    draw_full_row('Kullanilan Kayip Modeli:', load_mode.upper())
    draw_row('Garanti Yuk Kaybi (W)', f'{inputs.electrical.load_loss_W:g}', 'Hesaplanan Yuk Kaybi', f'{result.get("calculated_load_losses", {}).get("calculated_load_loss_W", 0):.0f}')
    draw_row('Garanti Bosta Kayip (W)', f'{inputs.electrical.no_load_loss_W:g}', 'Hesaplanan Bosta Kayip', f'{result.get("calculated_no_load_loss_W", 0):.0f}')
    draw_row('TOC Faktoru A', f'{result.get("toc_usd", 0):.0f}', 'TOC Faktoru B', 'Uygulandi')
    pdf.ln(5)

    # 3. Elektriksel Sonuçlar
    draw_header('3. ELEKTRIKSEL SONUCLAR')
    
    # Unit stripping for pint quantities
    uk = result.get("impedance_percent", 0)
    uk = uk.magnitude if hasattr(uk, "magnitude") else uk
    eff = result.get("eff", {}).get("efficiency", 0)
    
    i_hv = result.get("line_currents", {}).get("i_hv_line", 0)
    i_hv = i_hv.magnitude if hasattr(i_hv, "magnitude") else i_hv
    i_lv = result.get("line_currents", {}).get("i_lv_line", 0)
    i_lv = i_lv.magnitude if hasattr(i_lv, "magnitude") else i_lv
    
    hv_j = result.get("hv_cond", {}).get("j_actual", 0)
    hv_j = hv_j.magnitude if hasattr(hv_j, "magnitude") else hv_j
    lv_j = result.get("lv_cond", {}).get("j_actual", 0)
    lv_j = lv_j.magnitude if hasattr(lv_j, "magnitude") else lv_j

    draw_row('Empedans (uk) %', f'{uk:.2f}', 'Verim (%)', f'{eff*100:.2f}')
    draw_row('HV Akim (A)', f'{i_hv:.2f}', 'LV Akim (A)', f'{i_lv:.2f}')
    draw_row('HV J (A/mm2)', f'{hv_j:.2f}', 'LV J (A/mm2)', f'{lv_j:.2f}')
    draw_row('HV Sarim', f'{result.get("hv_turns", {}).get("n_selected", 0)}', 'LV Sarim', f'{result.get("lv_turns", {}).get("n_selected", 0)}')
    pdf.ln(5)

    # 4. Kademeler ve Regülasyon
    draw_header('4. KADEMELER VE GERILIM REGULASYONU')
    taps = result.get('taps_turns', {})
    if taps:
        tap_str = ", ".join(taps.keys())
        draw_full_row('Kademeler:', tap_str)
    
    reg = result.get('voltage_regulation', {})
    if '1.0' in reg:
        draw_row('Regulasyon (PF=1.0)', f'{reg["1.0"].get("inductive_percent", 0):.2f}%', 'Regulasyon (PF=0.8)', f'{reg.get("0.8", {}).get("inductive_percent", 0):.2f}%')
    pdf.ln(5)

    # 5. Geometri
    draw_header('5. CEKIRDEK VE SARGI GEOMETRISI')
    core_d = result.get("core_geom", {}).get("d_physical", 0)
    core_d = core_d.magnitude if hasattr(core_d, "magnitude") else core_d
    core_a = result.get("core_geom", {}).get("a_core_gross", 0)
    core_a = core_a.magnitude if hasattr(core_a, "magnitude") else core_a
    actual_flux = result.get("actual_flux_t", 0)
    
    draw_row('Cekirdek Capi (mm)', f'{core_d:.1f}', 'Brut Alan (cm2)', f'{core_a:.1f}')
    draw_row('Gercek Aki Yogunlugu', f'{actual_flux:.2f} T', 'Yag Tipi', f'{inputs.insulation.oil_type}')
    pdf.ln(5)

    # 6. Termal
    draw_header('6. TERMAL PROFIL')
    draw_row('Tepe Yag Sicakligi', f'{inputs.insulation.top_oil_temp_rise_limit_K} K', 'Tahmini Hot-Spot', f'{result.get("hot_spot_temperature_c", 0):.1f} C')
    
    rad_area = result.get("cooling", {}).get("radiator_area_needed", 0)
    rad_area = rad_area.magnitude if hasattr(rad_area, "magnitude") else rad_area
    tank_area = result.get("tank_surface", 0)
    tank_area = tank_area.magnitude if hasattr(tank_area, "magnitude") else tank_area
    
    draw_row('Gerekli Sogutma Alani', f'{rad_area:.1f} m2', 'Tank Yuzeyi', f'{tank_area:.1f} m2')
    pdf.ln(5)

    # 7. Maliyet ve Ağırlık
    draw_header('7. MALIYET VE AGIRLIK DAGILIMI')
    costs_usd = result.get("costs", {}).get("costs_usd", {})
    weights = result.get("costs", {}).get("weights_kg", {})
    if not costs_usd:
        # Compatibility with older cost_weight key if present
        costs_usd = result.get("cost_weight", {}).get("costs_usd", {})
        weights = result.get("cost_weight", {}).get("weights_kg", {})
        
    draw_row('Aktif Kisim Agirligi', f'{weights.get("active_part", 0):.0f} kg', 'Tank + Yag', f'{weights.get("tank", 0) + weights.get("oil", 0):.0f} kg')
    draw_row('Cekirdek Maliyeti', f'${costs_usd.get("core", 0):.0f}', 'HV/LV Maliyeti', f'${costs_usd.get("hv_winding", 0) + costs_usd.get("lv_winding", 0):.0f}')
    draw_full_row('Toplam Tahmini Maliyet:', f'${costs_usd.get("total", 0):.0f}')
    pdf.ln(5)

    # 8. Uyarilar
    warnings = result.get("warnings", [])
    if warnings:
        draw_header('8. UYARILAR VE KISITLAR')
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(200, 50, 50)
        for w in warnings:
            pdf.set_x(10)
            pdf.multi_cell(190, 6, sanitize_text(f"- {w}"))
        pdf.ln(5)

    return bytes(pdf.output(dest='S'))
