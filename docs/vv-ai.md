# 🚿 VV-AI – chytré řízení teplé vody (TUV)

VV-AI se učí, kdy v domě odebíráte teplou vodu, a podle toho, ceny elektřiny
a přetoků z FVE přepíná **komfortní režim TUV** tepelného čerpadla NIBE
(Modbus **47041**): `0 = Economy`, `1 = Normal`, `2 = Luxury`.

Doplňuje blueprint Smart NIBE Control: ten řídí topení přes posun křivky
(47011), VV-AI řídí jen teplou vodu (47041). Můžou běžet současně.

Běží jako [pyscript](https://github.com/custom-components/pyscript) v Home
Assistantu, s čerpadlem komunikuje přes MQTT (nibepi nebo jiný Modbus ↔ MQTT bridge).

---

## ✨ Co dělá

| Funkce | Popis |
|---|---|
| 🧠 **Učení odběrů** | Každou hodinu porovná BT6 (spodní část zásobníku) s předchozí hodinou. Pokles ≥ 2 °C = odběr. Ukládá týdenní profil – 168 slotů (den × hodina) s průměrným poklesem. |
| 🔮 **Předehřev** | Dívá se 2 h dopředu do profilu: čeká se velký odběr → vyšší režim předem. |
| ⚡ **Cena elektřiny** | Levná/záporná cena → vyšší režim, drahá → Economy (pokud se nečeká velký odběr). |
| ☀️ **FVE boost** | Přetok ≥ 1500 W → Luxury, ≥ 500 W → aspoň Normal. |
| 🛟 **Pojistky** | BT7 < 43 °C nebo BT6 < 42 °C → vždy Normal. Výpadek dat → Normal. |
| 💾 **Bez souborů** | Profil je uložený jako retained MQTT zpráva – přežije restart HA. |

### Pořadí rozhodování (každých 15 min)

```
1. BT7 nedostupná                  → Normal
2. BT7 < 43 °C                     → Normal
3. BT6 < 42 °C                     → Normal
4. FVE ≥ 1500 W                    → Luxury
   FVE ≥ 500 W                     → Normal (Luxury, pokud profil čeká velký odběr)
5. podle ceny a profilu (příští 2 h):
   max. očekávaný pokles  ≥ 8 °C → Luxury | ≥ 3 °C → Normal | jinak Economy
   cena ≤ 0      → Luxury
   cena ≤ 4.5    → aspoň Normal
   cena ≤ 6.0    → aspoň Normal
   cena ≤ 8.0    → nejvýš Normal
   cena > 8.0    → Economy (Normal, pokud se čeká pokles ≥ 5 °C)
```

Prahy cen jsou v jednotce vašeho senzoru ceny (např. Kč/kWh včetně distribuce)
a nastavují se na začátku `vv_ai.py`.

---

## 📋 Požadavky

- **NIBE** s registry BT6 (40014), BT7 (40013) a zápisem do **47041** (ověřeno na VVM 320)
- **nibepi** nebo jiný bridge publikující registry do MQTT
- **Home Assistant** + MQTT integrace
- **pyscript** (HACS → Integrace → *Pyscript Python scripting*)
- senzor **ceny elektřiny** za kWh, např. [CZ Energy Spot Prices](https://github.com/rnovacek/homeassistant_cz_energy_spot_prices)
- volitelně senzor **přetoků FVE** do sítě (W)

> ⚠️ V čerpadle **vypněte Smart Price Adaption** (menu 4.1.6) – jinak by
> čerpadlo režim TUV měnilo samo.

> ⚠️ **Periodu TUV (registr 47134) nechte na původní hodnotě (typicky 20–30 min), nikdy 0.**
> VV-AI mění jen režim TUV a ohřev dělá čerpadlo samo podle start/stop teplot režimu.
> S periodou 0 by čerpadlo TUV neohřálo vůbec. (Periodu 0 používá jiné řešení –
> VV-AI zabudované v NibePi, které spouští ohřev samo přes registr 48132. Obě
> řešení nekombinujte.)

---

## 🚀 Instalace

### 1. Pyscript
Nainstalujte pyscript přes HACS a do `configuration.yaml` přidejte:
```yaml
pyscript:
  allow_all_imports: true
```

### 2. Skript
Zkopírujte [`vv_ai/vv_ai.py`](../vv_ai/vv_ai.py) do `/config/pyscript/vv_ai.py`
a na začátku souboru upravte entity:

| Konstanta | Co to je | Příklad |
|---|---|---|
| `BT6_ENTITY` | BT6 – spodní část zásobníku TUV | `sensor.nibe_bt6_hw_load` |
| `BT7_ENTITY` | BT7 – horní část zásobníku TUV | `sensor.nibe_bt7_hw_top` |
| `SPOT_ENTITY` | aktuální cena za kWh | `sensor.current_buy_electricity_price_15min` |
| `SOLAR_ENTITY` | průměrné FVE přetoky (W) | `sensor.pretoky_klouzavy_prumer_15min` |
| `HW_TOPIC` | MQTT topic pro zápis 47041 | `nibe/modbus/47041/set` (nibepi) |

### 3. MQTT senzory
Zkopírujte [`vv_ai/vv_ai_package.yaml`](../vv_ai/vv_ai_package.yaml) do
`/config/packages/vv_ai.yaml` (balíčky musí být zapnuté v `configuration.yaml`)
a nahraďte `sensor.grid_export_power` svým senzorem přetoků.
Bez FVE sekci `sensor:` smažte.

### 4. Restart
Restartujte Home Assistant. V logu (`Nastavení → Systém → Protokoly`, filtr
`VV-AI`) se do hodiny objeví první `VV-AI: profil ulozen` a do 15 minut
`VV-AI: -> Normal (...)`.

---

## 📊 Entity

| Entita | Obsah |
|---|---|
| `sensor.vv_ai_rozhodnuti` | aktuální režim, v atributu `reason` důvod |
| `sensor.vv_ai_diagnostika` | `ok:<hodina týdne>`, atributy `bt6`, `learned`, `nonzero_slots` |
| `sensor.vv_ai_profil_uloziste` | profil (168 hodnot) a počty v atributech |

`nonzero_slots` ukazuje, kolik hodin týdne už má naučený odběr.
Po prvním týdnu bývá 15–25, po dvou týdnech je profil použitelný.

### Karta do dashboardu
```yaml
type: entities
title: VV-AI – teplá voda
entities:
  - entity: sensor.vv_ai_rozhodnuti
    name: Režim TUV
  - type: attribute
    entity: sensor.vv_ai_rozhodnuti
    attribute: reason
    name: Důvod
  - entity: sensor.vv_ai_diagnostika
    name: Učení
  - type: attribute
    entity: sensor.vv_ai_diagnostika
    attribute: nonzero_slots
    name: Naučené hodiny týdne
  - entity: sensor.nibe_bt7_hw_top
    name: BT7 nahoře
  - entity: sensor.nibe_bt6_hw_load
    name: BT6 dole
```

---

## 🧰 Řešení problémů

| Příznak | Příčina / řešení |
|---|---|
| Stále `Normal (vypadek BT7)` | `BT7_ENTITY` neodpovídá vaší entitě nebo nemá hodnotu |
| `bt6_none` v diagnostice | totéž pro `BT6_ENTITY`; občas při krátkém výpadku Modbusu, neškodí |
| Profil se nenaplňuje | odběry jsou menší než `DROP_MIN` (2 °C/h) – snižte, nebo počkejte na větší odběr |
| „Umytí rukou“ se počítá jako odběr | zvyšte `DROP_MIN` na 3 |
| Režim se nemění v čerpadle | ověřte zápis do 47041 přes `HW_TOPIC`, vypněte Smart Price Adaption |
| TUV se vůbec neohřívá | perioda TUV (47134) je 0 – nastavte zpět na 20–30 min (typicky po přechodu z VV-AI v NibePi) |
| Po restartu HA prázdný profil | MQTT broker neuchovává retained zprávy (persistence vypnutá) |

### Reset profilu
Smažte retained zprávu (prázdný payload s retain):
```yaml
action: mqtt.publish
data:
  topic: nibepi/vv_ai/profile_store
  payload: ""
  retain: true
```

### Vypnutí
Přejmenujte `/config/pyscript/vv_ai.py` na `vv_ai.py.disabled` a zavolejte
`pyscript.reload`. Režim TUV v čerpadle zůstane na poslední hodnotě –
případně ho nastavte ručně na Normal.
