# Chytré řízení tepelného čerpadla NIBE přes Home Assistant (MQTT) Blueprintu

Tato automatizace (v2.9.2) je v podstatě **„mozek“ vašeho vytápění**.  
Nedívá se pouze na venkovní teplotu, ale **kombinuje ekonomiku, fyziku domu
a ochranu samotného tepelného čerpadla**.

Cílem není jen ušetřit, ale **topit chytře, plynule a bezpečně**.

---

### 🔹 1️⃣ Ekvitermní základ (fyzika domu)

Automatizace nejprve vyhodnotí **aktuální venkovní teplotu**
(`aktualni_venkovni_teplota`) a stanoví **základní potřebu tepla**.

- čím větší mráz, tím vyšší základní offset
- čím tepleji, tím nižší základ
- dům se chová stabilně i při extrémních zimních podmínkách

Tento krok respektuje původní **ekvitermní filozofii NIBE**.

---

### 🔹 2️⃣ Spotová optimalizace (ekonomika)

Na ekvitermní základ je aplikována **spotová logika** podle
aktuální ceny elektřiny (`current_spot_electricity_price`):

- **levná elektřina** → offset se zvyšuje (předtápění, akumulace)
- **drahá elektřina** → offset se snižuje (útlum výkonu)

Dům je využíván jako **tepelný akumulátor** místo drahé elektřiny.

---

### 🔹 3️⃣ Předtopení – Look-ahead (předvídání)

Automatizace se **dívá dopředu (cca 2 hodiny)**:

- pokud vidí, že cena elektřiny brzy vzroste o **více než ~30 %**
- začne **zvyšovat offset už předem**

Dům se tak „nabije“ teplem **ještě za levnou elektřinu**  
a v drahých hodinách už jen pomalu chladne.

---

### 🔹 4️⃣ Vnitřní korekce – zpětná vazba (komfort)

Automatizace neignoruje realitu uvnitř domu.

Sleduje **vnitřní teplotu** (`nsblack_temperature`) a porovnává ji s cílem:

- pokud je doma **tepleji než cílová teplota**
  - offset se začne snižovat
- pokud je doma **chladněji**
  - offset se naopak zvýší

To platí **i v případě levné elektřiny** –  
komfort má vždy vyšší prioritu než slepé předtápění.

---

### 🔹 5️⃣ Solární brzda (využití slunce)

Pokud předpověď počasí hlásí **jasno / slunečno**:

- automatizace **sníží topný výkon**
- počítá s tím, že:
  - slunce dům zdarma ohřeje přes okna
  - není nutné topit „na plno“

Výsledkem je:
- méně přetápění
- lepší využití pasivních solárních zisků

---

### 🔹 6️⃣ Ochrana stupňominut – DM Guard (ochrana stroje)

Automatizace **neustále sleduje stupňominuty** (`stupnove_minuty`):

- pokud klesnou pod cca **-500**
  - začne **omezovat další přidávání výkonu**
- cílem je zabránit:
  - pádu k -700
  - sepnutí elektrické patrony

Tím chrání:
- kompresor
- COP
- životnost celého systému

---

### 🔹 7️⃣ Plynulost změn – Slew Rate (mechanická ochrana)

Automatizace **nedovolí skokové změny**:

- maximální změna offsetu je cca **±1.0 za hodinu**
- žádné náhlé skoky
- žádné šoky pro kompresor

Výsledek:
- stabilní stupňominuty
- plynulý chod
- dlouhá životnost TČ

---

## 🧠 Shrnutí filozofie

> Automatizace netopí „víc“ ani „míň“.  
> Topí **ve správný čas, správnou silou a z dobrého důvodu**.

Spojuje:
- **fyziku domu**
- **ekonomiku spotového trhu**
- **ochranu technologie**

A dělá to **plynule, předvídavě a bez zbytečných zásahů**.


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
