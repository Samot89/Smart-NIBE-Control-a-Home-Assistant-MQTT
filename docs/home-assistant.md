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
- sensor.current_spot_electricity_price - aktualní cena spotu 
- sensor.spot_electricity_is_cheapest_6_hours_block - senzor 6.hod nejlevnější spot
integrace spot: https://github.com/rnovacek/homeassistant_cz_energy_spot_prices

### Počasí
- weather.domov_2 -Počasí v HA
- input_number.weather_forecast_avg_6h - Helper
- input_number.weather_forecast_trend - Helper
- integrace počasí: https://www.home-assistant.io/integrations/open_meteo/

### Komfort
- sensor.nsblack_temperature - vnitřní čidlo teploty

### Řízení
- binary_sensor.hdo - senzor HDO
- sensor.last_nibe_offset - stav aktu.offsetu template senzor

---

## Řízení

Automatizace:
- běží 1× za hodinu
- počítá offset
- zapisuje přes MQTT
