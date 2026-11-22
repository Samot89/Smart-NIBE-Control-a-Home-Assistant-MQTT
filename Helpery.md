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

### 🔹 Last write timestamp (EEPROM protection)

`input_datetime.nibe_last_write` – **date and time** must both be enabled

**Purpose:**
The blueprint stores the time of every offset write here and does not write again
until `min_write_interval_minutes` (default 45 min) have passed.

**Important:**
Select this helper in the blueprint input *Helper for last write timestamp*.
Without it the minimum write interval is **not enforced**.

**Exception (comfort override):**
When the indoor temperature is 0.7 °C or more away from the target, a write is allowed
even before the interval has passed.

Create it in *Settings → Devices & services → Helpers → Create helper → Date and/or time*
(choose *Date and time*), or in YAML:

```yaml
input_datetime:
  nibe_last_write:
    name: NIBE last offset write
    has_date: true
    has_time: true
```

---

### 🔹 Weather forecast trend (not needed since v4.8)

`input_number.weather_forecast_trend`

Since v4.8 the blueprint calculates the trend itself from the **hourly forecast of the weather
entity** (`weather.get_forecasts`): average of the next 6 hours minus the current outdoor temperature.
Leave the input *Weather forecast trend helper* empty.

The helper is only a **fallback** for weather entities without an hourly forecast. In that case
it must be kept up to date by an automation (example:
[`Weather - Update forecast values.yaml`](Weather%20-%20Update%20forecast%20values.yaml) – replace
`weather.domov_2` with your weather entity). A helper that is never updated stays at its minimum
(−10) and adds a permanent +1 to the offset. The debug payload shows the used source in
`component_breakdown.7_forecast_bonus.trend_source` (`forecast` / `helper` / `none`).

---

### 🔹 Status text and history (v4.9)

Every run the blueprint publishes a plain-text **status** – what it is doing and why, e.g.
*"Raising offset 0 → 1: house 0.4 °C below target +1.0, cheap electricity (2.0) +0.9"* or
*"Holding at 0 (target 1) – write interval 23/45 min · …"*.

After every write it adds a line to the **history** (`nibe/debug/history`, retained, last 20
entries) and to the logbook of the *Current NIBE offset* entity. The blueprint finds the history
sensor below by its `history_topic` attribute – no need to select it anywhere.

Add both MQTT sensors (see `mqtt.yaml` below: *NIBE Status*, *NIBE Offset History*) and show them
on a dashboard, e.g.:

```yaml
type: markdown
title: Smart NIBE
content: |
  **{{ states('sensor.nibe_status') }}**

  {% for e in state_attr('sensor.nibe_offset_history', 'entries') or [] -%}
  - {{ e }}
  {% endfor %}
```

> Use `content: |` (not `>`) – otherwise YAML folds all history rows into one line.

**Notification after a write (v4.10):** in the blueprint open *🔔 Actions after a write*, add e.g.
a *Notifications* action and use `{{ nibe_message }}` as the message. In YAML:

```yaml
- action: notify.mobile_app_my_phone
  data:
    title: Smart NIBE
    message: "{{ nibe_message }}"
```

Available variables: `nibe_message` (short line / full status / both – chosen in
*💬 Message for the actions below*), `nibe_status`, `nibe_history_line`, `nibe_offset_old`,
`nibe_offset_new`, `nibe_reasons`.

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

  # Only needed as a fallback for weather entities without an hourly forecast (see above)
  weather_forecast_trend:
    name: Weather trend (upcoming hours)
    min: -10
    max: 10
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

    - name: NIBE Status
      unique_id: nibe_status
      state_topic: "nibe/debug/offset_calc"
      value_template: "{{ (value_json.status | default(''))[:255] }}"
      icon: mdi:message-text

    - name: NIBE Offset History
      unique_id: nibe_offset_history
      state_topic: "nibe/debug/history"
      value_template: "{{ (value_json.last | default(''))[:255] }}"
      json_attributes_topic: "nibe/debug/history"
      icon: mdi:history

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
