# Transformer Design Engine

Üç fazlı, üç bacaklı dağıtım transformatörleri için elektromanyetik, geometrik, termal, mekanik ve maliyet hesaplarını tek bir doğrulanmış akışta birleştiren ön tasarım motoru.

Proje iki kullanım biçimi sunar:

- Python API ve CLI ile tekrarlanabilir mühendislik hesapları
- Streamlit ile modern, etkileşimli tasarım ve karşılaştırma arayüzü

> [!IMPORTANT]
> Bu yazılım bir **ön tasarım ve seçenek tarama aracıdır**. IEC uygunluk belgesi, ayrıntılı üretim tasarımı, FEA/CFD, kısa devre dayanım doğrulaması veya tip testi yerine geçmez.

## Öne çıkan yetenekler

- Pydantic tabanlı fiziksel girdi doğrulaması
- Dyn11, Yyn0 ve Dd0 bağlantıları için hat/faz dönüşümleri
- Tur başına gerilim, çekirdek kesiti, akı yoğunluğu ve tur sayısı hesabı
- HV yuvarlak tel ve LV folyo için kesit ve sarım reçetesi
- Verim, kısa devre akımı ve Rogowski katsayılı yaklaşık kaçak empedans
- Yaklaşık radyal/eksenel kuvvet, dielektrik açıklık ve akustik tarama
- Tank/radyatör alanı, hot-spot ve 24 saatlik dinamik termal profil
- Üst yağ/hot-spot grafiği, sıcaklığa bağlı SVG ısı haritası ve yaşlanma katsayısı
- Deterministik malzeme fiyatlarıyla ağırlık, imalat maliyeti ve TOC
- Akı yoğunluğu ve akım yoğunluğu üzerinde parametrik grid-search optimizasyonu
- PDF ön tasarım raporu, imalat tabloları ve son 10 tasarım için A/B karşılaştırması
- GitHub Actions üzerinde test ve temel statik analiz

## Kurulum

Python 3.12 veya üzeri gereklidir.

Yalnızca hesap motoru:

```bash
python -m pip install -e .
```

Web arayüzü ve PDF raporu dahil:

```bash
python -m pip install -e ".[ui]"
```

Geliştirme araçlarıyla birlikte:

```bash
python -m pip install -e ".[ui,dev]"
```

## Çalıştırma

### Web arayüzü

```bash
python -m streamlit run streamlit_app.py
```

Arayüzde sol panelden sipariş, aktif kısım, termal ve maliyet girdileri belirlenir. **Tasarımı hesapla** tek bir tasarımı çözer; **Parametrik optimize et** ise tanımlı akı ve akım yoğunluğu adaylarını TOC'ye göre tarar.

Dinamik termal sekmesindeki 24 saatlik yük ve ortam tablosu düzenlenebilir. Simülasyon sonunda:

- ortam, üst yağ ve hot-spot sıcaklık eğrileri,
- seçilen saate ait termal SVG kesiti,
- tepe sıcaklıklar ve eşdeğer yaşlanma toplamı

görüntülenir.

### Komut satırı

Paket kurulduktan sonra:

```bash
transformer-design
```

veya doğrudan:

```bash
python cli_app.py
```

### Python API

```python
from transformer_design.calculations.engine import synthesize_transformer

# OrderInput örneği için example_usage.py dosyasına bakın.
result = synthesize_transformer(inputs)

print(result["total_weight"])
print(result["toc_usd"])
print(result["warnings"])
```

`synthesize_transformer` web arayüzü, CLI ve optimizasyon için tek hesaplama kaynağıdır. Malzeme fiyatları verilmezse deterministik varsayılanlar kullanılır; motor kendi içinde internetten fiyat çekmez.

## Dinamik termal model

`simulate_dynamic_thermal`, IEC 60076-7 yaklaşımından esinlenen birinci dereceden üstel geçiş modeli uygular. Her zaman aralığında nihai üst yağ artışı aşağıdaki oranla taranır:

$$
\Delta\theta_{o,u}=\Delta\theta_{o,r}
\left(\frac{K^2R+1}{R+1}\right)^x
$$

Sargı hot-spot gradyanı ise yükle birlikte yaklaşık olarak $K^{2y}$ oranında değişir. Yağ ve sargı sıcaklıkları ayrı zaman sabitleriyle nihai değerlere yaklaşır.

Model; karşılaştırma, yük profili inceleme ve erken risk tespiti içindir. Üreticiye özgü yağ akışı, sargı geometrisi, soğutma donanımı ve deney verileri girilmeden standart uygunluğu iddia etmez.

## Tasarım sağlık kontrolleri

Motor her çözümde dört açık tarama sonucu üretir:

| Kontrol | Varsayılan tarama ölçütü |
|---|---|
| Akı yoğunluğu | Gerçek değer ≤ 1,75 T |
| Amper-sarım dengesi | Bağıl fark ≤ %2 |
| Kaçak empedans | Hedefin ±max(0,5 puan, %15) aralığı |
| Hot-spot | Kullanıcının sıcaklık sınırının altında |

Bu eşikler üretim kabul kriteri değil, erken tasarım uyarılarıdır.

## Test ve kalite

```bash
python -m pytest
python -m ruff check src tests cli_app.py example_usage.py streamlit_app.py
```

Testler elektriksel dönüşümleri, çekirdek/sargı fonksiyonlarını, girdi doğrulamasını, ortak motoru, optimizasyon aday sayısını ve dinamik termal geçişleri kapsar.

## Proje yapısı

```text
.
├── .github/workflows/quality.yml
├── src/transformer_design/
│   ├── calculations/       # Saf hesap fonksiyonları ve ortak engine
│   ├── models/             # Doğrulanmış sipariş/kabul modelleri
│   ├── reporting/          # PDF ve SVG üretimi
│   ├── validation/         # Tasarım durum değerlendirmesi
│   └── cli.py              # Kurulabilir CLI
├── tests/
├── streamlit_app.py
├── example_usage.py
└── pyproject.toml
```

## Bilinen sınırlar

- Üç fazlı ve üç bacaklı dağıtım transformatörleriyle sınırlıdır.
- Geometri, kaçak empedans, kuvvet, akustik ve dielektrik hesapları tarama seviyesinde ampirik yaklaşımlar içerir.
- Malzeme fiyatları kullanıcı girdisidir; LME verisi olarak doğrulanmaz.
- Sac kalitesi eğrileri, harmonikler, girdap/stray kayıpları, detaylı yalıtım koordinasyonu ve üretici toleransları henüz modellenmemiştir.
- “Uygun” sonucu üretime hazır anlamına gelmez.

## Lisans

[MIT](LICENSE)
