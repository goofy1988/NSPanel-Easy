# Timer auf der Uhrkarte: Plan (Patch 10 + Blueprint)

Stand 24.10.2026. Die HMI ist vorbereitet (Rev 14): Bild 151 (rote Uhrkarte), `time.txt_maxl` 8.

## Fundstellen in 10.7

- Uhrzeit/Datum: `esphome/nspanel_esphome_datetime.yaml`, Script `refresh_datetime`.
  Es setzt `home.time` (Zeile ~79) und ruft `render_date("home.date", …)`. Es läuft jede Minute
  (`new_minute`) und bei `resync_display`. Den Bildschirmschoner-Text (`text`) nicht anfassen.
- Touch: `nspanel_esphome_hw_display.yaml`, `disp1.on_touch` (Zeile ~103) mit `page_id`,
  `component_id` und `touch_event` (1 = gedrückt, 0 = losgelassen).
  Auf home ist `time` die ID 3, `date` die ID 6. Beide haben `sendkey = 3`.
- Langer Druck öffnet die Einstellungen über das HMI-Timer-Bauteil `settings_timer` (ID 34,
  `tim` 1000, Ereignis `page settings`). `time`/`date` setzen down `en=1`, up `en=0`.
- HA-Events: `fire_ha_event(type, {...})` aus `components/nspanel_easy/base.h` sendet
  `esphome.nspanel_easy` (mit Gerätename).

## Firmware (Patch 10, nur unter `#ifdef`, damit andere Panels unverändert bleiben)

- API-Action `timer_set(state: string, remaining: int)`:
  - `active`: Sekunden lokal herunterzählen (`interval` 1 s), Anzeige an.
  - `paused`: Restzeit stehen lassen, Datumszeile „Timer pausiert“.
  - `idle`: Timer-Modus aus, Alarm aus, normale Uhrzeit (`refresh_datetime`).
  - `finished`: Alarm starten (auch wenn lokal schon 0 erreicht ist, nur einmal).
- Anzeige: unter 1 h „M:SS“, ab 1 h „H:MM h“. Ab 10 h passt „23:59 h“ (214 px) nicht in 170 px,
  dann Font 5, sonst Font 6 (wie `home_outdoor_temp_apply_font`). Datumszeile „Timer“,
  „Timer pausiert“, „Abgelaufen“.
- `refresh_datetime`: `home.time`/`home.date` nicht schreiben, solange die Timer-Ansicht aktiv ist.
- Kurzer Tipp auf `time`/`date` (losgelassen nach < 800 ms): Wechsel Uhrzeit ↔ Timer-Ansicht
  (nur wenn ein Timer läuft oder pausiert).
- Langer Druck (≥ 800 ms, selbst gemessen, Wiederholung abbrechen beim Loslassen): `fire_ha_event("timer",
  {{"action","stop"}})`. Damit der lange Druck nicht die Einstellungen öffnet:
  im Timer-Modus `home.settings_timer.tim=65000` setzen, bei jedem Laden von home erneut
  (lokale Variable, `vscope` 0), danach zurück auf 1000.
- Alarm: Display wecken, auf home wechseln, 1 min lang alle 500 ms blinken:
  `xpic 10,10,212,140,10,10,151` bzw. `home.pic`, dazu `picc` = 151/134 für `time`, `date`,
  `chip_relay1`, `chip_relay2`, `chip_climate`, `chip01` und deren Text neu setzen. Text bleibt weiß.
  Jeder Tipp aufs Panel oder `timer_set(idle)` beendet den Alarm und sendet `action: stop`
  (nur beim Tipp). Nach 1 min: Alarm aus, „0:00“/„Abgelaufen“ bleibt nicht stehen, normale Uhr.
- Summer: vorerst nicht (Option für später).

## HA

- Blueprint „Rounded 2 Panel-Timer“: Eingaben Timer-Entität (Standard `timer.timer_voice`) und
  Panels (ESPHome-Geräte).
  - Trigger: `timer.started/restarted/paused/cancelled/finished` für die Entität,
    `esphome.nspanel_easy` mit `type: timer`, Event `rounded2_timer_stop`, Panel wird verfügbar.
  - Restzeit aus `finishes_at` − jetzt (aktiv) bzw. `remaining` (pausiert) in Sekunden.
  - `action: stop` vom Panel: `timer.cancel`, dann `timer_set(idle)` an alle Panels.
- Script `script.timer_voice_stop` für Doms Intent: bei aktiv/pausiert `timer.cancel`, immer das
  Event `rounded2_timer_stop` feuern (nach dem Ablauf ist der Timer schon `idle`).
- Hinweis: `timer.timer_voice` hat das Attribut `last_transition` (Stand 24.10. `null`), evtl.
  `finished` nach Ablauf. Vor dem Bau prüfen, ob es sich als Resync beim Panel-Neustart eignet.
