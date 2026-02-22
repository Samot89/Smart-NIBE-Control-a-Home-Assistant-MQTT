# 🌡️ Smart NIBE Control – Home Assistant Blueprint

An **adaptive, high-level control system** for NIBE heat pumps using
**Home Assistant** and **MQTT**.

This project dynamically adjusts the **heat curve offset (Modbus register 47011)**
based on electricity spot prices, weather conditions, indoor comfort, and
heat pump protection — **without switching the compressor on/off**.

Think of it as a *brain*, not a switch.

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Samot89/Smart-NIBE-Control-a-Home-Assistant-MQTT/main/smart_nibe_control.yaml)

---

## ✨ Key Features

- Adaptive control of **heat curve offset** (Modbus 47011)
- Optimization based on **spot electricity prices**
- **Look-ahead price prediction** (preheating before price spikes, configurable 1–8 h)
- **Outdoor temperature (equithermal / weather-compensated logic)**
- **Indoor temperature feedback** (comfort-first)
- **Solar gain reduction** (sunny weather awareness)
- **Degree Minutes protection (DM Guard)** – configurable threshold
- **Smooth ramping (slew rate limiting)** to protect the compressor
- **Configurable spot price formula** (slope + intercept)
- Optional **HDO / grid signal support**
- Communication via **MQTT / nibepi**
- Full transparency via **debug MQTT logs**

---

## 🧠 Design Philosophy

- Home Assistant acts as a **supervisory controller**
- Native NIBE regulation remains fully active
- The compressor is **never switched directly**
- Only the **heat curve offset** is adjusted
- Designed primarily for **underfloor heating systems**

This is **not a hack** — it is a *layer above* the manufacturer's logic.

---

## 🔄 How the Automation Works (v4.4)

This automation acts as the **central decision engine** for heating.
It combines **economics, building physics, comfort feedback, and hardware protection**.

### 1️⃣ Equithermal Base (Physics-first)

The base heat demand is derived from **outdoor temperature**:

- colder outside → higher base offset
- milder weather → lower base offset
- fully aligned with NIBE's equithermal philosophy

This ensures stable behavior even during severe frost.

---

### 2️⃣ Spot Price Optimization (Economics)

The equithermal base is adjusted according to the **current electricity price**:

- **cheap electricity** → increase offset (thermal storage)
- **expensive electricity** → reduce offset (load shedding)

The building itself becomes a **thermal battery**.

The formula coefficients (`spot_slope`, `spot_intercept`) are now **fully configurable**,
making the blueprint currency-independent.

---

### 3️⃣ Look-ahead Preheating (Price Prediction)

The automation looks **ahead** by a configurable number of hours (1–8 h, default 4 h):

- if prices are expected to rise by a configurable ratio (default **~30%**)
- and current prices are below a configurable threshold
- **preheating is activated proactively**

Built-in safeguards prevent failures when price data is missing or incomplete.

---

### 4️⃣ Solar Gain Reduction

If the weather indicates **sunny conditions during daytime**:

- heating output is reduced
- passive solar gains through windows are expected

This prevents overheating and improves overall efficiency.

---

### 5️⃣ Indoor Temperature Feedback (Comfort Loop)

The system continuously evaluates **indoor temperature**:

- warmer than target → offset is reduced
- colder than target → offset is increased

This correction:
- is scaled by an adjustable **response gain**
- slowly adapts via a long-term **indoor bias**
- never overrides physical or safety limits

Comfort always has higher priority than aggressive cost optimization.

---

### 6️⃣ Degree Minutes Guard (DM Protection)

The automation monitors **Degree Minutes**:

- when DM drops below a configurable threshold (default −800)
- ramp-up speed is reduced
- prevents triggering electric backup heating

This protects:
- COP efficiency
- compressor lifetime
- system stability

---

### 7️⃣ Smooth Transitions (Slew Rate Limiting)

Offset changes are **never abrupt**:

- maximum change per hour is limited
- even more restrictive during critical states
- no thermal or mechanical shocks

Result:
- stable Degree Minutes
- smooth compressor operation
- long-term reliability

---

### 8️⃣ Write Protection & Transparency

A new offset is written only if:

- the change exceeds a defined threshold
- HDO (if used) allows operation

Every action is logged via MQTT (`nibe/debug/offset_calc`), enabling:

- debugging
- performance analysis
- proof of real-world benefits

---

## 🚫 What This Automation Intentionally Does NOT Do

- ❌ It does NOT switch the compressor on/off
- ❌ It does NOT bypass NIBE safety logic
- ❌ It does NOT control relays or power lines
- ❌ It does NOT chase temperature in 0.1 °C steps
- ❌ It does NOT react hysterically to short-term fluctuations

If you want *"cheap = ON, expensive = OFF"* logic,
this is **not** the right project.

---

## 🧰 Troubleshooting by Symptoms

### 🔥 House overheating
- Reduce `response_gain`
- Reset or reduce `indoor_bias`
- Check solar gain reduction logic

### 🧊 House too cold
- Increase `max_offset`
- Allow bias to adapt over several days
- Verify spot price input accuracy

### ⚡ Too many writes to NIBE
- Increase `min_change`
- Check sensor stability

### 🧯 Electric heater activates
- Verify Degree Minutes sensor
- Ensure DM Guard is active
- Lower the `degree_minutes_guard` threshold

### 📉 Automation seems inactive
- Offset change may be below threshold
- HDO may block operation
- Often this means the system is already optimal

---

## 🔄 Decision Flow Diagram

```mermaid
flowchart TD
    A[Start – every 2 minutes] --> B[Load input data]
    B --> C{Data valid?}
    C -- no --> Z[Fallback<br/>keep current state]
    C -- yes --> D[Equithermal base<br/>outdoor temperature]

    D --> E[Spot price optimization]
    E --> F{Price increase > configured ratio?}
    F -- yes --> G[Preheating<br/>look-ahead bonus]
    F -- no --> H[No preheating]

    G --> I
    H --> I

    I[Solar gain reduction<br/>sunny weather?] --> J[Indoor temperature feedback]
    J --> K[Degree Minutes Guard]
    K --> L[Clamping<br/>min / max offset]
    L --> M[Slew rate limit<br/>smooth transition]

    M --> N{Change > min_change?}
    N -- no --> O[Do not write<br/>EEPROM protection]
    N -- yes --> P[MQTT write<br/>Modbus 47011]

    P --> Q[MQTT debug log]
```

---

## 📚 Documentation

For detailed information, please refer to the following documentation:

- **[FAQ](docs/FAQ.md)** - Frequently Asked Questions
- **[Architecture](docs/architecture.md)** - System architecture overview
- **[Communication](docs/communication.md)** - MQTT and Modbus communication details
- **[Diagrams](docs/diagrams.md)** - System diagrams
- **[Home Assistant](docs/home-assistant.md)** - Home Assistant configuration details
- **[NIBE / nibepi](docs/nibe-nibepi.md)** - NIBE heat pump and nibepi bridge setup
- **[Dashboard](DASHBOARD.md)** - Dashboard setup and configuration
- **[Helpers](Helpery.md)** - Helper entities and their usage
- **[Changelog](CHANGELOG.md)** - Version history

---

## 📋 Requirements

- NIBE heat pump (F-series or S-series)
- Home Assistant
- MQTT broker (e.g. Mosquitto)
- nibepi or compatible Modbus-MQTT bridge
- Spot electricity price integration (Nordpool, Tibber, OTE…)
- Weather integration (e.g. Open-Meteo)
- Indoor temperature sensor

---

## 🚀 Installation

1. Click the **Import Blueprint** button above
2. Configure required entities (spot price, weather, sensors)
3. Set up helper entities (input_number helpers) – see [Helpery.md](Helpery.md)
4. Configure MQTT topics for your nibepi/bridge
5. Adjust parameters according to your house characteristics
6. Monitor and fine-tune over several days

---

## ⚖️ License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- NIBE for providing Modbus access to their heat pumps
- [nibepi project](https://github.com/anerdins/nibepi) for the MQTT-Modbus bridge
- Home Assistant community for integrations and support
- [Community discussion](https://community.home-assistant.io/t/smart-nibe-ultra-adaptive-heat-curve-control-mqtt-spot-prices/975863)
