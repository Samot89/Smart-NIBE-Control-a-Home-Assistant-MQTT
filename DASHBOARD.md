# 📊 Smart NIBE Dashboard – Přehled Automatizace

## 🎯 Základní Info
- **Verze:** Ultra Adaptive FINAL 
- **Spouštěč:** Každé 2 minuty po celé hodině (time_pattern)
- **Režim:** Single (jeden běh najednou)

---

## 📈 Vstupní Senzory

### 🔌 Hlavní vstupy
| Typ | Popis | Doména |
|-----|-------|--------|
| **Spot Price** | Aktuální cena elektřiny | sensor |
| **Cheap Block** | Nejlevnější 6h blok | sensor |
| **Degree Minutes** | Stupňominuty | sensor |
| **Outdoor Weather** | Venkovní počasí | weather |
| **Indoor Temp** | Vnitřní teplota | sensor |
| **Current Offset** | Aktuální NIBE offset | sensor |
| **HDO** | HDO senzor (volitelné) | binary_sensor |

### 🎛️ Pomocné vstupy
| Vstup | Popis | Rozsah |
|-------|-------|--------|
| **Forecast Trend** | Trend předpovědi počasí | input_number |
| **Indoor Bias** | Bias vnitřní teploty | input_number |
| **Response Gain** | Zesílení odezvy | input_number |
| **Target Temp** | Cílová teplota | 18-24°C (default: 21.5°C) |
| **Max Offset** | Maximální offset | 1-10 (default: 6) |
| **Min Offset** | Minimální offset | -8 až -1 (default: -3) |
| **Min Change** | Minimální změna | 1-5 (default: 1) |
| **Look Ahead Hours** | Hodiny předpovědi | 1-6 (default: 2) |

---

## 🧮 Výpočetní Logika

### 1️⃣ LOOK-AHEAD (Předtopení)
```
Pokud cena za 2h > (aktuální cena × 1.3) AND aktuální cena < 2.5 CZK
  → Preheat Bonus: +1.5
Jinak
  → 0
```

### 2️⃣ POČASÍ & SOLÁRNÍ VLIVY

#### ☀️ Solární malus (9:00-15:00)
| Stav počasí | Úprava |
|-------------|--------|
| Slunečno | -1.0 |
| Polojasno | -0.5 |
| Oblačno+ | 0.0 |

#### 🌧️ Dešťový bonus
| Stav počasí | Bonus |
|-------------|-------|
| Silný déšť/krupobití | +1.0 |
| Lehký déšť/sníh | +0.5 |
| Sucho | 0.0 |

#### 💧 Vlhkostní bonus
```
Pokud vlhkost > 80% AND venkovní teplota < 10°C
  → +0.5
```

#### 📉 Forecast bonus
```
Linearní úprava podle trendu: (trend × -0.4)
Omezeno: -1 až +1
```

---

## ⚙️ Výpočet Offsetu

### Surový výpočet:
```
raw_calc = (
    (-0.8 × spot_cena) + 4.0
    + ekviterm_posun
    + bonus_6h
    + (indoor_korekce × gain)
    + preheat_bonus
    + solar_malus
    + rain_bonus
    + humidity_bonus
    + forecast_bonus
)
```

### Ekviterm posun:
```
Pokud venkovní teplota < 5°C:
  ekviterm = (0 - t_venkovní) / 10
Jinak:
  ekviterm = 0
```

### Vnitřní korekce:
```
rozdíl = t_vnitřní - (t_cílová + bias)

Pokud rozdíl >= +0.8°C  → -1.5
Pokud rozdíl >= +0.3°C  → -0.7
Pokud rozdíl <= -0.8°C  → +2.0
Pokud rozdíl <= -0.3°C  → +1.0
Jinak                   → 0
```

### Bonus 6h blok:
```
Pokud je aktivní cheap_block (nejlevnější 6h):
  → +1.0
```

---

## 🛡️ Bezpečnostní Ochrana

### DM Guard (Ochrana stupňominut)
```
Pokud degree_minutes < -800:
  max_step = 1  (omez změnu na ±1)
Jinak:
  max_step = 2
```

### Clamping (Omezení rozsahu)
```
Pokud t_venkovní < -15°C AND raw_calc > 2:
  → offset = 2

Jinak:
  - Omez na max_offset až min_offset
  - Zaokrouhli na celé číslo
```

### Finální aplikace:
```
rozdíl = vypočtený_offset - aktuální_offset

Pokud rozdíl >= max_step:
  → offset = aktuální + max_step

Pokud rozdíl <= -2:
  → offset = aktuální - 1

Jinak:
  → offset = vypočtený_offset (celé číslo)
```

---

## ✅ Podmínky Spuštění

### Musí být splněno:
1. ✓ HDO je buď "none" nebo "on"
2. ✓ Všechny hlavní senzory jsou dostupné (ne "unavailable")
3. ✓ Rozdíl offsetů >= min_change_limit

---

## 📤 Akce

### 1. MQTT Publish - Offset
- **Topic:** `nibe/modbus/47011/set` (konfigurovatelné)
- **Payload:** Finální offset (celé číslo)

### 2. MQTT Publish - Debug Info
- **Topic:** `nibe/debug/offset_calc`
- **Retain:** true
- **Obsah:**
  - Celkový offset
  - Surový výpočet
  - Stupňominuty
  - Složky výpočtu (všechny bonusy/malusy)
  - Ceny (aktuální, za 2h, první 3h)
  - Teploty (venkovní, vnitřní, cílová)
  - Počasí (stav, vlhkost, trend)

---

## 📊 Monitorování

### Doporučené entity k sledování:

#### Základní metriky:
- [ ] `sensor.nibe_current_offset` - Aktuální offset
- [ ] `sensor.spot_price` - Cena elektřiny
- [ ] `sensor.degree_minutes` - Stupňominuty
- [ ] `sensor.indoor_temperature` - Vnitřní teplota
- [ ] `weather.outdoor` - Počasí

#### Debug informace:
- [ ] `nibe/debug/offset_calc` - Kompletní debug výstup (JSON)

#### Kontrolní hodnoty:
- [ ] `binary_sensor.cheap_6h_block` - Levný blok
- [ ] `input_number.forecast_trend` - Trend předpovědi
- [ ] `input_number.indoor_bias` - Vnitřní bias
- [ ] `input_number.response_gain` - Zesílení odezvy

---

## 🎨 Příklad Dashboard Konfigurace

### Lovelace YAML (kopíruj do dashboardu):

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # 🏠 Smart NIBE Control
      ### Adaptivní řízení tepelného čerpadla
  
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.nibe_current_offset
        name: Aktuální Offset
        icon: mdi:thermometer-lines
      - type: entity
        entity: sensor.spot_price
        name: Cena Elektřiny
        icon: mdi:currency-eur
      - type: entity
        entity: sensor.degree_minutes
        name: Stupňominuty
        icon: mdi:gauge
  
  - type: entities
    title: 🌡️ Teploty
    entities:
      - entity: sensor.indoor_temperature
        name: Vnitřní
      - entity: weather.outdoor
        name: Venkovní
        attribute: temperature
      - entity: input_number.target_temp
        name: Cílová
  
  - type: entities
    title: ⚙️ Nastavení
    entities:
      - entity: input_number.indoor_bias
        name: Indoor Bias
      - entity: input_number.response_gain
        name: Response Gain
      - entity: input_number.forecast_trend
        name: Forecast Trend
  
  - type: entities
    title: 📊 Stav
    entities:
      - entity: binary_sensor.cheap_6h_block
        name: Levný 6h blok
      - entity: binary_sensor.hdo
        name: HDO signál
  
  - type: history-graph
    title: 📈 Historie Offsetu
    hours_to_show: 24
    entities:
      - entity: sensor.nibe_current_offset
  
  - type: history-graph
    title: 💰 Cena Elektřiny
    hours_to_show: 24
    entities:
      - entity: sensor.spot_price
```

---

## 🔧 Údržba & Ladění

### Tipy pro optimalizaci:

1. **Response Gain** (1.0-2.0)
   - Vyšší hodnota = rychlejší reakce na vnitřní teplotu
   - Doporučeno: 1.2

2. **Indoor Bias** (-2.0 až +2.0)
   - Posun cílové teploty
   - Použij pro dlouhodobou korekci

3. **Look Ahead Hours** (1-6)
   - Delší horizont = větší předtopení při růstu cen
   - Doporučeno: 2

4. **Max/Min Offset**
   - Omez podle možností systému
   - Default: 4 / -3

### Řešení problémů:

❌ **Offset se nemění**
- Zkontroluj `min_change` - možná je příliš velké
- Ověř dostupnost všech senzorů
- Zkontroluj HDO signál

❌ **Příliš časté změny**
- Zvyš `min_change` na 2
- Snižuj `response_gain`

❌ **Nedostatečné předtopení**
- Zvyš `look_ahead_hours`
- Zkontroluj předpověď cen (today_prices atribut)

---

## 📝 Changelog

### 
- Všechny výpočty zaokrouhleny na celá čísla
- DM Guard pro ochranu při extrémních stupňominutách
- Rozšířené debug info v MQTT
- Look-ahead preheat mechanismus

---

## 🔗 Reference

- **GitHub:** https://github.com/Samot89/Smart-NIBE-Control-a-Home-Assistant-MQTT.git
- **Blueprint:** https://community.home-assistant.io/t/smart-nibe-ultra-adaptive-heat-curve-control-mqtt-spot-prices/975863

---

*Poslední aktualizace: 22. ledna 2026*


