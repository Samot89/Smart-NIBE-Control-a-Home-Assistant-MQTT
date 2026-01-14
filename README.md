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
