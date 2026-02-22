## 🧩 Použité helpery (Home Assistant)

Tato automatizace využívá několik **helperů Home Assistantu**
(`input_number`, případně senzory), které umožňují
**dlouhodobé učení domu, jemné ladění a bezpečný provoz**.

Helpery jsou záměrně oddělené od samotné logiky automatizace,
aby byla regulace:
- přehledná
- stabilní
- snadno laditelná
- a neagresivní

---

### 🔹 Indoor bias – dlouhodobý posun domu  
`input_number.indoor_bias`

**Účel:**  
Kompenzuje **dlouhodobou systematickou odchylku** chování domu.

**Proč existuje:**  
Každý dům se chová jinak.  
Některé domy jsou trvale o něco chladnější / teplejší,
než by odpovídalo ekvitermní křivce.

Místo neustálého zvyšování nebo snižování křivky
se dům **postupně „naučí“ sám sebe**.

**Vliv:**
- kladná hodnota → dům má tendenci být chladnější → přidá se výkon
- záporná hodnota → dům má tendenci být teplejší → výkon se ubere
---
### 🔹 Stupňominuty (Degree Minutes)

sensor.degree_minutes

Účel:
Chrání tepelné čerpadlo před přetížením
a spuštěním elektrické patrony.

Proč existují:
Stupňominuty jsou klíčová interní veličina NIBE,
která vyjadřuje akumulovaný tepelný deficit.

Jejich sledováním lze:

zpomalit nárůst výkonu

zabránit pádu k −700

chránit COP i kompresor

Použití v automatizaci:

DM Guard

omezení rychlosti změn


Účel:
Poskytuje aktuální cenu elektřiny.

Požadavky:

musí mít aktuální cenu

ideálně i atribut today[] pro pohled dopředu

Použití:

optimalizace nákladů

logika předtopení

ekonomické rozhodování
---
### 🔹 Nejlevnější blok (např. 6 hodin)

sensor.cheapest_6h_block

Účel:
Binární informace, že probíhá nejlevnější část dne.

Proč existuje:
Umožňuje bezpečné, ale výraznější předtopení
v předem známých levných hodinách.

Vliv:

zapnuto → přidá se bonus k offsetu

vypnuto → bez bonusu
---
###🔹 Aktuální offset topné křivky

sensor.current_offset

Účel:
Zobrazuje skutečný offset, který je právě nastavený v NIBE.

Proč existuje:
Automatizace musí vždy vycházet z reality,
jinak by docházelo ke kmitání a zbytečným zápisům.

Použití:

omezení rychlosti změn

ochrana EEPROM

stabilita regulace
---
### 🔹 Volitelně: HDO / blokace sítě

binary_sensor.hdo

Účel:
Zabrání regulaci během blokovaných tarifních období.

Chování:

pokud je zadáno → regulace běží jen při HDO = ON

pokud není → regulace je vždy povolena

**Doporučené nastavení:**
```yaml

configuration.yaml
input_number:
  indoor_bias:
    name: Bias vnitřní teploty
    min: -1.0
    max: 1.0
    step: 0.05
    unit_of_measurement: "°C"


input_number:
  indoor_response_gain:
    name: Zesílení reakce regulace
    min: 0.5
    max: 1.5
    step: 0.1


input_number:
  weather_forecast_trend:
    name: Trend počasí (nejbližší hodiny)
    min: -10
    max: 10
    step: 0.1
    unit_of_measurement: "°C"


input_number:
  weather_forecast_avg_6h:
    name: Forecast avg 6h
    min: -30
    max: 20
    step: 0.1
    unit_of_measurement: "°C"

mqtt.yaml
mqtt:
 senzor:
   # ===========================================================================
  # HLAVNÍ SENZOR - Obsahuje VŠE v JSON atributech
  # ===========================================================================  

  - name: "NIBE Offset Debug"
    unique_id: nibe_offset_debug
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.offset.finalni }}"
    unit_of_measurement: "offset"
    icon: mdi:thermometer-lines
    json_attributes_topic: "nibe/debug/offset_calc"
    json_attributes_template: "{{ value_json | tojson }}"
  
  # ===========================================================================
  # TOP 10 SENZORŮ
  # ===========================================================================
  
  - name: NIBE Offset Finální
    unique_id: nibe_offset_final
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.offset.finalni | default(0) }}"
    icon: mdi:target
  
  - name: NIBE Offset Změna
    unique_id: nibe_offset_change
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.offset.zmena | default(0) }}"
    icon: mdi:delta
  
  - name: NIBE Vliv Spot Ceny
    unique_id: nibe_component_spot
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['1_vliv_spot_ceny'].hodnota | default(0) | round(2) }}"
    icon: mdi:currency-eur
  
  - name: NIBE Vliv Vnitřní Korekce
    unique_id: nibe_component_indoor
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['3_vnitrni_korekce'].hodnota | default(0) | round(2) }}"
    icon: mdi:home-thermometer-outline
  
  - name: NIBE Vliv Ekviterm
    unique_id: nibe_component_ekvi
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['2_ekvitermni_posun'].hodnota | default(0) | round(2) }}"
    icon: mdi:chart-line
  
  - name: NIBE Spot Cena
    unique_id: nibe_debug_spot_price
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.spot_price.hodnota | default(0) | round(3) }}"
    unit_of_measurement: "Kč/kWh"
    icon: mdi:currency-eur
  
  - name: NIBE Venkovní Teplota
    unique_id: nibe_outdoor_temp
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.venkovni_teplota.hodnota | default(0) | round(1) }}"
    unit_of_measurement: "°C"
    icon: mdi:thermometer
    device_class: temperature
  
  - name: NIBE Vnitřní Teplota
    unique_id: nibe_indoor_temp
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.vnitrni_teplota.hodnota | default(0) | round(1) }}"
    unit_of_measurement: "°C"
    icon: mdi:home-thermometer
    device_class: temperature
  
  - name: NIBE Stupňominuty
    unique_id: nibe_degree_minutes
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.stupnominuty.hodnota | default(0) | round(0) }}"
    unit_of_measurement: "°C·min"
    icon: mdi:timer-sand
  
  - name: NIBE Minut Od Zápisu
    unique_id: nibe_eeprom_minutes
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.ochrana_a_limity.eeprom_ochrana.minut_od_zapisu | default(0) | round(1) }}"
    unit_of_measurement: "min"
    icon: mdi:timer

  - name: "NIBE Vliv Spot Ceny"
    unique_id: nibe_component_spot
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['1_vliv_spot_ceny'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:currency-eur
    
  - name: "NIBE Vliv Ekviterm"
    unique_id: nibe_component_ekvi
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['2_ekvitermni_posun'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:chart-line
    
  - name: "NIBE Vliv Vnitřní Korekce"
    unique_id: nibe_component_indoor
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['3_vnitrni_korekce'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:home-thermometer-outline
    
  - name: "NIBE Bonus 6h Blok"
    unique_id: nibe_bonus_6h
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['4_bonus_6h_blok'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:clock-time-six
    
  - name: "NIBE Preheat Bonus"
    unique_id: nibe_preheat_bonus
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['5_preheat_bonus'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:fire-alert
    
  - name: "NIBE Solar Malus"
    unique_id: nibe_solar_malus
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['6_solar_malus'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:white-balance-sunny
    
  - name: "NIBE Forecast Bonus"
    unique_id: nibe_forecast_bonus
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['7_forecast_bonus'].hodnota | default(0) | round(2) }}"
    unit_of_measurement: ""
    icon: mdi:crystal-ball

  # ── COP ─────────────────────────────────────────────
  - name: "NIBE Debug COP"
    unique_id: nibe_debug_cop_hodnota
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.cop.hodnota }}"
    unit_of_measurement: ""
    icon: mdi:lightning-bolt-circle

  - name: "NIBE Debug COP Kvalita"
    unique_id: nibe_debug_cop_kvalita
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.cop.kvalita }}"
    icon: mdi:star-circle

  - name: "NIBE Debug COP Bonus"
    unique_id: nibe_debug_cop_bonus
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['8_cop_bonus'].hodnota }}"
    unit_of_measurement: ""
    icon: mdi:plus-minus

number:
  - name: Teplotní křivka Offset
    unique_id: Heat Offset S1
    json_attributes_topic: "{{ value_json.state }}"
    min: -6
    max: 6
    step: 1
    state_topic: "nibe/modbus/47011"
    command_topic: "nibe/modbus/47011/set"


  - name: Teplotní křivka Offset
    unique_id: a220223829
    state_topic: "nibe/modbus/47011"

binary_sensor:
  - name: NIBE Zápis Povolen
    unique_id: nibe_write_allowed
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.ochrana_a_limity.eeprom_ochrana.write_allowed | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:check-circle
  
  - name: NIBE DM Alarm
    unique_id: nibe_dm_alarm
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vstupni_senzory.stupnominuty.alarm | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:alert
    device_class: problem
  
  - name: NIBE Senzory OK
    unique_id: nibe_check_sensors
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.rozhodnuti.kontroly.senzory_dostupne | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:check
    device_class: connectivity

  - name: "NIBE 6h Blok Nakonfigurován"
    unique_id: nibe_6h_configured
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['4_bonus_6h_blok'].nakonfigurovano | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:cog
    
  - name: "NIBE Preheat Aktivní"
    unique_id: nibe_preheat_active
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['5_preheat_bonus'].aktivni | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:fire
    
  - name: "NIBE Solar Aktivní"
    unique_id: nibe_solar_active
    state_topic: "nibe/debug/offset_calc"
    value_template: "{{ value_json.vypocet_offsetu.rozpad_slozek['6_solar_malus'].aktivni | default(false) }}"
    payload_on: true
    payload_off: false
    icon: mdi:weather-sunny









