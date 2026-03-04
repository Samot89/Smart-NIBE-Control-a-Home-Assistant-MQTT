# 🏠 Smart NIBE Control – Adaptive Heat Pump Control

[![Version](https://img.shields.io/badge/version-v4.4-blue)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/Home%20Assistant-Blueprint-41BDF5?logo=homeassistant)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An intelligent Home Assistant blueprint that adaptively controls a NIBE heat pump by adjusting the equithermal curve (Modbus register 47011). The system **does not toggle the compressor** — it smoothly optimizes thermal output based on 8 independent factors.

---

## ✨ What the system does

| Component | Description |
|-----------|-------------|
| 🌡️ **Equithermal** | Base calculation from outdoor temperature |
| ⚡ **Spot prices** | Increases heating when electricity is cheap, reduces when expensive |
| 🏠 **Indoor temperature** | Corrects offset based on deviation from target temperature |
| ☀️ **Solar braking** | Limits heating between 9–15 h on sunny days |
| 🔮 **Pre-heating** | Warms the house 1–8 h before electricity prices rise |
| 📊 **Degree-minutes** | Protects the compressor and prevents bivalence activation |
| 🌤️ **Forecast bonus** | Responds to weather forecast (cooling/warming trend) |
| 🔧 **Smooth change** | Limits offset jump to ±1 per hour |

---

## 🧮 How it calculates

The resulting offset is the sum of all components:

```
offset = spot_influence + equithermal_influence + indoor_influence × gain
       + bonus_6h_block + preheat_bonus − solar_malus
       + forecast_bonus + cop_bonus
```

### Spot price influence (v4.4)
```
spot_influence = (−0.3 × price [currency/kWh]) + 1.5
```

| Electricity price | Offset influence |
|------------------|-----------------|
| 2 units/kWh | **+0.9** (slightly increases heating) |
| 5 units/kWh | **0.0** (neutral) |
| 10 units/kWh | **−1.5** (slightly reduces) |

> 💡 **v4.4:** The spot price influence was intentionally reduced 3× (previously coefficient −0.8/+4.0). The system now prioritizes indoor comfort over aggressive price optimization.

### Indoor temperature correction
```
temp_diff = indoor_temperature − (target_temperature + indoor_bias)
```
Correction is non-linear (±0.3, ±0.7, ±1.5) and multiplied by `indoor_response_gain`.

---

## 📋 Requirements

- **NIBE heat pump** (S-series, F-series with VVM 320/500)
- **Home Assistant** 2024.1+
- **MQTT broker** (Mosquitto)
- **nibepi bridge** or equivalent for Modbus–MQTT
- **Spot prices** – integration e.g. Nordpool / Amber Electric
- **Outdoor temperature** – sensor or weather integration
- **Indoor temperature** – sensor in the living space

---

## 🚀 Installation

### 1. Import the blueprint
```
Settings → Automations → Blueprints → Import Blueprint
```
Enter the URL of this repository or upload the `smart_nibe_control.yaml` file manually.

### 2. Create helpers (input_number)

| Helper | Min | Max | Step | Recommended value |
|--------|-----|-----|------|-------------------|
| `input_number.indoor_bias` | −1.0 | 1.0 | 0.1 | **0.0** |
| `input_number.indoor_response_gain` | 0.5 | 1.5 | 0.1 | **1.5** |
| `input_number.weather_forecast_trend` | −10 | 10 | 0.1 | *(auto)* |
| `input_number.weather_forecast_avg_6h` | −30 | 20 | 0.1 | *(auto)* |

> ⚠️ `indoor_bias = 0.0` ensures the effective target temperature matches the value set in the thermostat. Negative values cause the system to react later.

### 3. Configure the automation
Create a new automation from the blueprint and assign entities:
- Outdoor temperature sensor
- Indoor temperature sensor
- Target temperature sensor
- Electricity spot price sensor
- NIBE degree-minutes sensor
- Heat curve number entity (e.g. `number.heat_offset_s1`)

### 4. Optional: Dashboard
Import ready-made cards from [DASHBOARD.md](DASHBOARD.md).

---

## ⚙️ Key parameters

| Parameter | Description | Recommendation |
|-----------|-------------|----------------|
| `indoor_bias` | Systematic correction of target temperature | 0.0 (no correction) |
| `indoor_response_gain` | Sensitivity of indoor temperature correction | 1.5 (max) |
| `offset_min` / `offset_max` | Range of the resulting offset | −3 / +3 |
| `step_limit` | Max offset change per hour | 1.0 |
| `dm_threshold` | Degree-minute protection threshold | −400 |

---

## 📊 MQTT sensors (debug)

The blueprint automatically publishes diagnostics:

```yaml
sensor.nibe_offset_debug          # JSON with breakdown of all components
sensor.nibe_spot_price_influence  # Spot price component
sensor.nibe_indoor_correction     # Indoor temperature component
sensor.nibe_equithermal_influence # Equithermal component
sensor.nibe_final_offset          # Resulting offset before write
sensor.last_nibe_offset           # Last written offset
```

---

## 🖼️ Screenshots

![Dashboard overview](Screenshot_1.png)
![Offset detail](Screenshot_2.png)

---

## 📝 Changelog

### v4.4 (2026-03-02)
- **Spot price influence reduced 3×**: coefficient −0.8 → −0.3, offset +4.0 → +1.5
- Indoor temperature now dominates control
- Recommendation: `indoor_bias = 0.0`, `indoor_response_gain = 1.5`

### v4.3
- Added COP bonus (±0.8 based on compressor efficiency)
- Improved forecast bonus

### v4.0–v4.2
- Equithermal calculation, solar braking, 6h cheap electricity block

Full changelog → [CHANGELOG.md](CHANGELOG.md)

---

## 🤝 Acknowledgements

- [NIBE](https://www.nibe.eu/) – heat pump manufacturer
- [nibepi](https://github.com/anerdins/nibepi) – Modbus bridge
- [Home Assistant](https://www.home-assistant.io/) community

---

## 📄 License

MIT © [Samot89](https://github.com/Samot89)
