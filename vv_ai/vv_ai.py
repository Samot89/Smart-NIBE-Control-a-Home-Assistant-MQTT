"""
VV-AI — adaptivni rizeni teple vody (TUV) tepelneho cerpadla NIBE v Home Assistant

Uci se tydenni profil odberu teple vody (168 hodinovych slotu, pokles BT6)
a kazdych 15 minut nastavuje komfortni rezim TUV (Modbus 47041):
0 = Economy, 1 = Normal, 2 = Luxury.

Rozhodovani (v tomto poradi):
  1. BT7 nedostupna            -> Normal (FALLBACK)
  2. BT7 < BT7_MIN             -> Normal (pojistka)
  3. BT6 < BT6_MIN             -> Normal (studena nadrz)
  4. FVE pretok >= SOLAR_VERY_CHEAP -> Luxury
     FVE pretok >= SOLAR_CHEAP      -> aspon Normal
  5. cena + naucena spotreba v teto a pristich PREHEAT_H hodinach

Zapis rezimu (HW_WRITE):
  "mqtt"   – 0/1/2 na HW_TOPIC (nibepi / Modbus–MQTT bridge)
  "entity" – nastavi entitu HW_ENTITY (integrace NIBE / myUplink nebo NIBE Heat Pump):
             select -> moznost z HW_OPTIONS, number / input_number -> 0/1/2

Ukladani profilu a stavu (USE_MQTT):
  True  – retained MQTT zpravy + MQTT senzory z vv_ai_package.yaml
  False – bez MQTT: entity pyscript.vv_ai_rozhodnuti / _diagnostika / _profil
          (state.persist – preziji restart HA)
Pyscript nemuze zapisovat soubory.

Umisteni: /config/pyscript/vv_ai.py
Pozor: pyscript nepodporuje generator expressions — pouzivat list comprehension.
"""

import json
from datetime import datetime

# --- Nastaveni: entity (prizpusobte svym nazvum) ---------------------------
BT6_ENTITY      = "sensor.nibe_bt6_hw_load"                     # BT6, spodni cast zasobniku TUV
BT7_ENTITY      = "sensor.nibe_bt7_hw_top"                      # BT7, horni cast zasobniku TUV
SPOT_ENTITY     = "sensor.current_buy_electricity_price_15min"  # aktualni cena za kWh
SOLAR_ENTITY    = "sensor.pretoky_klouzavy_prumer_15min"        # prumerne FVE pretoky ve W (nepovinne)

# --- Nastaveni: zapis rezimu TUV ---------------------------------------------
HW_WRITE        = "mqtt"                     # "mqtt" (nibepi) nebo "entity" (myUplink / NIBE integrace)
HW_TOPIC        = "nibe/modbus/47041/set"    # jen pro "mqtt"; jiny bridge = jiny topic
HW_ENTITY       = "select.hot_water_comfort_mode"  # jen pro "entity": select, number nebo input_number
HW_OPTIONS      = ["economy", "normal", "luxury"]  # jen pro select: moznosti pro 0 / 1 / 2
                                                   # (velikost pismen nevadi; S-serie napr. small/medium/large)

# --- Nastaveni: ukladani profilu a stavu -------------------------------------
USE_MQTT        = True                       # False = bez MQTT brokeru (pyscript.vv_ai_* entity)
STATUS_TOPIC    = "nibepi/vv_ai/ha_mode"     # posledni rozhodnuti (pro dashboard)
DIAG_TOPIC      = "nibepi/vv_ai/diag"        # diagnostika uceni
STORE_TOPIC     = "nibepi/vv_ai/profile_store"
STORE_ENTITY    = "sensor.vv_ai_profil_uloziste" if USE_MQTT else "pyscript.vv_ai_profil"
STATUS_ENTITY   = "sensor.vv_ai_rozhodnuti" if USE_MQTT else "pyscript.vv_ai_rozhodnuti"
DIAG_ENTITY     = "pyscript.vv_ai_diagnostika"   # jen pro USE_MQTT = False

# --- Nastaveni: chovani -------------------------------------------------------
PREHEAT_H        = 2      # kolik hodin dopredu se diva do profilu
BT7_MIN          = 43.0   # °C, pod tim vzdy Normal
BT6_MIN          = 42.0   # °C, pod tim vzdy Normal
DROP_MIN         = 2.0    # °C, minimalni pokles BT6 za hodinu, ktery se pocita jako odber
FALLBACK         = 1      # rezim pri vypadku dat
HW_REFRESH_H     = 6      # beze zmeny rezimu se zapise znovu nejdriv po tolika hodinach (EEPROM)

# Prahy ceny (stejna jednotka jako SPOT_ENTITY; vychozi hodnoty jsou pro Kc/kWh!)
PRICE_VERY_CHEAP = 0.0    # <= -> Luxury (zaporna/nulova cena)
PRICE_CHEAP      = 4.5    # <= -> aspon Normal
PRICE_NORMAL     = 6.0    # <= -> aspon Normal
PRICE_EXPENSIVE  = 8.0    # <= -> nejvys Normal; nad tim Economy (pokud neni velky odber)

SOLAR_VERY_CHEAP = 1500   # W
SOLAR_CHEAP      = 500    # W

MODE_NAMES = {0: "Economy", 1: "Normal", 2: "Luxury"}


def hour_of_week():
    now = datetime.now()
    return now.weekday() * 24 + now.hour

def get_float(entity_id):
    try:
        val = state.get(entity_id)
        if val in (None, "unavailable", "unknown", ""):
            return None
        return float(val)
    except (ValueError, TypeError, NameError):
        return None

def publish(kind, data, value):
    # kind: "status" | "diag" | "store" -> retained MQTT, nebo pyscript entita (USE_MQTT = False)
    if USE_MQTT:
        topic = {"status": STATUS_TOPIC, "diag": DIAG_TOPIC, "store": STORE_TOPIC}[kind]
        service.call("mqtt", "publish", topic=topic, payload=json.dumps(data), qos=1, retain=True)
    else:
        entity = {"status": STATUS_ENTITY, "diag": DIAG_ENTITY, "store": STORE_ENTITY}[kind]
        state.set(entity, value, new_attributes=data)

@time_trigger("startup")
def vv_ai_startup():
    if not USE_MQTT:
        # pyscript.* entity si HA pamatuje pres restart jen po state.persist
        state.persist(STORE_ENTITY)
        state.persist(STATUS_ENTITY)
        state.persist(DIAG_ENTITY)

def load_profile():
    try:
        st = state.get(STORE_ENTITY)
        if st in (None, "unavailable", "unknown"):
            log.info("VV-AI: profil uloziste nedostupne, zacinam s prazdnym")
            return _empty_profile()
        attrs = state.getattr(STORE_ENTITY)
        profile  = attrs.get("profile")
        counts   = attrs.get("counts")
        last_bt6 = attrs.get("last_bt6")
        last_hi  = attrs.get("last_hi")
        if (isinstance(profile, list) and len(profile) == 168 and
                isinstance(counts, list) and len(counts) == 168):
            return {"profile": list(profile), "counts": list(counts),
                    "last_bt6": last_bt6, "last_hi": last_hi}
        log.warning("VV-AI: profil ma spatny format, zacinam s prazdnym")
    except Exception as e:
        log.error(f"VV-AI: load_profile chyba ({e})")
    return _empty_profile()

def _empty_profile():
    return {"profile": [0.0]*168, "counts": [0]*168, "last_bt6": None, "last_hi": None}

def save_profile(prof):
    try:
        publish("store", prof, prof.get("last_bt6"))
        nonzero = len([v for v in prof['profile'] if v > 0])
        log.info(f"VV-AI: profil ulozen last_bt6={prof.get('last_bt6')} nonzero={nonzero}")
    except Exception as e:
        log.error(f"VV-AI: save_profile CHYBA ({e})")

def write_mode(mode):
    # Zapise rezim do cerpadla. Vraci False, kdyz entita uz rezim ma (nic se nezapsalo).
    if HW_WRITE != "entity":
        service.call("mqtt", "publish", topic=HW_TOPIC, payload=str(mode), qos=1, retain=False)
        return True
    domain = HW_ENTITY.split(".")[0]
    current = state.get(HW_ENTITY)
    if domain == "select":
        wanted = str(HW_OPTIONS[mode]).lower()
        options = (state.getattr(HW_ENTITY) or {}).get("options") or []
        match = [o for o in options if str(o).lower() == wanted]
        if options and not match:
            raise ValueError(f"{HW_ENTITY} nema moznost '{HW_OPTIONS[mode]}' (ma {options})")
        option = match[0] if match else HW_OPTIONS[mode]
        if str(current).lower() == wanted:
            return False
        service.call("select", "select_option", entity_id=HW_ENTITY, option=option)
    else:
        try:
            if float(current) == float(mode):
                return False
        except (ValueError, TypeError):
            pass
        service.call(domain, "set_value", entity_id=HW_ENTITY, value=mode)
    return True

def send_mode(mode, reason=""):
    # Rezim se zapisuje jen pri zmene (nebo jednou za HW_REFRESH_H hodin) – setri EEPROM.
    # Status (duvod) se publikuje vzdy.
    try:
        last_mode  = None
        last_write = 0.0
        try:
            attrs = state.getattr(STATUS_ENTITY) or {}
            last_mode  = attrs.get("mode")
            last_write = float(attrs.get("written") or 0)
        except Exception:
            pass
        now_ts = datetime.now().timestamp()
        if last_mode != mode or now_ts - last_write >= HW_REFRESH_H * 3600:
            try:
                if write_mode(mode):
                    log.info(f"VV-AI: -> {MODE_NAMES[mode]} ({reason})")
                last_write = now_ts
            except Exception as we:
                log.warning(f"VV-AI: zapis rezimu {MODE_NAMES[mode]} selhal ({we})")
                reason = f"ZAPIS SELHAL: {we} | {reason}"
                mode = last_mode if last_mode in MODE_NAMES else mode
        publish("status", {"mode": mode, "name": MODE_NAMES[mode],
                           "reason": reason, "written": last_write}, MODE_NAMES[mode])
    except Exception as e:
        log.warning(f"VV-AI: nelze odeslat mode {mode} ({e})")


@time_trigger("period(now, 1h)")
def vv_ai_learn():
    try:
        prof = load_profile()
        hi   = hour_of_week()
        bt6  = get_float(BT6_ENTITY)

        if bt6 is None:
            log.warning("VV-AI uceni: BT6 nedostupna, preskakuji")
            try:
                publish("diag", {"status": "bt6_none", "hi": int(hi)}, f"bt6_none:{hi}")
            except Exception as de:
                log.error(f"VV-AI: diag bt6_none CHYBA ({de})")
            return

        last_bt6 = prof.get("last_bt6")
        last_hi  = prof.get("last_hi")
        learned  = False

        # Odber = pokles BT6 od minule hodiny; slot drzi klouzavy prumer poklesu.
        # Uci se jen z navazujicich hodin (po vypadku HA by se pokles za vic hodin
        # pripsal jedne) a pokles patri hodine, ve ktere zacal (last_hi).
        if last_bt6 is not None and last_hi is not None and int(last_hi) == (hi - 1) % 168:
            slot = int(last_hi)
            drop = float(last_bt6) - bt6
            if drop >= DROP_MIN:
                n     = prof["counts"][slot] + 1
                old   = prof["profile"][slot]
                prof["profile"][slot] = old + (drop - old) / n
                prof["counts"][slot]  = n
                learned = True
                log.info(f"VV-AI uceni: slot {slot} pokles {drop:.1f}C prumer={prof['profile'][slot]:.1f}C n={n}")
        elif last_bt6 is not None and last_hi != hi:
            log.info(f"VV-AI uceni: mezera v datech (posledni slot {last_hi}, ted {hi}), neucim")

        prof["last_bt6"] = bt6
        prof["last_hi"]  = hi
        save_profile(prof)

        nonzero = len([v for v in prof["profile"] if v > 0])
        try:
            publish("diag", {
                "status": "ok",
                "hi": int(hi),
                "bt6": float(bt6),
                "last_bt6": float(last_bt6) if last_bt6 is not None else None,
                "learned": bool(learned),
                "nonzero_slots": int(nonzero),
            }, f"ok:{hi}")
        except Exception as de:
            log.error(f"VV-AI: diag ok CHYBA ({de})")

    except Exception as e:
        log.error(f"VV-AI uceni: neocekavana chyba ({e})")


@time_trigger("period(now, 15min)")
def vv_ai_control():
    try:
        bt7   = get_float(BT7_ENTITY)
        price = get_float(SPOT_ENTITY)

        if bt7 is None:
            send_mode(FALLBACK, "vypadek BT7"); return

        if bt7 < BT7_MIN:
            send_mode(1, f"BT7={bt7:.1f}C < min {BT7_MIN}C"); return

        bt6 = get_float(BT6_ENTITY)
        if bt6 is not None and bt6 < BT6_MIN:
            send_mode(1, f"BT6={bt6:.1f}C < {BT6_MIN}C -> Normal (studena nadrz)"); return

        # Nejvetsi ocekavany odber v teto a pristich PREHEAT_H hodinach
        prof     = load_profile()
        hi       = hour_of_week()
        max_drop = 0.0
        for offset in range(0, PREHEAT_H + 1):
            future_hi = (hi + offset) % 168
            if prof["profile"][future_hi] > max_drop:
                max_drop = prof["profile"][future_hi]

        if max_drop >= 8.0:   base_mode = 2
        elif max_drop >= 3.0: base_mode = 1
        else:                 base_mode = 0

        solar = get_float(SOLAR_ENTITY)
        if solar is not None and solar >= SOLAR_VERY_CHEAP:
            send_mode(2, f"FVE pretoky={solar:.0f}W >= {SOLAR_VERY_CHEAP}W -> Luxury"); return
        if solar is not None and solar >= SOLAR_CHEAP:
            mode = 2 if base_mode == 2 else 1
            send_mode(mode, f"FVE pretoky={solar:.0f}W >= {SOLAR_CHEAP}W -> {MODE_NAMES[mode]}"); return

        if price is None:
            mode   = base_mode if base_mode > 0 else FALLBACK
            reason = f"profil={max_drop:.1f}C, cena N/A"
        elif price <= PRICE_VERY_CHEAP:
            mode   = 2; reason = f"cena={price:.2f} zaporna/nulova -> Luxury"
        elif price <= PRICE_CHEAP:
            mode   = max(base_mode, 1); reason = f"cena={price:.2f} levna, profil={max_drop:.1f}C"
        elif price <= PRICE_NORMAL:
            mode   = max(base_mode, 1); reason = f"cena={price:.2f} normalni, profil={max_drop:.1f}C"
        elif price <= PRICE_EXPENSIVE:
            mode   = min(base_mode, 1); reason = f"cena={price:.2f} draha, max Normal"
        else:
            mode   = 0 if max_drop < 5.0 else 1
            reason = f"cena={price:.2f} velmi draha, profil={max_drop:.1f}C"

        send_mode(mode, reason)

    except Exception as e:
        log.error(f"VV-AI rizeni: neocekavana chyba ({e}) -> fallback Normal")
        send_mode(FALLBACK, f"chyba: {e}")
