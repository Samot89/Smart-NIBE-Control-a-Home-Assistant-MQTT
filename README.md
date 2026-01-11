🏠 Smart NIBE Control via Home Assistant (MQTT / nibepi)

Kompletní řízení tepelného čerpadla NIBE pomocí Home Assistantu,
optimalizované na:

spotové ceny elektřiny

predikci počasí

ekvitermní regulaci (podlahovka)

vnitřní tepelný komfort

bezpečný a šetrný provoz TČ

Projekt nahrazuje aktivní řízení z nibepi – nibepi slouží pouze jako komunikační bridge (Modbus ↔ MQTT).

🎯 Základní filozofie projektu

JEDEN mozek – JEDEN zápis – ŽÁDNÉ KONFLIKTY

Home Assistant = jediný řídicí systém

Zápis pouze do jednoho registru NIBE

Heat Offset S1 → Modbus 47011

nibepi / ESP / Modbus bridge:

pouze čtení a přenos dat

žádná vlastní logika řízení

🧠 Co systém řídí

NEzapíná / nevypíná tepelné čerpadlo

NEpoužívá DM jako hlavní regulaci

ANO:

plynule upravuje offset topné křivky

respektuje fyziku domu a podlahovky

maximalizuje využití levné elektřiny


🔌 Komunikace s NIBE
MQTT topic pro řízení
nibe/modbus/47011


payload: číslo (float)

jednotka: offset topné křivky

retain: true

HA zapisuje max. 1× za hodinu

zápis pouze při významné změně

🧰 Požadavky
Hardware / firmware

NIBE TČ (podporující Modbus)

nibepi / ESP / jiný Modbus ↔ MQTT bridge

MQTT broker (Mosquitto apod.)

Software

Home Assistant (aktuální verze)

Weather integrace (např. Open-Meteo)

Spot ceny (libovolná integrace – hodinová data)

📡 MQTT / nibepi nastavení
Povinné:

nibepi musí:

publikovat aktuální hodnotu registru 47011

přijímat zápisy na stejný topic
