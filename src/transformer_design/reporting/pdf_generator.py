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
        # Ust Baslik
        self.set_font('helvetica', 'B', 22)
        self.set_text_color(44, 75, 100) # Dark Blue
        self.cell(0, 12, 'TRANSFORMATOR TASARIM RAPORU', border=False, align='C', ln=True)
        
        # Alt Baslik
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, 'TEKNIK SARTNAME VE SIPARIS FORMU / URETIM FOYU', border=False, align='C', ln=True)
        
        # Yesil cizgi
        self.set_draw_color(46, 160, 67) # Green
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
        self.set_line_width(0.2)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, sanitize_text(f'Sayfa {self.page_no()} / {{nb}} - Uretim Tarihi: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}'), align='C')

def generate_engineering_pdf(data: dict, output_path: str = "rapor.pdf") -> str:
    pdf = TransformerReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Genislikler (toplam 190mm)
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
        pdf.set_text_color(200, 50, 50) # Red
        pdf.cell(col_w[1], row_h, sanitize_text(str(val1)), border=1, align='L')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(col_w[2], row_h, sanitize_text(label2), border=1, fill=True, align='L')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(200, 50, 50) # Red
        pdf.cell(col_w[3], row_h, sanitize_text(str(val2)), border=1, align='L')
        pdf.ln(row_h)

    # 1. TABLO
    draw_header('GENEL VE ELEKTRIKSEL BILGILER')
    draw_row('Kalite', 'IEC 60076 / TSE', 'Uygulama', 'Dagitim Transformatoru')
    draw_row('Guc Degeri (kVA)', f'{data["s_rated_kva"]:g}', 'Faz Sayisi', '3 Fazli')
    draw_row('Primer Gerilimi (V)', f'{data["v_hv"]:g}', 'Sekonder Gerilimi (V)', f'{data["v_lv"]:g}')
    draw_row('Frekans (Hz)', '50', 'Sargi Turu', 'Standart')
    draw_row('Baglanti Grubu', 'Dyn11', 'Kademe', '+/- 2x2.5%')
    draw_row('Primer Akimi (A)', f'{data.get("i_hv", 0):.2f}', 'Sekonder Akimi (A)', f'{data.get("i_lv", 0):.2f}')
    pdf.ln(5)
    
    # 2. TABLO
    draw_header('YAPI VE TASARIM PARAMETRELERI')
    draw_row('Sargi Malzemesi', f'{data["hv_mat"]} / {data["lv_mat"]}', 'Kademe Degistirici', 'Yuksuz')
    draw_row('Sogutma', 'ONAN', 'Empedans (% @75C)', f'{data["uk_percent"]}')
    draw_row('Izolasyon Yagi Tipi', data["oil_type"], 'Izolasyon Sinifi', 'A Sinifi')
    draw_row('Koruma Derecesi (IP)', 'IP00', 'Ortam Sicakligi (C)', '40')
    draw_row('Sertifikasyon', 'TSE', 'Yuzey Rengi (RAL)', 'RAL 7033')
    pdf.ln(5)
    
    # 3. TABLO
    draw_header('CEKIRDEK VE SARGI DETAYLARI')
    draw_row('Hedef Aki Yogunlugu', f'{data.get("target_flux_T", 0):.2f} T', 'Cekirdek Capi (mm)', f'{data.get("core_d_mm", 0):.1f}')
    draw_row('Brut Cekirdek Alani', f'{data.get("core_a_cm2", 0):.1f} cm2', 'Cekirdek Sac Tipi', 'Silisli Sac (M5 / M4)')
    draw_row('HV Sarim Sayisi', f'{data.get("hv_turns", 0)}', 'HV Akim Yogunlugu', f'{data.get("hv_j", 0):.2f} A/mm2')
    draw_row('LV Sarim Sayisi', f'{data.get("lv_turns", 0)}', 'LV Akim Yogunlugu', f'{data.get("lv_j", 0):.2f} A/mm2')
    draw_row('Maks. Kisa Devre Gucu', f'{data.get("f_radial", 0):.2f} kN', 'Min. HV Faz-Faz', f'{data.get("clearance", 0):.1f} mm')
    pdf.ln(5)
    
    # 4. TABLO
    draw_header('TERMAL ANALIZ VE AGIRLIKLAR')
    draw_row('Radyator Dilim Sayisi', f'{data.get("rad_fins", 0)} Adet', 'Yag Hacmi (Litre)', f'{data.get("oil_volume", 0):,.0f} L')
    draw_row('Sargi En Sicak Nokta', f'{data.get("hot_spot_rise", 0):.1f} K', 'Tank Isinma Sinifi', 'ONAN Standart')
    draw_row('Aktif Kisim Agirligi', f'{data.get("weight_active", 0):,.1f} kg', 'Tank + Diger Aksam', f'{data.get("weight_tank", 0):,.1f} kg')
    draw_row('Izolasyon Yagi Agirligi', f'{data.get("weight_oil", 0):,.1f} kg', 'Toplam Nakliye Agirligi', f'{data.get("weight_total", 0):,.1f} kg')
    pdf.ln(5)
    
    # 5. TABLO
    draw_header('KAYIPLAR VE MALIYET RAPORU')
    draw_row('Bosta (Demir) Kaybi', f'{data["p_no_load_w"]:g} W', 'Yukte (Bakir) Kaybi', f'{data["p_load_w"]:g} W')
    draw_row('Tam Yukte Verim', f'% {data.get("eff", 0)*100:.2f}', 'Kisa Devre Isi Limiti', 'Gecildi')
    draw_row('Tahmini Fabrika Maliyeti', f'$ {data.get("cost_total", 0):,.2f}', 'TOC (20 Yil Isletme)', f'$ {data.get("toc_total", 0):,.2f}')
    pdf.ln(8)
    
    # NOTLAR / TASARIM KRITERLERI
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(44, 75, 100)
    pdf.cell(190, 8, 'Ek Notlar / Uretim Direktifleri:', ln=True)
    
    # Kesik Cizgili Kutu Hissi
    box_x = pdf.get_x()
    box_y = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(250, 250, 250)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(180, 50, 0) # Darker Orange/Red
    
    notes = [
        "- Bu rapor Antigravity Muh. Motoru tarafindan uretilmistir.",
        "- Radyator tasariminda 1 dilim = 0.32 m2 (800mm x 200mm) olarak kabul edilmistir.",
        "- TOC hesaplamalari girilen A ve B cezai faktorlerine gore yapilmistir.",
        "- Cekirdek kesim olculeri (Step-Lap) arayuz Imalat sekmesinden alinmalidir.",
        "- Imalat esnasinda %5 tolere edilebilir hata payi mevcuttur."
    ]
    
    pdf.rect(box_x, box_y, 190, len(notes) * 6 + 6)
    pdf.set_xy(box_x + 5, box_y + 3)
    for note in notes:
        pdf.cell(180, 6, sanitize_text(note), ln=True)
        pdf.set_x(box_x + 5)
        
    pdf.output(output_path)
    return output_path
