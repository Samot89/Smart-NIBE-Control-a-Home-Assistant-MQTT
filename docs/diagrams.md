# 📊 Diagramy

## Architektura

```mermaid
flowchart LR
    Spot[Spot ceny]
    Weather[Počasí]
    Indoor[Vnitřní teplota]

    HA[Home Assistant]
    MQTT[MQTT]
    Bridge[nibepi / ESP]
    NIBE[NIBE TČ]

    Spot --> HA
    Weather --> HA
    Indoor --> HA

    HA -->|offset| MQTT --> Bridge -->|Modbus| NIBE
    NIBE -->|stav| Bridge --> MQTT --> HA
