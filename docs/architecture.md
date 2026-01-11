# 🧠 Architektura systému

Základní princip:

> **Jeden řídicí systém – jeden zápis – žádné konflikty**

Home Assistant je jediný systém, který zapisuje do NIBE.

---

## Řídicí tok

- Home Assistant:
  - vyhodnocuje cenu, počasí a komfort
  - vypočítá finální offset
- MQTT:
  - přenáší hodnotu
- nibepi / ESP:
  - pouze překládá MQTT ↔ Modbus
- NIBE:
  - aplikuje offset topné křivky

---

## Řízený registr

- **47011 – Heat Offset S1**
- jediný bod zásahu
