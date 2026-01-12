# 🔌 Komunikace (MQTT / Modbus)

## MQTT+conf.yaml config

```text

mqtt:
number:
  - name: Teplotní křivka Offset
    unique_id: Heat Offset S1
    json_attributes_topic: "{{ value_json.state }}"
    min: -6
    max: 6
    step: 1
    state_topic: "nibe/modbus/47011"
    command_topic: "nibe/modbus/47011/set"

sensor:
  - name: Teplotní křivka Offset
    unique_id: a220223829
    state_topic: "nibe/modbus/47011"


configuration.yaml

- sensor:
      - name: "Last NIBE offset"
        state: >
          {{ states('number.teplotni_krivka_offset') | float }}
        icon: mdi:chart-line
