Chování

HA zapisuje max. 1× za hodinu

zápis pouze při změně > 0.4

aktuální stav je vždy čitelný zpět


---

# 📄 docs/home-assistant.md

```md
# 🏠 Home Assistant konfigurace

## Použité entity

### Spot ceny
- sensor.current_spot_electricity_price
- sensor.spot_electricity_is_cheapest_6_hours_block

### Počasí
- weather.domov_2
- input_number.weather_forecast_avg_6h
- input_number.weather_forecast_trend

### Komfort
- sensor.nsblack_temperature

### Řízení
- binary_sensor.hdo
- sensor.last_nibe_offset

---

## Řízení

Automatizace:
- běží 1× za hodinu
- počítá offset
- zapisuje přes MQTT
