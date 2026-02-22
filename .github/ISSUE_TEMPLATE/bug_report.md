---
name: Bug report
about: Report a problem with the blueprint
title: "[BUG] "
labels: bug
assignees: Samot89
---

## Popis problému / Problem description

<!-- Stručně popiš co se děje špatně / Briefly describe what is going wrong -->

## Verze blueprintu / Blueprint version

<!-- Zkontroluj v HA → Nastavení → Automatizace → Blueprint / Check in HA → Settings → Automations → Blueprint -->
- Verze / Version: `v4.x`

## Prostředí / Environment

- Home Assistant verze / version:
- Integrace spot ceny / Spot price integration: `(např. Nordpool, Tibber, OTE...)`
- NIBE model: `(např. F1255, S1255...)`
- Připojení k HA / Connection to HA: `(nibepi / Modbus-MQTT / jiné)`

## Konfigurace blueprintu / Blueprint configuration

<!-- Vyplň hodnoty svých !input parametrů / Fill in your !input parameter values -->

| Parametr | Hodnota |
|----------|---------|
| spot_slope | |
| spot_intercept | |
| preheat_price_threshold | |
| degree_minutes_guard | |
| max_offset | |
| min_offset | |
| min_write_interval_minutes | |

## Co se očekávalo / Expected behavior

<!-- Co by se mělo stát? -->

## Co se stalo / Actual behavior

<!-- Co se skutečně stalo? -->

## Logy / Logs

<!-- Vlož obsah MQTT debug topicu nebo HA logy -->
<details>
<summary>MQTT debug payload</summary>

```json
// vlož zde / paste here
```

</details>

<details>
<summary>Home Assistant logy</summary>

```
// vlož zde / paste here
```

</details>

## Doplňující informace / Additional context

<!-- Cokoliv dalšího, screenshoty atd. -->
