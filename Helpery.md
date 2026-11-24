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
- Limiting the rate of changes (below −800 the offset moves max. 1 step per write)
- **DM guard** (v4.13, optional) – caps the offset while DM is low, with hysteresis

**When does the immersion heater start?** That is set **in the heat pump itself**, not in the
blueprint – service menu *degree minute settings* (F-series / VVM usually 4.9.3, S-series similar):
- *start compressor*, e.g. −60 DM
- *difference to start of additional heat*, e.g. 400 → the heater starts at about **−460 DM**

Check these first. If the heater starts too early for you, raising the difference (or limiting /
blocking the additional heat except for emergencies) in the pump is the cleanest fix and works
without the blueprint. Use the **DM guard** when you can't or don't want to change the pump
settings: set its threshold a little above the heater start (e.g. −400 for −460) and the release
threshold higher (e.g. −200), so the offset doesn't flip back and forth.

> ℹ️ The blueprint keeps no state between runs, so the hysteresis is taken from the current offset:
> the cap applies when DM is below the threshold, **or** when DM is below the release threshold and
> the offset is already at or below the cap. In practice it means *"don't raise the offset above the
> cap while DM is below the release threshold"* – so the cap can also show up at e.g. DM −250 when the
> offset was already −2 because of price or indoor temperature. That is intended (a bit safer).

---

### 🔹 Spot price sensor and price list

**Spot price sensor** – the current electricity price (state, currency/kWh).

**Price list** – today's (and tomorrow's) prices, used for pre-heating and the **relative spot mode**
(v4.13). The blueprint reads it from the spot price sensor, or from the optional
*📋 Price list sensor*. The format is recognised automatically; 15-minute prices are averaged per hour.

| Integration | Where the prices are | Status |
|---|---|---|
| CZ Energy Spot Prices | timestamp attributes (`2026-11-23T00:00:00+01:00: 4.58`) | ✅ tested (live) |
| Nord Pool – core integration | **no price list** → use the helper sensor below | ✅ tested (real data, SE3) |
| Own template sensor with `today` / `tomorrow` lists | `today`, `tomorrow` | ✅ tested |
| Nord Pool (HACS) | `raw_today` / `today` | 🧪 **testers wanted** |
| ENTSO-e (HACS) | `prices_today` / `prices_tomorrow` | 🧪 **testers wanted** |
| Energi Data Service (HACS) | `raw_today` / `today` | 🧪 **testers wanted** |
| Tibber, Octopus, Amber, … | not built in – a helper sensor with `today` / `tomorrow` lists works | 🧪 **testers wanted** |

> 🧪 **Testers wanted:** the formats marked above were implemented from the integrations' source code,
> not tested on real data. If you use one of them, please check the debug payload
> (`input_sensors.price_list`: `source`, `hours_today` should be 24) and report in
> [issue #5](https://github.com/Samot89/Smart-NIBE-Control-HA-Modbus-MQTT-myUplink/issues/5) – thanks!

#### Price list for the core Nord Pool integration

The core Nord Pool integration only exposes the current / next / min / max price. The full day is
available through the action `nordpool.get_prices_for_date`. This trigger-based template sensor
calls it once an hour (not on every blueprint run) and stores the prices in currency/kWh:

```yaml
template:
  - trigger:
      - trigger: time_pattern
        minutes: 1
      - trigger: homeassistant
        event: start
    action:
      - action: nordpool.get_prices_for_date
        continue_on_error: true
        data:
          config_entry: YOUR_NORD_POOL_CONFIG_ENTRY_ID
          date: "{{ now().date() }}"
        response_variable: np_today
      - action: nordpool.get_prices_for_date
        continue_on_error: true
        data:
          config_entry: YOUR_NORD_POOL_CONFIG_ENTRY_ID
          date: "{{ (now() + timedelta(days=1)).date() }}"
        response_variable: np_tomorrow
    sensor:
      - name: "NIBE price list"
        unique_id: nibe_price_list
        icon: mdi:format-list-numbered
        # number of price slots for today (96 = 15-min prices)
        state: "{{ (np_today.values() | first | default([])) | length if np_today is mapping else 0 }}"
        attributes:
          # Nord Pool returns currency/MWh – converted to currency/kWh like the price sensors
          raw_today: >
            {% set ns = namespace(l=[]) %}
            {% for e in ((np_today.values() | first | default([])) if np_today is mapping else []) %}
              {% set ns.l = ns.l + [{'start': e.start, 'price': (e.price / 1000) | round(5)}] %}
            {% endfor %}
            {{ ns.l }}
          raw_tomorrow: >
            {% set ns = namespace(l=[]) %}
            {% for e in ((np_tomorrow.values() | first | default([])) if np_tomorrow is mapping else []) %}
              {% set ns.l = ns.l + [{'start': e.start, 'price': (e.price / 1000) | round(5)}] %}
            {% endfor %}
            {{ ns.l }}
```

Replace `YOUR_NORD_POOL_CONFIG_ENTRY_ID` – easiest: *Developer tools → Actions →
Nord Pool: Get prices for date*, pick your entry, switch to YAML mode and copy the `config_entry`.
Then select `sensor.nibe_price_list` as *📋 Price list sensor* in the blueprint (the spot price
sensor stays your Nord Pool current price sensor).

**Used for:**
- Spot price influence (absolute or relative)
- Pre-heating logic

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

`nibe_message` is built from the parts you tick in *💬 Message for the actions below* (v4.11,
one line each): short line, full status, offset change, calculated value, reasons, inputs.
Each part is also available on its own: `nibe_history_line`, `nibe_status`, `nibe_offset_old`,
`nibe_offset_new`, `nibe_calculated`, `nibe_reasons`, `nibe_inputs` – e.g. a short message to
the phone and a detailed one to Telegram.

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
