# Üç Fazlı Dağıtım Transformatörü Matematik ve Ön Tasarım Kütüphanesi

Bu kütüphane, üç fazlı dağıtım transformatörlerinin elektromanyetik ön tasarımı ve hesaplamaları için geliştirilmiş bağımsız, modüler ve matematiksel doğruluğa önem veren bir Python paketidir. 

## Özellikler

- **Saf Fonksiyonlar:** Tüm hesaplamalar girdi olarak fiziksel birim (Pint Quantity) alır ve yan etkisiz saf fonksiyonlarla çıktı üretir.
- **Güçlü Tip Denetimi:** `pydantic` kullanılarak veri modelleri doğrulanır, `mypy` ile statik analiz desteklenir.
- **Genişletilebilirlik:** Bağlantı grubu ayrıştırması, tur hesaplamaları, iletken boyutlandırma, kısa devre, empedans ve verim hesapları birbirinden tamamen bağımsızdır.

## Kurulum

Projeyi klonladıktan sonra aşağıdaki komutla kurabilirsiniz:

```bash
pip install -e .
```

Geliştirme bağımlılıkları (pytest, ruff, mypy vb.) ile kurmak için:

```bash
pip install -e .[dev]
```

## Kullanım Örneği

```python
from transformer_design.units import Q_
from transformer_design.calculations.electrical import calculate_rated_currents

s_rated = Q_(1000, 'kVA')
v_hv = Q_(33000, 'V')
v_lv = Q_(400, 'V')

currents = calculate_rated_currents(s_rated, v_hv, v_lv)
print(f"HV Hat Akımı: {currents['i_hv_line'].to('A'):.2f}")
print(f"LV Hat Akımı: {currents['i_lv_line'].to('A'):.2f}")
```
