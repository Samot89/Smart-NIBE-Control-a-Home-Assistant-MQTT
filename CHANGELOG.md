# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v4.10] – 2026-11-22

### Added
- **Actions after a write** (optional, #10): run any notify service, Telegram message or script
  after every offset write. Choose the message (short line, full status or both) and use
  `{{ nibe_message }}`, `{{ nibe_status }}`, `{{ nibe_history_line }}`, `{{ nibe_offset_old }}`,
  `{{ nibe_offset_new }}` and `{{ nibe_reasons }}` in your actions.

### Fixed
- Helpery.md: the history dashboard card used `content: >`, which folded all rows into one line.
  Now `content: |` (#9).

---

## [v4.9.2] – 2026-11-22

### Changed
- Repository renamed to **Smart-NIBE-Control-HA-Modbus-MQTT-myUplink** (old links redirect).
- Blueprint renamed to *Smart NIBE – Adaptive Heat Curve Control (MQTT/Modbus or myUplink)* with
  an up-to-date description (it still showed the v4.4 notes).
- README: both write methods (MQTT/Modbus and NIBE/myUplink) described up front; MQTT broker is
  optional with myUplink.

### Fixed
- Without an MQTT integration (myUplink-only setups) the debug publish failed and stopped the
  automation before the offset was written. Debug and history publishes now continue on error.

---

## [v4.9.1] – 2026-11-22

### Fixed
- With cloud integrations (myUplink) the new offset shows up with a delay. Right after a write the
  status said *"Holding at -2 (target -3)"* although -3 had already been written. For 15 minutes
  after a write the blueprint now recognises the offset as "not confirmed yet": the status says
  *"Offset -3 written 2 min ago – waiting for NIBE to report it"* and the same value is not
  written again. Uses the history sensor (needs `mqtt_history_topic` + the *NIBE Offset History*
  sensor). (#9)
- MQTT debug: `decision.write_pending`; the history payload stores `last_offset` and `last_write`.

---

## [v4.9] – 2026-11-21

### Added
- **Plain-text status** in the debug payload (`status`): what the blueprint is doing and why –
  direction (raising / lowering / holding), what blocks a write (HDO, dead band, write interval,
  unavailable offset) and the up to 3 strongest components. New MQTT sensor *NIBE Status*. (#9)
- **Offset history**: after every write a line (time, old → new offset, reasons) is published to
  `mqtt_history_topic` (default `nibe/debug/history`, retained, last 20 entries) and logged to the
  logbook of the *Current NIBE offset* entity. New MQTT sensor *NIBE Offset History* and a
  markdown card example in Helpery.md. (#7)
- MQTT debug: `decision.will_write`, `decision.blocked_by`.

### Changed
- The logbook entry is written only when the offset is actually written (previously every run,
  i.e. every 2 minutes).

---

## [v4.8] – 2026-11-20

### Changed
- The weather forecast trend is now calculated by the blueprint from the hourly forecast of the
  selected weather entity (`weather.get_forecasts`, average of the next 6 hours − current outdoor
  temperature). The *Weather forecast trend* helper is now optional and only used as a fallback
  when the weather entity has no hourly forecast. (#8)
- MQTT debug: `component_breakdown.7_forecast_bonus.trend_source` (`forecast` / `helper` / `none`).

### Fixed
- A forecast trend helper that was never updated (stuck at its minimum −10) added a permanent
  +1 to the offset. With the built-in calculation this can no longer happen. (#8)

---

## [v4.7] – 2026-11-20

### Added
- `offset_write_method`: write the offset via MQTT (default, unchanged) or directly to the
  *Current NIBE offset* entity with `number.set_value` / `input_number.set_value` – works with
  the NIBE and myUplink integrations without NibePi. (#6)
- `comfort_override_delta`: configurable threshold for the comfort override that bypasses the
  minimum write interval (default 0.7 °C as before, 0 = off). (#6)
- MQTT debug: `eeprom_protection.interval_ok`, `comfort_override`, `comfort_override_delta`,
  `decision.write_method`, `decision.checks.current_offset_available`.

### Fixed
- No write when the *Current NIBE offset* entity is unavailable / unknown (e.g. myUplink after
  a write). Previously it was read as 0, which caused unnecessary writes. (#6)

---

## [v4.6] – 2026-11-19

### Added
- `target_temp_entity` (optional): take the target indoor temperature from an entity
  (`input_number`, `number` or `sensor`), so it can be changed from a dashboard or an automation.
  Falls back to the fixed `target_temp` when not set or not numeric. (#3)
- MQTT debug payload: `input_sensors.target_temperature` (value, bias, source).

### Changed
- `current_offset` now also accepts `number` and `input_number` entities (e.g. the NIBE
  integration exposes register 47011 as a `number`). (#3)

---

## [v4.5.1] – 2026-11-19

### Fixed
- **Optional HDO input blocked all writes** (#4) – `default: none` is the string `"none"` in YAML,
  not null, so `hdo_ent is none` was always false and the HDO condition aborted every run when
  no HDO sensor was selected. Optional inputs (`hdo`, `cheap_block`, `cop_sensor`,
  `last_write_helper`) are now treated as "not configured" when they are null, empty or `"none"`.
  This also fixes `configured: true` in the MQTT debug payload for unset COP / 6h block sensors
  and the failing `input_datetime.set_datetime` call when no last-write helper is selected.

---

## [v4.5] – 2026-10-28

### Added
- **VV-AI** – smart hot water control as a pyscript (`vv_ai/vv_ai.py`): learns a weekly
  hot water usage profile (168 hourly slots from the BT6 drop) and sets the hot water
  comfort mode (47041) every 15 minutes by profile, electricity price and PV surplus,
  with BT6/BT7 safety floors. Profile stored as a retained MQTT message.
- `vv_ai/vv_ai_package.yaml` – MQTT sensors (decision, diagnostics, profile store) and
  a PV surplus average
- `docs/vv-ai.md` – description, installation, troubleshooting (Czech)

---

## [v4.4] – 2026-03-02

### Changed
- **Spot price influence reduced 3×** – coefficient -0.8 → -0.3, offset +4.0 → +1.5
- Indoor temperature now dominates control (recommended: indoor_bias = 0.0)
- At a price of 10 units/kWh, offset is -1.5 instead of -4.0 (previously too aggressive)

---

## [4.4] – 2026-02-22

### Added
- `spot_slope` input: configurable spot price coefficient (default: -0.8)
- `spot_intercept` input: configurable spot price base value (default: 4.0)
- `preheat_price_threshold` input: max spot price to allow preheating (default: 2.5) – no longer hardcoded
- `preheat_ratio` input: future/current price ratio that triggers preheating (default: 1.3)
- `preheat_look_ahead_hours` input: how many hours ahead to check price (default: 4)
- `degree_minutes_guard` input: configurable alarm threshold for degree-minutes (default: -800)
- `source_url` in blueprint metadata for HACS compatibility
- MQTT debug payload now includes active configuration values (`configuration` section)

### Changed
- Renamed blueprint file from `Smart_NIBE_Ultra_Adaptive_FINAL_v2_9_2.yaml` to `smart_nibe_control.yaml`
- Spot price formula now uses configurable slope/intercept instead of hardcoded `-0.8` / `4.0`
- Preheat condition now uses configurable threshold and ratio
- Degree-minutes guard threshold now uses configurable value
- MQTT debug: spot price formula string dynamically reflects configured coefficients
- Version string updated from `4.3 + COP` to `4.4`
- `preheat_5_price_in_4h` renamed to `preheat_5_price_in_Xh` in debug payload to reflect variable look-ahead

### Fixed
- `spot_price` field label in MQTT debug changed from hardcoded currency unit to `currency_unit/kWh` for multi-currency support

---

## [4.3] – 2025-XX-XX

### Added
- COP bonus component (8th calculation factor)
- COP sensor input (`cop_sensor`) – optional
- COP thresholds: >7.0 → -0.8, >6.5 → -0.5, >6.0 → -0.3, <5.0 → +0.5, <4.0 → +0.8
- COP quality label in MQTT debug payload

### Changed
- Blueprint version bumped to v4.3
- MQTT debug payload extended with COP breakdown

---

## [2.9.2] – 2025-XX-XX

### Initial public release
- 7-component adaptive offset calculation
- Spot price optimization
- Equithermal curve adjustment
- Indoor temperature feedback
- Look-ahead preheating (4h)
- Solar malus (9:00–15:00 window)
- Weather forecast bonus
- 6-hour cheap block bonus
- Degree-minutes guard
- MQTT debug publish
- HDO binary sensor support
- EEPROM write protection (interval + comfort override)
