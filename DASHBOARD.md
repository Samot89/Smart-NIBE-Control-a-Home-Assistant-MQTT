# 📊 Smart NIBE Dashboard – Automation Overview

## 🎯 Basic Info
- **Version:** Ultra Adaptive FINAL
- **Trigger:** Every 2 minutes past the hour (time_pattern)
- **Mode:** Single (one run at a time)

---

## 📈 Input Sensors

### 🔌 Main inputs
| Type | Description | Domain |
|------|-------------|--------|
| **Spot Price** | Current electricity price | sensor |
| **Cheap Block** | Cheapest 6h block | sensor |
| **Degree Minutes** | Degree-minutes | sensor |
| **Outdoor Weather** | Outdoor weather | weather |
| **Indoor Temp** | Indoor temperature | sensor |
| **Current Offset** | Current NIBE offset | sensor |
| **HDO** | HDO sensor (optional) | binary_sensor |

### 🎛️ Auxiliary inputs
| Input | Description | Range |
|-------|-------------|-------|
| **Forecast Trend** | Weather forecast trend | input_number |
| **Indoor Bias** | Indoor temperature bias | input_number |
| **Response Gain** | Response amplification | input_number |
| **Target Temp** | Target temperature | 18-24°C (default: 21.5°C) |
| **Max Offset** | Maximum offset | 1-10 (default: 6) |
| **Min Offset** | Minimum offset | -8 to -1 (default: -3) |
| **Min Change** | Minimum change | 1-5 (default: 1) |
| **Look Ahead Hours** | Forecast hours | 1-6 (default: 2) |

---

## 🧮 Calculation Logic

### 1️⃣ LOOK-AHEAD (Pre-heating)
```
If price in 2h > (current price × 1.3) AND current price < 2.5
  → Preheat Bonus: +1.5
Else
  → 0
```

### 2️⃣ WEATHER & SOLAR INFLUENCES

#### ☀️ Solar malus (9:00-15:00)
| Weather state | Adjustment |
|---------------|-----------|
| Sunny | -1.0 |
| Partly cloudy | -0.5 |
| Cloudy+ | 0.0 |

#### 🌧️ Rain bonus
| Weather state | Bonus |
|---------------|-------|
| Heavy rain/hail | +1.0 |
| Light rain/snow | +0.5 |
| Dry | 0.0 |

#### 💧 Humidity bonus
```
If humidity > 80% AND outdoor temperature < 10°C
  → +0.5
```

#### 📉 Forecast bonus
```
Linear adjustment based on trend: (trend × -0.4)
Clamped: -1 to +1
```

---

## ⚙️ Offset Calculation

### Raw calculation:
```
raw_calc = (
    (-0.3 × spot_price) + 1.5
    + equithermal_shift
    + bonus_6h
    + (indoor_correction × gain)
    + preheat_bonus
    + solar_malus
    + rain_bonus
    + humidity_bonus
    + forecast_bonus
)
```

### Equithermal shift:
```
If outdoor temperature < 5°C:
  equithermal = (0 - t_outdoor) / 10
Else:
  equithermal = 0
```

### Indoor correction:
```
diff = t_indoor - (t_target + bias)

If diff >= +0.8°C  → -1.5
If diff >= +0.3°C  → -0.7
If diff <= -0.8°C  → +2.0
If diff <= -0.3°C  → +1.0
Else               → 0
```

### 6h block bonus:
```
If cheap_block is active (cheapest 6h):
  → +1.0
```

---

## 🛡️ Safety Protection

### DM Guard (Degree-minute protection)
```
If degree_minutes < -800:
  max_step = 1  (limit change to ±1)
Else:
  max_step = 2
```

### Clamping (Range limiting)
```
If t_outdoor < -15°C AND raw_calc > 2:
  → offset = 2

Else:
  - Clamp to max_offset and min_offset
  - Round to integer
```

### Final application:
```
diff = calculated_offset - current_offset

If diff >= max_step:
  → offset = current + max_step

If diff <= -2:
  → offset = current - 1

Else:
  → offset = calculated_offset (integer)
```

---

## ✅ Run Conditions

### Must be satisfied:
1. ✓ HDO is either "none" or "on"
2. ✓ All main sensors are available (not "unavailable")
3. ✓ Offset difference >= min_change_limit

---

## 📤 Actions

### 1. MQTT Publish - Offset
- **Topic:** `nibe/modbus/47011/set` (configurable)
- **Payload:** Final offset (integer)

### 2. MQTT Publish - Debug Info
- **Topic:** `nibe/debug/offset_calc`
- **Retain:** true
- **Contents:**
  - Total offset
  - Raw calculation
  - Degree-minutes
  - Calculation components (all bonuses/malusses)
  - Prices (current, in 2h, first 3h)
  - Temperatures (outdoor, indoor, target)
  - Weather (state, humidity, trend)

---

## 📊 Monitoring

### Recommended entities to track:

#### Basic metrics:
- [ ] `sensor.nibe_current_offset` - Current offset
- [ ] `sensor.spot_price` - Electricity price
- [ ] `sensor.degree_minutes` - Degree-minutes
- [ ] `sensor.indoor_temperature` - Indoor temperature
- [ ] `weather.outdoor` - Weather

#### Debug information:
- [ ] `nibe/debug/offset_calc` - Complete debug output (JSON)

#### Control values:
- [ ] `binary_sensor.cheap_6h_block` - Cheap block
- [ ] `input_number.forecast_trend` - Forecast trend
- [ ] `input_number.indoor_bias` - Indoor bias
- [ ] `input_number.response_gain` - Response gain

---

## 🎨 Dashboard Configuration Example

### Lovelace YAML (copy to dashboard):

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # 🏠 Smart NIBE Control
      ### Adaptive heat pump control

  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.nibe_current_offset
        name: Current Offset
        icon: mdi:thermometer-lines
      - type: entity
        entity: sensor.spot_price
        name: Electricity Price
        icon: mdi:currency-eur
      - type: entity
        entity: sensor.degree_minutes
        name: Degree-minutes
        icon: mdi:gauge

  - type: entities
    title: 🌡️ Temperatures
    entities:
      - entity: sensor.indoor_temperature
        name: Indoor
      - entity: weather.outdoor
        name: Outdoor
        attribute: temperature
      - entity: input_number.target_temp
        name: Target

  - type: entities
    title: ⚙️ Settings
    entities:
      - entity: input_number.indoor_bias
        name: Indoor Bias
      - entity: input_number.response_gain
        name: Response Gain
      - entity: input_number.forecast_trend
        name: Forecast Trend

  - type: entities
    title: 📊 Status
    entities:
      - entity: binary_sensor.cheap_6h_block
        name: Cheap 6h block
      - entity: binary_sensor.hdo
        name: HDO signal

  - type: history-graph
    title: 📈 Offset History
    hours_to_show: 24
    entities:
      - entity: sensor.nibe_current_offset

  - type: history-graph
    title: 💰 Electricity Price
    hours_to_show: 24
    entities:
      - entity: sensor.spot_price
```

---

## 🔧 Maintenance & Tuning

### Optimization tips:

1. **Response Gain** (1.0-2.0)
   - Higher value = faster response to indoor temperature
   - Recommended: 1.2

2. **Indoor Bias** (-2.0 to +2.0)
   - Shift of target temperature
   - Use for long-term correction

3. **Look Ahead Hours** (1-6)
   - Longer horizon = more pre-heating when prices rise
   - Recommended: 2

4. **Max/Min Offset**
   - Limit according to system capabilities
   - Default: 4 / -3

### Troubleshooting:

❌ **Offset not changing**
- Check `min_change` – may be set too high
- Verify all sensors are available
- Check HDO signal

❌ **Too frequent changes**
- Increase `min_change` to 2
- Reduce `response_gain`

❌ **Insufficient pre-heating**
- Increase `look_ahead_hours`
- Check price forecast (today_prices attribute)

---

## 📝 Changelog

### Notes
- All calculations rounded to integers
- DM Guard for protection at extreme degree-minutes
- Extended debug info in MQTT
- Look-ahead preheat mechanism

---

## 🔗 References

- **GitHub:** https://github.com/Samot89/Smart-NIBE-Control-a-Home-Assistant-MQTT.git
- **Blueprint:** https://community.home-assistant.io/t/smart-nibe-ultra-adaptive-heat-curve-control-mqtt-spot-prices/975863

---

*Last updated: March 4, 2026*
