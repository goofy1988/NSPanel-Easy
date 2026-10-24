# NSPanel-TFT-Design (Rounded 2)

## HMI bearbeiten ohne Nextion Editor: nxwright

`tools/nxwright/` ist ein Klon von https://github.com/nixiewright/nxwright (v0.1.0,
Commit 46f3eb4, geprüft am 24.10.2026) mit eigener venv. Nichts ist systemweit installiert.

```
tools\nxwright\.venv\Scripts\nxwright.exe dump  <projekt.HMI> <ordner>
tools\nxwright\.venv\Scripts\nxwright.exe write --overwrite <projekt.HMI> <ordner> <neu.HMI>
```

- Mit NSPanel-Easy-HMIs geht **nur `dump`/`write`**. `extract`/`build` brechen am Seiten-Header
  von `screensaver` ab.
- Im Dump steht je Seite eine `pages/NN-name.txt` mit allen Attributen und dem Event-Code.
  Bilder liegen als `images/NNNN.png`, die IDs lückenlos. Farben sind RGB565 als Dezimalzahl.
- Erlaubt sind: Attribute ändern, Objekte anlegen (eine bestehende Kopie mit neuer `id` und
  neuem `objname`, `endx`/`endy` = x+w-1 / y+h-1), Bilder ersetzen oder anhängen.
- Nach dem Umnummerieren rechnet nxwright die Verweise nicht um: `pic=`, `font=` und `page N`
  im Code müssen schon auf die neuen IDs zeigen.

## Regeln

- Die Arbeitsdatei `Rounded2Project\nspanel_landscape_v2026.10.7.HMI` nie überschreiben.
  Immer eine neue Datei daneben schreiben, Dom öffnet und kompiliert sie im Nextion Editor.
- Nach jedem `write` die neue Datei erneut dumpen und mit dem bearbeiteten Dump vergleichen.

## Skripte

- `tools/nx_home_apply.py <quelle.HMI> <ziel.HMI>` setzt `assets/` (Bilder 134–151) und
  `assets/positions.md` auf der Seite home um und prüft das Ergebnis.
  Ergebnis vom 24.10.: kompiliert mit 0 Fehlern.
- `tools/nx_pages_apply.py <quelle.HMI> <ziel.HMI>` setzt `pages_assets.py` um: Bild 0 schwarz,
  46/47 Button-Karten, 152/153 Hintergrund notification/qrcode (dort im Event-Code statt
  `pic_background_main`, also nur Dark-Theme) und die Positionen aus `assets/pages_positions.json`.
  Braucht eine HMI mit Bild 151 (Rev 14), weil die Bild-IDs lückenlos sein müssen.
  154 = Seitenhintergrund buttonpage01-04 mit Zurück-Kreis (statische Dark-Attribute, der Event-Code
  setzt Bilder dort nur im Light-Theme). Icons sitzen in Kreisen: aus grau (46), an blau mit blauem
  Rand (47). Die Kreisfarbe steckt im Bild, ist also nicht je Gerät wählbar. Notification: Pillen mit getöntem Kreis (Icon = `txt` von bt_accept/bt_clear in Font 8,
  linksbündig), „Gelesen“/„Löschen“ ist in Bild 152 eingebacken. Ergebnis 24.10.:
  `Rounded2Project\nspanel_landscape_v2026.10.7_rounded2g.HMI`.
- `tools/nx_slim_apply.py <quelle.HMI> <ziel.HMI>` (nach nx_pages_apply): Fonts 0–4 nur noch
  Latein/Griechisch/Kyrillisch/U+2000–2BFF (1246 statt 10569 Zeichen, ~4,6 MB weniger), 27 Bilder
  des Light-Themes auf 1×1 (~1,8 MB). IDs bleiben. Encoder-Round-Trip war byte-identisch.
  Kette 24.10.: `_rounded2d` → nx_pages_apply → `_rounded2g` → nx_slim_apply → `_rounded2h.HMI`; 24.10. abends `_rounded2i.HMI` (Zurück-X, Haken, Kreuz ins Bild gebacken).
  🔴 Danach kein Light-Theme und keine CJK/Arabisch/Thai-Sprachen mehr.
- `home_assets.py` / `rounded2_patch.py` erzeugen die Assets (aus dem Design-Chat).
  Die Vorschau `assets/preview.png` zeichnet Texte und Icons mit den echten Fonts aus `fonts_dump/`
  (= `fonts/` eines Dumps; nach Font-Änderungen in der HMI neu kopieren).
- `tools/font_text_width.py`: Breite eines Textes in einem Panel-Font. Ein Text, der nicht in seine
  Box passt, verliert beim Nextion ganze Zeichen.
- `tools/font_glyph_check.py`: wie MDI-Glyphen in Font 7/8 sitzen. Alle liegen 1,5–2,5 px zu tief,
  deshalb liegen die Icon-Bauteile 2 px höher (`ICON_DY`). `tools/icon_compare.py` vergleicht Icons im Kachelkreis.

## Was die Firmware erledigt (kein Event-Code in der HMI nötig)

Patch `rounded2_patch.py`, auf dem Fork `goofy1988/NSPanel-Easy`, Branch `rounded2`:

- **Bild 150:** Aktive HW-Taste = ganze Pille. Die Firmware kopiert sie per `xpic` aus 150
  (an) bzw. `home.pic` (aus) und zeichnet die Beschriftung danach neu (Patch 7).
  🔴 Nie `home.pic=150` setzen, das tauscht den ganzen Seitenhintergrund.
- **Timer (Patch 10, `rounded2_patch10.py`, nach `rounded2_patch.py` ausführen):** API-Action
  `timer_set(state, remaining)`, Blueprint `blueprints/rounded2_panel_timer.yaml` im Fork,
  Script `script.timer_voice_stop` für den Voice-Intent. Plan und Verhalten: `timer_patch10_plan.md`.
- **Bild 151:** home mit roter Uhrkarte, für den abgelaufenen Timer (Patch 10). Die Firmware
  blinkt per `xpic` zwischen 151 und `home.pic` und setzt dabei `picc` der Bauteile in der Uhrkarte.
  `time` hat `txt_maxl` 8 für „12:05 h“ (`EXTRA_ATTRS` in `nx_home_apply.py`).
- **`value0X_label`:** HA liefert „Wert|Beschriftung“, die Firmware teilt das auf (Patch 6).
- **`left_bt_text`/`right_bt_text`:** werden nicht genutzt. Die Beschriftungen zeichnet die
  Firmware per `xstr` direkt. Deshalb sind sie geparkt.
- **`bt_notific` (Glocke):** 414/109, unten in der rechten Spalte der Wetterkarte. Das ist ein
  MDI-Glyph, kein Bild. Die Firmware gibt ihm die Chip-Schrift (Patch 8), die Farben für
  gelesen/ungelesen kommen aus dem Blueprint.
- **`bt_qrcode`:** 209/274, 37×37 (von Dom festgelegt, 1 px unter `ICON_DY`) im Kreis zwischen den Pillen. Es ist nur sichtbar, wenn ein QR-Wert
  konfiguriert ist.
- **Geparkt bei x 456:** `bt_icon` (nur bei BLE-Firmware sichtbar), `bt_entities`, `bt_utilities`,
  `button01`–`07`, `meridiem`, `left_bt_text`, `right_bt_text`, `chip04`–`07` (je 18 px hoch).
  Dieser Streifen liegt hinter dem Rahmen. Soll eins davon zurück, in `home_assets.py` die Liste
  `PARKED` ändern und neu erzeugen.
- 🔴 Nie zwei Bauteile übereinanderlegen. Beim Neuaufbau der Seite (nach dem Bildschirmschoner)
  malt der Nextion sie in ID-Reihenfolge, ein leeres Bauteil übermalt das darunter. So
  verschwanden die Chips, als chip04–07 deckungsgleich auf Platz 1–4 lagen.
- Ergebnis 24.10. (Rev 14): `Rounded2Project\nspanel_landscape_v2026.10.7_rounded2d.HMI`. Nur die
  Seite home ist geändert, Pillen 10–191 / 262–443, Kreis 202–251.
- **Button-Beschriftung (Patch 13, `rounded2_patch13.py`):** Der Nextion richtet mehrzeiligen Text
  als Block aus, nicht je Zeile. Die Firmware rückt kürzere Zeilen mit Leerzeichen ein, deshalb
  `txt_maxl` 40 an `buttonNNtext`.
- Icons allein im Kreis (Zurück, QR-Kopf, `bt_qrcode`) sitzen mit `ICON_DY + 1` mittig.
- **Speicher:** TFT 16,1 MB bei 16 MB Display-Flash. Fonts 0–4 machen ~5,5 MB aus, ~88 % davon
  CJK/Hangul/Arabisch/Thai. nxwright kann Fonts kodieren (`zi_font.encode_font`).
- Die Blueprint-Eingabe `home_outdoor_temp_font` muss `6` sein, sonst setzt der Blueprint die Schrift
  der Außentemperatur zurück.
