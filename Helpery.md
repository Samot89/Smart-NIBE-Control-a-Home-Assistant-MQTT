## 🧩 Helpers used (Home Assistant)

This automation uses several **Home Assistant helpers**
(`input_number` and sensors) that enable
**long-term learning, fine-tuning, and safe operation**.

The helpers are intentionally separated from the automation logic
so that control is:
- transparent
- stable
- easy to tune
- and non-aggressive

---

### 🔹 Indoor bias – long-term house offset
`input_number.indoor_bias`

**Purpose:**
Compensates for the **long-term systematic deviation** in house behavior.

**Why it exists:**
Every house behaves differently.
Some houses are consistently slightly cooler / warmer
than what the equithermal curve would suggest.

Instead of constantly raising or lowering the curve,
the house **gradually "learns" itself**.

**Effect:**
- Positive value → house tends to be cooler → heating output is added
- Negative value → house tends to be warmer → output is reduced

---

### 🔹 Degree-minutes

`sensor.degree_minutes`

**Purpose:**
Protects the heat pump from overload
and from triggering the electric backup heater.

**Why it exists:**
Degree-minutes are a key internal NIBE variable
that expresses the accumulated heat deficit.

By monitoring them, you can:
- Slow the rise in output
- Prevent the value from dropping to −700
- Protect COP and the compressor

**Used in automation for:**
- DM Guard
- Limiting the rate of changes

---

### 🔹 Spot price sensor

**Purpose:**
Provides the current electricity price.

**Requirements:**
- Must have a current price
- Ideally also a `today[]` attribute for look-ahead

**Used for:**
- Cost optimization
- Pre-heating logic
- Economic decisions

---

### 🔹 Cheapest block (e.g. 6 hours)

`sensor.cheapest_6h_block`

**Purpose:**
Binary information that the cheapest part of the day is active.

**Why it exists:**
Enables safe but more significant pre-heating
during known cheap hours.

**Effect:**
- Active → a bonus is added to the offset
- Inactive → no bonus

---

### 🔹 Current heating curve offset

`sensor.current_offset`

**Purpose:**
Shows the actual offset currently set in NIBE.

**Why it exists:**
The automation must always work from reality,
otherwise oscillation and unnecessary writes would occur.

**Used for:**
- Limiting rate of changes
- EEPROM protection
- Regulation stability

---

### 🔹 Optional: HDO / grid blocking

`binary_sensor.hdo`

**Purpose:**
Prevents control during blocked tariff periods.

**Behavior:**
- If set → control only runs when HDO = ON
- If not set → control is always allowed

---

**Recommended configuration:**

```yaml
# configuration.yaml
input_number:
  indoor_bias:
    name: Indoor temperature bias
    min: -1.0
    max: 1.0
    step: 0.05
    unit_of_measurement: "°C"

  indoor_response_gain:
    name: Control response gain
    min: 0.5
    max: 1.5
    step: 0.1

  weather_forecast_trend:
    name: Weather trend (upcoming hours)
    min: -10
    max: 10
    step: 0.1
    unit_of_measurement: "°C"

  weather_forecast_avg_6h:
    name: Forecast avg 6h
    min: -30
    max: 20
    step: 0.1
    unit_of_measurement: "°C"
```

```yaml
# mqtt.yaml
mqtt:
  sensor:
    # ===========================================================================
    # MAIN SENSOR - Contains EVERYTHING in JSON attributes
    # ===========================================================================
    - name: "NIBE Offset Debug"
      unique_id: nibe_offset_debug
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset.final }}"
      unit_of_measurement: "offset"
      icon: mdi:thermometer-lines
      json_attributes_topic: "nibe/debug/offset_calc"
      json_attributes_template: "{{ value_json | tojson }}"

    - name: NIBE Final Offset
      unique_id: nibe_offset_final
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset.final | default(0) }}"
      icon: mdi:target

    - name: NIBE Offset Change
      unique_id: nibe_offset_change
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset.change | default(0) }}"
      icon: mdi:delta

    - name: NIBE Spot Price Influence
      unique_id: nibe_component_spot
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['1_spot_price_influence'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:currency-eur

    - name: NIBE Equithermal Influence
      unique_id: nibe_component_ekvi
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['2_equithermal_shift'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:chart-line

    - name: NIBE Indoor Correction Influence
      unique_id: nibe_component_indoor
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['3_indoor_correction'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:home-thermometer-outline

    - name: NIBE Spot Price
      unique_id: nibe_debug_spot_price
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.spot_price.value | default(0) | round(3) }}"
      unit_of_measurement: "currency/kWh"
      icon: mdi:currency-eur

    - name: NIBE Outdoor Temperature
      unique_id: nibe_outdoor_temp
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.outdoor_temperature.value | default(0) | round(1) }}"
      unit_of_measurement: "°C"
      icon: mdi:thermometer
      device_class: temperature

    - name: NIBE Indoor Temperature
      unique_id: nibe_indoor_temp
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.indoor_temperature.value | default(0) | round(1) }}"
      unit_of_measurement: "°C"
      icon: mdi:home-thermometer
      device_class: temperature

    - name: NIBE Degree Minutes
      unique_id: nibe_degree_minutes
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.degree_minutes.value | default(0) | round(0) }}"
      unit_of_measurement: "°C·min"
      icon: mdi:timer-sand

    - name: NIBE Minutes Since Write
      unique_id: nibe_eeprom_minutes
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.protection_and_limits.eeprom_protection.minutes_since_write | default(0) | round(1) }}"
      unit_of_measurement: "min"
      icon: mdi:timer

    - name: "NIBE 6h Block Bonus"
      unique_id: nibe_bonus_6h
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['4_bonus_6h_block'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:clock-time-six

    - name: "NIBE Preheat Bonus"
      unique_id: nibe_preheat_bonus
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['5_preheat_bonus'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:fire-alert

    - name: "NIBE Solar Malus"
      unique_id: nibe_solar_malus
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['6_solar_malus'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:white-balance-sunny

    - name: "NIBE Forecast Bonus"
      unique_id: nibe_forecast_bonus
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['7_forecast_bonus'].value | default(0) | round(2) }}"
      unit_of_measurement: ""
      icon: mdi:crystal-ball

    - name: "NIBE Debug COP"
      unique_id: nibe_debug_cop_value
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.cop.value }}"
      unit_of_measurement: ""
      icon: mdi:lightning-bolt-circle

    - name: "NIBE Debug COP Quality"
      unique_id: nibe_debug_cop_quality
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.cop.quality }}"
      icon: mdi:star-circle

    - name: "NIBE Debug COP Bonus"
      unique_id: nibe_debug_cop_bonus
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['8_cop_bonus'].value }}"
      unit_of_measurement: ""
      icon: mdi:plus-minus

  number:
    - name: Heat Curve Offset
      unique_id: heat_offset_s1
      min: -6
      max: 6
      step: 1
      state_topic: "nibe/modbus/47011"
      command_topic: "nibe/modbus/47011/set"

    - name: Heat Curve Offset
      unique_id: a220223829
      state_topic: "nibe/modbus/47011"

  binary_sensor:
    - name: NIBE Write Allowed
      unique_id: nibe_write_allowed
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.protection_and_limits.eeprom_protection.write_allowed | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:check-circle

    - name: NIBE DM Alarm
      unique_id: nibe_dm_alarm
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.input_sensors.degree_minutes.alarm | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:alert
      device_class: problem

    - name: NIBE Sensors OK
      unique_id: nibe_check_sensors
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.decision.checks.sensors_available | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:check
      device_class: connectivity

    - name: "NIBE 6h Block Configured"
      unique_id: nibe_6h_configured
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['4_bonus_6h_block'].configured | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:cog

    - name: "NIBE Preheat Active"
      unique_id: nibe_preheat_active
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['5_preheat_bonus'].active | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:fire

    - name: "NIBE Solar Active"
      unique_id: nibe_solar_active
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ value_json.offset_calculation.component_breakdown['6_solar_malus'].active | default(false) }}"
      payload_on: true
      payload_off: false
      icon: mdi:weather-sunny
```
