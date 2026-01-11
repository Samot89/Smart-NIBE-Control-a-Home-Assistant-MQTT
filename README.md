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

Příklad:

nibe/modbus/47011   → stav (float)
nibe/modbus/47011   ← příkaz (float)

🧪 Stav offsetu v Home Assistantu
Zdroj pravdy

Používá se existující entita:

number.teplotni_krivka_offset


Z ní je vytvořen template senzor:

template:
  - sensor:
      - name: "Last NIBE offset"
        state: >
          {{ states('number.teplotni_krivka_offset') | float }}


Výsledná entita:

sensor.last_nibe_offset


➡️ Slouží jako:

kontrola aktuální hodnoty

ochrana proti zbytečným zápisům

debug / grafy

🌦️ Počasí – predikce (VARIANTA A)

Forecast se nikdy neukládá celý (limit HA, zbytečné).

Používá se:

výpočet průměru teploty na 6 hodin

trend (oteplení / ochlazení)

Pomocníci
input_number:
  weather_forecast_avg_6h:
    min: -40
    max: 40
    step: 0.1
    unit_of_measurement: "°C"

  weather_forecast_trend:
    min: -20
    max: 20
    step: 0.1
    unit_of_measurement: "°C"

🔋 Spotové ceny

Použité entity (příklad):

sensor.current_spot_electricity_price
sensor.spot_electricity_is_cheapest_6_hours_block


spot = hlavní rozhodovací faktor

levný 6h blok = akumulace tepla

🏠 Komfort
Vnitřní teplota
sensor.nsblack_temperature


cílová teplota: 21.5 °C

NENÍ termostat

pouze jemná korekce (±0.3 až ±0.6)

⚡ HDO
binary_sensor.hdo


absolutní priorita

pokud off → automatizace se nespustí

🤖 Finální automatizace (shrnutí)

Automatizace:

běží 1× za hodinu

počítá:

spot cenu

bonus za levný blok

korekci podle venkovní teploty

korekci podle trendu počasí

ochranu komfortu podle vnitřní teploty

výstup:

offset topné křivky

zápis:

MQTT → nibe/modbus/47011

pouze při změně > 0.4

🛑 Co MUSÍ být vypnuto v nibepi / NIBE

Smart Price Adaptation

Weather control

Indoor control

Jakékoli jiné automatické zásahy do offsetu

Nibepi = jen transport a monitoring

📊 Doporučené grafy v HA

Spot cena × Offset

Offset × Vnitřní teplota

Trend počasí × Offset

✅ Výhody řešení

✔ žádné konflikty řízení
✔ stabilní chod TČ
✔ šetrné ke kompresoru
✔ maximální využití levné energie
✔ transparentní logika
✔ snadné ladění podle domu
✔ plně otevřené řešení

⚠️ Upozornění

projekt není „klikni a hotovo“

určen pro ekvitermní regulaci

optimalizován pro podlahové topení

používáš na vlastní odpovědnost

🏁 Stav projektu

Produkční / stabilní provoz

Možná budoucí rozšíření:

krizový režim při extrémních cenách

watchdog zásahů do registru

adaptivní učení koeficientů

denní / noční cílová teplota



publikovat aktuální hodnotu registru 47011

přijímat zápisy na stejný topic
