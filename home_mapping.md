# NSPanel Easy – Home-Seite: Entwurf → echte Bauteile

Basis: **v2026.9.14** (läuft auf allen 5 Panels, `min_tft_version` 21.2).
HMI: `C:\Users\dom\nspanel_tft\nspanel_landscape_v2026.9.14.HMI` (EU = landscape)
Text-Dump: `v2026.9.14_home.txt`, Upstream-Quellen: `easy_src\` (Tag v2026.9.14)

## Was fest im Firmware-Code steckt (nicht verschiebbar)

| Element | Wo | Folge |
|---|---|---|
| Tastenleisten links/rechts | `disp1->fill_area(47..167 / 288..408, y 312–315)` in `nspanel_esphome_hw_buttons.yaml` | Leiste bleibt 3 px Strich bei y 312. Pille im Hintergrund drumherum zeichnen, Leiste = Unterstrich |
| Hintergrund aller Seiten | Bild-Slot **0** (`pic_background_main=0`), alle Textfelder „crop image“ aus Slot 0 | Kacheln NICHT in Slot 0 malen (sonst auf jeder Seite) → Home bekommt eigenen, neu angehängten Slot |
| Wetterbild | Picture `weather` (ID 7), 100×100, Slots 1–15 (dark) | Icons müssen opak auf Kachelfarbe gerendert werden, Größe 100×100 bleibt |

## Bauteile der Home-Seite (alle Text, Fill = crop image)

| Bauteil | heute x,y,w,h | Font | Entwurf |
|---|---|---|---|
| `time` | 246,45,168,62 | 6 (Sarasa 72) | Uhr-Kachel, groß |
| `date` | 121,110,293,30 | 3 (26) | unter der Uhr |
| `meridiem` | 414,92,40,20 | 2 | unbenutzt (24 h) |
| `outdoor_temp` | 120,45,125,65 | 4 (36) | Wetter-Kachel, neben Icon |
| `weather` (Bild) | 20,45,100,100 | – | Wetter-Kachel; ggf. kleiner nur mit neuen Bildern |
| `indr_temp` / `indr_temp_icon` | 50,150 / 15,150 | 4 / 8 | Wetter-Kachel unten („21,4°“) |
| `value01..03` + `_icon` | 42,196/224/252 · 150×25 | 3 / 7 | Kacheln 1–3 (PV, Einspeisung, Müll) |
| `value04` + `_icon` | 303,2 · 119×30 / 422,2 | 3 / 7 | Kachel 4 (Warmwasser) |
| `chip_relay1/2`, `chip_climate`, `chip01..07` | Reihe y 2, x 13…274, je 30×30 | 7 (MDI) | Uhr-Kachel oben; Chips 01/02 = Lüfter/Post |
| `wifi_icon`, `bt_icon` | 422,62 / 422,32 | 7 | Uhr-Kachel oben, dezent |
| `left_bt_text` / `right_bt_text` | 47,288 / 288,288 · 120×20 | 1 (18) | in den Pillen |
| `bt_qrcode` | 305,230 · 45×42 | 8 | zwischen den Pillen |
| `bt_notific`, `bt_utilities`, `bt_entities`, `button01..07` | rechte Hälfte | 8 | bei eg_f unbenutzt → aus dem Sichtfeld schieben, nicht löschen |

**Nicht vorhanden:** Wetter-Zustand als Text („Regen“), zweite Zeile je Slot.
→ Statisch im Hintergrund: „Trittau“, Kachel-Beschriftungen, Icon-Kreise, graue Chip-Silhouetten.

## Fonts (in allen Seiten genutzt)

0 Sarasa 16 · 1 Sarasa 18 · 2 Sarasa 22 · 3 Sarasa 26 · 4 Sarasa 36 · 5 Sarasa 48 (limited) · 6 Sarasa 72 (limited)
7/8 = SarasaGothicSC 24/32 **mit MDI-Icons** – nicht anfassen.
Inter: 0–6 durch Inter in **gleicher Höhe und gleichem Zeichensatz** ersetzen (sonst verrutschen andere Seiten).

## Bild-Pipeline (upstream)

`hmi/dev/pics/generate_images.sh` + `mapping.yaml`: setzt alle Icons/Buttons opak auf den Hintergrund
(Slot 0) und schreibt `landscape/<slot>.png`. Neuer Hintergrund → alle Slot-Bilder neu erzeugen →
im Editor per „Replace“ an gleicher Stelle tauschen (Indizes bleiben gleich).
