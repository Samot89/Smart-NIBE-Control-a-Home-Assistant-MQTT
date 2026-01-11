# Smart NIBE Control via Home Assistant

Řízení tepelného čerpadla **NIBE** pomocí **Home Assistantu** s využitím:
- spotových cen elektřiny
- predikce počasí
- ekvitermní regulace
- vnitřního komfortu
- MQTT / nibepi (Modbus bridge)

Projekt nahrazuje aktivní řízení v nibepi –  
**Home Assistant je jediný řídicí mozek systému.**

---

## 📌 Hlavní vlastnosti

- plynulá regulace topné křivky (Heat Offset S1 – Modbus 47011)
- žádné zapínání / vypínání TČ
- optimalizace na cenu i počasí
- stabilní chování pro podlahové topení
- žádné konflikty regulátorů

---

## 📖 Dokumentace

- 🧠 [Architektura](docs/architecture.md)
- 🔌 [Komunikace MQTT / Modbus](docs/communication.md)
- 🏠 [Home Assistant konfigurace](docs/home-assistant.md)
- 🔧 [nibepi / Modbus bridge](docs/nibe-nibepi.md)
- 📊 [Diagramy](docs/diagrams.md)
- 📄 [FAG](docs/FAG.md)
---

## ⚠️ Upozornění

Projekt není plug&play.  
Vyžaduje znalost Home Assistantu, MQTT a ekvitermní regulace.

Používáš na vlastní odpovědnost.
je pořád ve fázi testování
za případné nápady budu rád

---

## 📜 Licence

MIT – viz [LICENSE](LICENSE)
