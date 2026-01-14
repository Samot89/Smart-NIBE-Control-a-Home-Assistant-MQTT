# Chytré řízení tepelného čerpadla NIBE přes Home Assistant (MQTT) Blueprintu

Adaptivní řízení offsetu topné křivky tepelného čerpadla **NIBE** pomocí
**Home Assistantu**.  
Navrženo pro **spotové ceny elektřiny**, **předpověď počasí** a **stabilní vnitřní komfort**
– bez zapínání / vypínání kompresoru.

Tento projekt funguje jako **nadřazený regulátor**, který respektuje
vnitřní logiku NIBE a pouze ji jemně koriguje.

---

## ✨ Funkce

- Řízení **offsetu topné křivky** (Modbus registr **47011**)
- Reakce na **spotové ceny elektřiny**
- Zohlednění **předpovědi počasí (trend)**
- Korekce podle **vnitřní teploty**
- **Dlouhodobé učení domu (bias)**
- **Auto-tuning síly reakce**
- Podpora **HDO**
- Komunikace přes **MQTT / nibepi**
- Plná transparentnost (debug & grafy)

---

## 🧠 Filozofie řízení

- Home Assistant je **jediný mozek řízení**
- Vnitřní regulace NIBE zůstává zachována
- Neřídí se zapnutí / vypnutí TČ
- Pouze **plynulá úprava topné křivky**
- Optimalizováno pro **podlahové topení**

Tento projekt **není hack**, ale **nadřazený adaptivní regulátor**.

## 🚀 Instalace Blueprintu

Tato kapitola popisuje kompletní postup instalace a zprovoznění blueprintu
pro chytré řízení tepelného čerpadla **NIBE** pomocí **Home Assistantu** a **MQTT**.

---

### 1️⃣ Požadavky

Před instalací se ujisti, že máš k dispozici:

- funkční **Home Assistant**
- běžící **MQTT broker** (např. Mosquitto)
- komunikaci s NIBE přes:
  - **nibepi**, nebo
  - jiný **Modbus → MQTT bridge**
- senzor **spotové ceny elektřiny** (OTE / Nordpool apod.)
- senzor **vnitřní teploty**
- entitu **počasí** (např. Open-Meteo)
- (volitelně) binární senzor **HDO**

---

### 2️⃣ Umístění souboru Blueprintu

Stáhni soubor blueprintu:

smart_nibe_offset_adaptive_v2

arduino
Zkopírovat kód
---
a ulož jej do adresáře:

/config/blueprints/automation/

3️⃣ Načtení Blueprintu v Home Assistantu

Otevři Nastavení → Automatizace a scény → Blueprinty

Klikni na Znovu načíst blueprinty

Ověř, že se v seznamu objeví:
Smart NIBE – Ultra Adaptive (Winter + Ekviterm + Spot)

4️⃣ Vytvoření potřebných helperů

Blueprint využívá několik helperů (input_number), které je nutné vytvořit
buď přes UI Home Assistantu, nebo vložením do YAML konfigurace.


Hodnota trendu může být počítána automatizací nebo Node-REDem
(např. rozdíl mezi aktuální a predikovanou venkovní teplotou).

5️⃣ Vytvoření automatizace z Blueprintu

Otevři Nastavení → Automatizace → Vytvořit automatizaci

Zvol Vytvořit z blueprintu

Vyber Smart NIBE – Ultra Adaptive (Winter + Ekviterm + Spot)

Vyplň jednotlivé vstupy:

Spot price sensor – senzor spotové ceny elektřiny

Cheapest 6h block sensor – binární senzor levného bloku

Weather entity – entita počasí

Indoor temperature sensor – senzor vnitřní teploty

Forecast trend helper – input_number.weather_forecast_trend

Indoor bias helper – input_number.indoor_bias

Indoor response gain helper – input_number.indoor_response_gain

Current NIBE offset sensor – aktuální offset topné křivky

MQTT topic – např. nibe/modbus/47011/set

HDO sensor – volitelné (pokud není, lze ponechat prázdné)

6️⃣ Ověření funkce

Po uložení automatizace doporučujeme:

sledovat MQTT topic:

nibe/debug/offset_calc


ověřit, že:

offset se mění pouze při významné změně

hodnota je vždy v nastavených mezích

nedochází k častému přepisování (ochrana EEPROM)

První 1–2 dny je vhodné systém pouze sledovat
a teprve poté jemně ladit koeficienty.



---

## 🏗 Architektura

```mermaid
flowchart LR
  Spot[Spotová cena]
  Weather[Předpověď počasí]
  Indoor[Vnitřní teplota]
  HA[Home Assistant]
  MQTT[MQTT / nibepi]
  NIBE[NIBE TČ]

  Spot --> HA
  Weather --> HA
  Indoor --> HA
  HA --> MQTT
  MQTT --> NIBE
