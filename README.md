# Transformatör Ön Tasarım Motoru (Transformer Design Engine)

Bu proje, 3 fazlı dağıtım transformatörleri için elektromanyetik, mekanik, termal ve maliyet parametrelerini eşzamanlı olarak hesaplayan, doğrulayan ve optimize eden bir **Ön Tasarım ve Simülasyon Motorudur**.

Uygulama, hem mühendisler için matematiksel bir altyapı (Python SDK) sunar hem de kullanıcı dostu bir web arayüzü (Streamlit) ile interaktif analiz yapmaya olanak tanır.

## 🌟 Temel Özellikler

- **🧮 Elektromanyetik & Fizik Motoru:**
  - Sargı tasarımı (Bakır / Alüminyum, HV / LV)
  - Çekirdek tasarımı (Silisli Sac, 3 Bacaklı)
  - Empedans, boşta/yükte kayıplar, verim ve gerilim düşümü hesaplamaları.
- **💰 Gerçek Zamanlı Maliyet (LME) ve Ağırlık Analizi:**
  - Güncel veya manuel girilen hammadde (LME) fiyatlarına göre İmalat Maliyeti hesabı.
  - TOC (Total Ownership Cost) ve Ceza Faktörleri (A/B faktörleri) destekli A/B tasarımı testi.
- **📈 Dinamik Termal Simülasyon (Ön Tahmin):**
  - **IEC 60076-7** standardındaki üstel (exponential) sıcaklık geçiş formüllerine dayalı simülasyon.
  - Zamana bağlı 24 saatlik yük (% load) ve ortam sıcaklığı profillerini işleyerek **Üst Yağ (Top-Oil)** ve **Hot-Spot** sıcaklıklarının dinamik hesabını yapar.
  - Zaman kaydırıcısı (slider) ile günün her anı için anlık SVG Isı Haritası görselleştirme.
- **🎨 İnteraktif SVG Şema & Isı Haritası:**
  - Hesaplanan fiziksel boyutlara (çekirdek çapı, et kalınlığı, yalıtım boşlukları) göre gerçekçi dinamik SVG transformatör kesiti.
  - Termal simülasyondan alınan sıcaklık değerlerine göre renk değiştiren termal ısı haritası.
- **🖨️ PDF Mühendislik Raporu:**
  - Tasarım sonuçlarını (boyutlar, verim, kayıplar, kütleler vb.) temiz bir mühendislik dökümanı olarak PDF formatında çıktı alma imkanı.
- **🤖 Parametrik Optimizasyon:**
  - Grid-search yöntemiyle Akı (T), HV ve LV Akım Yoğunluğu (A/mm²) üzerinden en uygun maliyetli TOC değerini veren tasarımı bulma.

---

## 🛠️ Kurulum

Proje **Python 3.12+** ve üzeri sürümlerde çalışacak şekilde tasarlanmıştır.

1. **Bağımlılıkları Yükleyin:**
   Projenin ana bağımlılıklarını kurmak için komut satırından aşağıdaki komutları çalıştırın:
   ```bash
   pip install pydantic Pint pytest pandas streamlit fpdf2
   ```

2. **Geliştirici Modunda Yükleme (Opsiyonel):**
   Projenin kök dizininde `pyproject.toml` mevcuttur. Dilerseniz paketi düzenlenebilir (editable) modda kurabilirsiniz:
   ```bash
   pip install -e .
   ```

---

## 🚀 Nasıl Çalıştırılır?

### 1. Kullanıcı Arayüzü (Web - Streamlit)
Uygulamanın grafiksel arayüzüne erişmek için proje kök dizininde şu komutu çalıştırın:
```bash
python -m streamlit run streamlit_app.py
```
> Komutu çalıştırdıktan sonra tarayıcınızda otomatik olarak açılmazsa, terminalde belirtilen `http://localhost:8501` adresine giderek erişebilirsiniz.

### 2. Arayüz Kullanım Adımları:
1. **Sol Menü:** Sipariş özelliklerini (kVA, Yüksek/Alçak Gerilim, uk%, boşta/yükte kayıplar) ve tasarım limitlerini (Akı Yoğunluğu, Akım Yoğunluğu, İletken Tipi vb.) belirleyin.
2. **Hesapla Butonu:** 🚀 "Hesapla" butonuna basarak mühendislik hesaplamalarını çalıştırın.
3. **Sekmeler (Tabs):** 
   - Geometri ve Elektriksel KPI'ları inceleyin.
   - **Görsel Şema:** Fiziksel kesitleri interaktif olarak inceleyin (fare ile sargıların üzerine gelip tooltip görebilirsiniz).
   - **İmalat Reçetesi:** Ustalar için sarım tur/et kalınlığı bilgilerini ve sac kesim ölçülerini görün.
   - **Dinamik Termal Simülasyon:** İstediğiniz zaman-yük profili üzerinden dinamik termal değişim simülasyonu çalıştırıp SVG animasyonu ve çizgi grafikleri inceleyin.

---

## 📂 Proje Yapısı

```
transformer_design/
├── src/transformer_design/
│   ├── calculations/          # Fizik, elektrik, mekanik ve kayıp hesaplama fonksiyonları
│   ├── models/                # Pydantic tabanlı veri yapıları (girdiler, sonuçlar, termal yapılar)
│   ├── thermal/               # Dinamik termal simülasyon motoru ve profil yönetimi
│   ├── reporting/             # PDF raporlama üreticisi (fpdf2)
│   └── visualization/         # SVG ve Heatmap oluşturma sınıfları
├── tests/                     # pytest klasörü (matematik, termal doğrulama vb.)
├── streamlit_app.py           # Streamlit web arayüzü dosyası
├── pyproject.toml             # Python proje ve paketasyon ayarları
└── README.md                  # Bu dosya
```

---

## ✅ Testleri Çalıştırma

Kodun doğruluğunu ve fizik motorunun regrese (bozulma) olup olmadığını kontrol etmek için tüm test senaryolarını çalıştırabilirsiniz:

```bash
python -m pytest tests/
```
Özellikle dinamik termal simülasyon için yazılan `test_dynamic_thermal_model.py` ve veri doğrulama için `test_thermal_profile_validation.py` senaryoları mevcuttur.

---

## 📜 Lisans & Uyarılar
Bu yazılım bir **Ön Tasarım (Screening)** aracıdır. Elde edilen değerler, transformatör üretim standartlarına (IEC/IEEE) uygun olarak tasarımın yönünü belirlemeye yardımcı olur; ancak profesyonel FEA (Sonlu Elemanlar Analizi) veya CFD hesaplamalarının yerine geçmez. Üretim aşamasından önce muhakkak tam kapsamlı tip testi simülasyonlarıyla doğrulanmalıdır.
