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
   - name: "NIBE Offset Debug"
     state_topic: "nibe/debug/offset_calc"
     value_template: "{{ value_json.final }}"
     json_attributes_topic: "nibe/debug/offset_calc"

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











