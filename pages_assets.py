"""Rounded 2 / Graphit fuer die Seiten buttonpage01-04, notification und qrcode (Dark-Theme).

Erzeugt in C:\\Users\\dom\\nspanel_tft\\assets\\:
  page_bg_0.png            Bild 0 = pic_background_main (Dark): schwarz, ohne Welle
  buttons_off_46.png       Button-Seiten: Karten aus (Firmware schneidet per picc aus Bild 46)
  buttons_on_47.png        dasselbe gedrueckt/an (Bild 47): blauer Rand + Toenung, Icon-Kreise grau bzw. blau
  notification_152.png     Hintergrund der Seite notification (Textkarte + zwei Pillen mit Kreis, Beschriftung eingebacken)
  qrcode_153.png           Hintergrund der Seite qrcode (weisses Feld um den Code)
  buttonpage_154.png       Seitenhintergrund buttonpage01-04 (schwarz + Zurueck-Kreis)
  preview_buttons.png, preview_notification.png, preview_qrcode.png   Vorschau (2x)
  pages_positions.json     Bauteil-Positionen je Seite fuer tools/nx_pages_apply.py

Raster wie home (home_assets.py): Rand 10, Abstand 10, Karten 10..444, sichtbar x 0..455.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home_assets as ha  # noqa: E402
from home_assets import C, ICON, nx_text, shot, tint, CSS_VARS, OUT  # noqa: E402
from PIL import Image  # noqa: E402

NOTIFY_SLOT, QR_SLOT, BTNPAGE_SLOT = 152, 153, 154
GRID_X = [10, 121, 232, 343]          # wie die Home-Kacheln
CARD_W = 101
ROW_Y, CARD_H = [52, 177], 115        # zwei Reihen, Abstand 10, unten bleibt Platz fuer page_index
HEADER = dict(title=(22, 10, 300, 30), back=(406, 7, 36, 36))     # back = Kreis, Icon darin
ICON_DY = ha.ICON_DY
# Einzel-Icons in Kreisen (Zurueck, QR-Kopf): am Panel sitzt das X mit ICON_DY 1 px zu hoch, wie bt_qrcode auf home
CIRCLE_DY = ICON_DY + 1
BACK_COL = "p_blue"                   # Zurueck-Kreis und aktive Buttons: blau (universell, nicht geraeteabhaengig)
ON_COL = "p_blue"
OFF_CIRCLE = "c10"                    # Kreis hinter dem Icon, wenn aus: neutral grau

# Button-Karte, alles mittig: Icon im Kreis oben, Name (bis 2 Zeilen, Firmware bricht nach 10 Zeichen um), Helligkeit
def button_parts(x, y):
    return {"pic": (x, y, CARD_W, CARD_H),
            "circle": (x + 28, y + 10, 44, 44),
            "icon": (x + 28, y + 10 + ICON_DY, 44, 44),
            "text": (x + 4, y + 58, CARD_W - 8, 34),
            "bri": (x + 4, y + 92, CARD_W - 8, 18)}

BUTTONS = [button_parts(x, y) for y in ROW_Y for x in GRID_X]

NOTE_CARD = (10, 50, 434, 182)
NOTE_PILLS = [(10, 244, 212, 64), (232, 244, 212, 64)]
# Pillen wie auf home: getoenter Kreis mit Icon links, Beschriftung daneben (ins Bild 152 gebacken)
NOTE_BTN = [("bt_accept", "p_green", "check-bold", "Gelesen"), ("bt_clear", "p_red", "close-thick", "Löschen")]


def note_circle(pill):
    x, y, w, h = pill
    return (x + 10, y + 10, h - 20, h - 20)


def ink_width(icon, fid=8):
    """Linksbuendig beginnt die Glyphe ohne Rand am Bauteil-x, also Breite der Tinte messen."""
    im = Image.new("RGB", (100, 60))
    nx_text(im, ICON[icon], (0, 0, 100, 60), fid, "#ffffff", 0, 1)
    return im.getbbox()[2]


def note_button(pill, icon):
    """Bauteil ueber die ganze Pille (Touch), Icon linksbuendig mittig im Kreis."""
    x, y, w, h = pill
    cx, cy, cw, ch = note_circle(pill)
    ix = cx + (cw - ink_width(icon)) // 2
    return (ix, y + 4 + ICON_DY, x + w - 8 - ix, h - 8)


QR_ICON = (12, 7, 36, 36)             # Kreis links im Kopf der QR-Seite
QR_BOX = (127, 81, 200, 200)          # weisses Feld mittig in der Karte 10,50,434,262, Code 180 x 180 darin


def page(parts):
    return f'''<!doctype html><html><head><meta charset="utf-8">
<style>:root{{{CSS_VARS}}}*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:480px;height:320px;overflow:hidden;background:var(--bg)}}
.card{{position:absolute;background:var(--card);border:2px solid var(--c6);border-radius:16px}}
</style></head><body>{"".join(parts)}</body></html>'''


def card(box, extra="", radius=16):
    x, y, w, h = box
    return (f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'border-radius:{radius}px;{extra}"></div>')


ON = f"border-color:var(--{ON_COL});background:{tint(ON_COL, 14)};"


def circle(box, col, pct=ha.CIRCLE_TINT):
    x, y, w, h = box
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'border-radius:50%;background:{tint(col, pct)}"></div>')


BACK = circle(HEADER["back"], BACK_COL)


def rgb565(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def positions():
    """name: (x, y, w, h, font, xcen, ycen) je Seite; None = Attribut bleibt."""
    bx, by, bw, bh = HEADER["back"]
    back = (bx, by + CIRCLE_DY, bw, bh, 8, 1, 1)
    btn = {"page_label": (*HEADER["title"], 3, 0, 1), "button_back": back,
           "page_index": (177, 294, 100, 20, 9, 1, 1)}
    for i, b in enumerate(BUTTONS, 1):
        n = f"button{i:02d}"
        btn[n + "pic"] = (*b["pic"], None, None, None)
        btn[n] = (*b["pic"], None, None, None)                   # Touch-Flaeche
        btn[n + "icon"] = (*b["icon"], 8, 1, 1)
        btn[n + "text"] = (*b["text"], 0, 1, 1)
        btn[n + "bri"] = (*b["bri"], 0, 1, 1)
    x, y, w, h = NOTE_CARD
    note = {"notifi_label": (*HEADER["title"], 3, 0, 1), "button_back": back,
            "notifi_text01": (x + 12, y + 10, w - 24, h - 20, 3, 1, 1),
            **{n: (*note_button(p, ic), 8, 0, 1) for p, (n, _, ic, _) in zip(NOTE_PILLS, NOTE_BTN)}}
    qx, qy, qw, qh = QR_BOX
    qr = {"icon_state": (QR_ICON[0], QR_ICON[1] + CIRCLE_DY, *QR_ICON[2:], 8, 1, 1),
          "page_label": (56, 10, 300, 30, 3, 0, 1), "button_back": back, "qr": (qx + 10, qy + 10, 180, 180, None, None, None)}
    return {"buttonpage": btn, "notification": note, "qrcode": qr}


# Attribute ausser Position/Font (RGB565): Pillen der Benachrichtigung in der Panel-Palette
def nx_txt(text):
    return '"' + "".join(c if ord(c) < 128 else "".join(f"\\x{b:02x}" for b in c.encode()) for c in text) + '"'


# Buttons (Typ 98) malen das Glyphen-Rechteck ueber dem Crop-Bild heller als den Kreis (am Panel ein
# helles Quadrat hinter dem X). Deshalb sind X, Haken und Kreuz ins Bild gebacken, txt bleibt leer.
EXTRA = {"notification": {n: {"txt": '""'} for n, _, _, _ in NOTE_BTN}}
# Platz fuer die Einrueck-Leerzeichen der Firmware (Patch 13), vorher 22
EXTRA["buttonpage"] = {f"button{i:02d}text": {"txt_maxl": 40} for i in range(1, len(BUTTONS) + 1)}
for kind in ("buttonpage", "notification", "qrcode"):
    EXTRA.setdefault(kind, {})["button_back"] = {"txt": '""'}
# Event-Code: der Zurueck-Pfeil bekommt die Kreisfarbe statt color_pco_navigation (nx_pages_apply ersetzt das)
BACK_PCO = rgb565(C[BACK_COL])


def bake_icon(path, icon, box, col):
    """Glyphe aus Font 8 mit der Tinte genau mittig in den Kreis `box` ins Bild malen."""
    probe = Image.new("RGB", (100, 100))
    nx_text(probe, ICON[icon], (0, 0, 100, 100), 8, "#ffffff", 0, 0)
    l, t, r, b = probe.getbbox()
    x, y, w, h = box
    ox = x + (w - (r - l)) / 2 - l
    oy = y + (h - (b - t)) / 2 - t
    im = Image.open(path).convert("RGB")
    nx_text(im, ICON[icon], (round(ox), round(oy), 100, 100), 8, C[col], 0, 0)
    im.save(path)


def draw(im, layout, sample, cols):
    """Mehrzeilig wie der Nextion: Zeilen dicht untereinander, der Block mittig in der Box."""
    for name, text in sample.items():
        x, y, w, h, fid, xcen, ycen = layout[name]
        lines = text.split("\n")
        lh = ha.font(fid).height
        top = y + (h - lh * len(lines)) // 2 if ycen == 1 else y
        for k, line in enumerate(lines):
            nx_text(im, line, (x, top + k * lh, w, lh), fid, cols.get(name, C["c20"]), xcen, 1)


if __name__ == "__main__":
    tmp = os.path.join(OUT, "_pg.png")
    Image.new("RGB", (480, 320), (0, 0, 0)).save(os.path.join(OUT, "page_bg_0.png"))
    shot(page([BACK] + [card(b["pic"]) + circle(b["circle"], OFF_CIRCLE) for b in BUTTONS]),
         os.path.join(OUT, "buttons_off_46.png"))
    shot(page([BACK] + [card(b["pic"], ON) + circle(b["circle"], ON_COL) for b in BUTTONS]),
         os.path.join(OUT, "buttons_on_47.png"))
    shot(page([BACK]), os.path.join(OUT, f"buttonpage_{BTNPAGE_SLOT}.png"))
    shot(page([BACK, card(NOTE_CARD)] + [card(p, radius=p[3] // 2) + circle(note_circle(p), b[1])
                                         for p, b in zip(NOTE_PILLS, NOTE_BTN)]),
         os.path.join(OUT, f"notification_{NOTIFY_SLOT}.png"))
    im = Image.open(os.path.join(OUT, f"notification_{NOTIFY_SLOT}.png")).convert("RGB")
    for (x, y, w, h), (_, _, _, label) in zip(NOTE_PILLS, NOTE_BTN):
        nx_text(im, label, (x + h, y, w - h - 16, h), 3, C["c20"], 1)
    im.save(os.path.join(OUT, f"notification_{NOTIFY_SLOT}.png"))
    qx, qy, qw, qh = QR_BOX
    shot(page([BACK, circle(QR_ICON, "p_blue"), card((10, 50, 434, 262)),
               f'<div style="position:absolute;left:{qx}px;top:{qy}px;width:{qw}px;height:{qh}px;'
               f'background:#fff;border-radius:16px"></div>']), os.path.join(OUT, f"qrcode_{QR_SLOT}.png"))
    for slot in (f"buttonpage_{BTNPAGE_SLOT}", f"notification_{NOTIFY_SLOT}", f"qrcode_{QR_SLOT}"):
        bake_icon(os.path.join(OUT, slot + ".png"), "close", HEADER["back"], BACK_COL)
    for pill, (_, col, ic, _) in zip(NOTE_PILLS, NOTE_BTN):
        bake_icon(os.path.join(OUT, f"notification_{NOTIFY_SLOT}.png"), ic, note_circle(pill), col)
    pos = positions()
    json.dump({"positions": pos, "extra": EXTRA, "back_pco": BACK_PCO}, open(os.path.join(OUT, "pages_positions.json"), "w"), indent=1)

    # Vorschau Button-Seite: 1 und 6 an (Bild 47), Rest aus (46), 8 nicht belegt
    off = Image.open(os.path.join(OUT, "buttons_off_46.png"))
    on = Image.open(os.path.join(OUT, "buttons_on_47.png"))
    im = Image.open(os.path.join(OUT, f"buttonpage_{BTNPAGE_SLOT}.png")).convert("RGB")
    lay = pos["buttonpage"]
    names = ["Decke", "Esstisch", "LED Leiste", "Spots", "Kaffee", "Trigger\nGaragentor", "Radio", None]
    icons = ["ceiling-light", "lamp", "led-strip-variant", "spotlight-beam", "coffee-maker", "garage",
             "radio", None]
    bris = ["80%", "", "", "", "", "", "", ""]
    for i, (n, ic) in enumerate(zip(names, icons), 1):
        if n is None:
            continue
        x, y, w, h = BUTTONS[i - 1]["pic"]
        im.paste((on if i in (1, 6) else off).crop((x, y, x + w, y + h)), (x, y))
        k = f"button{i:02d}"
        col = C[ON_COL] if i in (1, 6) else C["c14"]
        draw(im, lay, {k + "icon": ICON[ic]}, {k + "icon": col})
        draw(im, lay, {k + "text": n, k + "bri": bris[i - 1]}, {k + "bri": C["c14"]})
    draw(im, lay, {"page_label": "Buttons"}, {})
    im.resize((960, 640), Image.NEAREST).save(os.path.join(OUT, "preview_buttons.png"))

    im = Image.open(os.path.join(OUT, f"notification_{NOTIFY_SLOT}.png")).convert("RGB")
    lay = pos["notification"]
    draw(im, lay, {"notifi_label": "Waschmaschine",
                   "notifi_text01": "Die Wäsche ist fertig.\nBitte ausräumen."},
         {"notifi_label": C["c14"]})
    im.resize((960, 640), Image.NEAREST).save(os.path.join(OUT, "preview_notification.png"))

    im = Image.open(os.path.join(OUT, f"qrcode_{QR_SLOT}.png")).convert("RGB")
    lay = pos["qrcode"]
    draw(im, lay, {"icon_state": ICON["wifi"], "page_label": "Gäste Wifi"}, {"icon_state": C["p_blue"]})
    x, y, w, h = lay["qr"][:4]
    qr = Image.new("RGB", (w, h), (255, 255, 255))
    for r in range(0, h, 12):
        for c in range(0, w, 12):
            if (r * 7 + c * 13) % 5 < 2:
                qr.paste((0, 0, 0), (c, r, c + 12, r + 12))
    im.paste(qr, (x, y))
    im.resize((960, 640), Image.NEAREST).save(os.path.join(OUT, "preview_qrcode.png"))
    os.remove(os.path.join(OUT, "_tmp.html"))
    print("ok")
