"""NSPanel Easy Home-Seite im Rounded-2-Stil: Assets fuer den Nextion Editor.

Erzeugt in C:\\Users\\dom\\nspanel_tft\\assets\\:
  home_bg_134.png          Home-Hintergrund 480x320 (neuer Bild-Slot 134)
  home_on_150.png          dasselbe mit aktiven Pillen (Patch 7 kopiert die Pille per xpic)
  home_alarm_151.png       dasselbe mit roter Uhrkarte (abgelaufener Timer, Patch 10)
  home_wx_<slot>.png       15 Wetter-Icons, deckend aus dem Hintergrund geschnitten (Slots 135-149)
  preview.png              Vorschau mit Beispielwerten (2x), Texte und Icons mit den echten Panel-Fonts
  positions.md             Bauteil-Liste fuer den Editor (x, y, w, h, Font, Farbe RGB565)

Alle Koordinaten stehen nur in LAYOUT; Hintergrund, Icons, Vorschau und Liste lesen von dort.
"""
import colorsys, io, json, os, re, subprocess, sys
from PIL import Image

sys.path.insert(0, r"C:\Users\dom\nspanel_tft\tools\nxwright")
from nxwright.project.zi_font import decode_font  # noqa: E402

OUT = r"C:\Users\dom\nspanel_tft\assets"
FONTS = r"C:\Users\dom\nspanel_tft\fonts_dump"      # die .zi-Fonts der HMI (nxwright dump)
ICON_CODES = r"C:\Users\dom\nspanel_tft\easy_src_10.7\docs\icons\all_icons.json"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
os.makedirs(OUT, exist_ok=True)
icons = json.load(open(r"C:\Users\dom\wetter_icons.json", encoding="utf-8"))

C = dict(bg="#000000", card="#14171D", c6="#303339", c10="#74777F", c14="#B7BBC2",
         c16="#D4D7E0", c20="#F9FCFF", red="#FDA19A", orange="#F5AB77",
         yellow="#FCC364", green="#89D298", blue="#92C1FD", purple="#D6A9F1")


# Rev 13: Das Panel waescht Pastelltoene aus (Foto 24.10.: Orange wirkt fast weiss).
# Fuer Icons, Kreise und Wetterbilder gilt deshalb eine kraeftigere Panel-Palette;
# die Textfarben (c-Toene) bleiben.
def vivid(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, max(0.5, l - 0.14), min(1.0, s * 1.15 + 0.1))
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in (r, g, b))


ACCENTS = ("red", "orange", "yellow", "green", "blue", "purple")
for k in ACCENTS:
    C["p_" + k] = vivid(C[k])
WX_SATURATE = 1.6      # CSS-Filter nur auf das Wetter-SVG, der Kartenhintergrund bleibt unberuehrt
CIRCLE_TINT = 36       # Kreis hinter den Kachel-Icons (vorher 28 %)

BG_SLOT = 134          # neuer Home-Hintergrund (Liste endet in 10.7 bei 133)
ON_SLOT = 150          # Home-Hintergrund mit aktiven Pillen (Patch 7 kopiert die Pille per xpic)
ALARM_SLOT = 151       # Home-Hintergrund mit roter Uhrkarte: abgelaufener Timer blinkt (Patch 10)
ALARM_TINT = 22        # Toenung der Uhrkarte im Alarm, Rand in p_red
WX_OFFSET = BG_SLOT    # Home-Wetterbild = Legacy-Dark-Slot (1..15) + 134 -> 135..149

# Raster: Rand 10, Abstand 10, Innenabstand P = 12 in jeder Karte.
# Nextion-Fonts = Sarasa: 0:16 1:18 2:22 3:26 4:36 5:48 6:72, 7 = Icons 24, 8 = Icons 32.
# Sichtbar ist nur x 0-455 (Overscan rechts ~25 px, am Foto 23.10. an den HW-Leisten gemessen)
P = 12
CARDS = dict(clock=(10, 10, 212, 140), weather=(232, 10, 212, 140))
TILE_X = [10, 121, 232, 343]
TILE_Y, TILE_W, TILE_H = 160, 101, 98
TILES = [("value01", "yellow"), ("value02", "green"), ("value03", "orange"), ("value04", "blue")]
TILE_PX = 10                                             # seitlicher Innenabstand der Kacheln
CAPTION_Y = TILE_Y + 76                                  # unter dem Wert, 8 px Rand unten
# Rev 13: Pillen buendig mit den Kartenkanten (10 / 444), dazwischen ein fester Kreis (QR-Knopf)
ROW_Y, ROW_H = 268, 50
CIRCLE = (227 - ROW_H // 2, ROW_Y, ROW_H, ROW_H)          # 202..252, Mitte des Rasters 10..444
PILLS = [(10, ROW_Y, CIRCLE[0] - 10 - 10, ROW_H), (CIRCLE[0] + ROW_H + 10, ROW_Y, 444 - CIRCLE[0] - ROW_H - 10, ROW_H)]
HW_LABELS = [(x + (w - 120) // 2, 280, 120, 24) for x, y, w, h in PILLS]   # Firmware zeichnet 120 breit mittig
HW_BARS = [(47, 312, 120, 3), (288, 312, 120, 3)]        # nur andere Seiten (hardware.h), home zeigt Pillen

CR = CARDS["clock"][0] + CARDS["clock"][2] - P           # rechte Kante Uhrkarte
WX_L = CARDS["weather"][0] + P                           # linke Kante Wetterkarte
WR = CARDS["weather"][0] + CARDS["weather"][2] - P       # rechte Kante Wetterkarte

# Icon-Font 7/8: die Glyphen sitzen 1,5-2,5 px unter der Zellmitte (tools/font_glyph_check.py).
# Alle Icon-Bauteile liegen deshalb 2 px hoeher als ihr Platz; Kreise im Hintergrund bleiben.
ICON_DY = -2

# Chips als Spalte rechtsbuendig, zuerst in der Uhrkarte (4), dann in der Wetterkarte (2).
# Bauteile duerfen sich nicht ueberlappen: ein leeres Text-Bauteil zeichnet trotzdem seinen Hintergrund.
CHIP_STEP = 29                                           # 4 x 24 + 3 x 5 = 111 px, mittig in der Karte
CHIP_Y0 = CARDS["clock"][1] + (CARDS["clock"][3] - (3 * CHIP_STEP + 24)) // 2
# Rev 14: Chipspalte 6 px vom rechten Kartenrand (Glyphen sind schmaler als 24 px, sichtbar ~9 px),
# damit Uhrzeit und Datum links denselben Innenabstand P haben wie die Wetterkarte
CHIP_PAD = 6
CHIP_COL_CLOCK = CARDS["clock"][0] + CARDS["clock"][2] - CHIP_PAD - 24
CHIP_COL_WEATHER = CARDS["weather"][0] + CARDS["weather"][2] - CHIP_PAD - 24

# Rev 13: Uhrzeit Font 6 (72), Datum + innen Font 3 (26), Aussentemperatur Font 6.
# Breiten mit den echten Fonts gemessen (tools/font_text_width.py): "00:00" 169 px, "00°" 103 px,
# "Mo, 30. Nov" 121 px. Ein Nextion-Text, der nicht in die Box passt, verliert ganze Zeichen.
# Die Boxen reichen deshalb bis an die Chipspalte (kein Abstand, keine Ueberlappung).
ROW1_Y, ROW1_H = 25, 72                                  # Tinte y 39..82
ROW2_Y, ROW2_H = 97, 26                                  # Tinte y 102..120; Gruppe 39..120 ~ mittig in 10..150
TIME_L = CARDS["clock"][0] + P                    # 22, wie die Wetterkarte
WX = (WX_L, ROW1_Y + 36 - 28, 56, 56)                    # Wetterbild mittig zur Tinte der Temperatur
OUT_L = WX_L + 56 + 2

# Bauteile (name: x, y, w, h, font, Farbe-Key, xcen 0=links 1=mitte 2=rechts, Hinweis)
LAYOUT = {
    "time":           (TIME_L, ROW1_Y, CHIP_COL_CLOCK - TIME_L, ROW1_H, 6, "c20", 0, "Font 6"),
    "date":           (TIME_L, ROW2_Y, CHIP_COL_CLOCK - TIME_L, ROW2_H, 3, "c14", 0, "Font 3; Blueprint date_format '%a, %d. %b'"),
    "weather":        (*WX, None, None, None, "Picture, pic = Slot 135"),
    # Temperaturen (Firmware-Patch 5): aussen "10°" Font 6 (ab 4 Zeichen wie "-10°" Font 5), innen "21,8°"
    "outdoor_temp":   (OUT_L, ROW1_Y, CHIP_COL_WEATHER - OUT_L, ROW1_H, 6, "c20", 0, "Font 6"),
    "indr_temp_icon": (WX_L, ROW2_Y + ICON_DY, 24, ROW2_H, 7, "c14", 1, ""),
    "indr_temp":      (WX_L + 30, ROW2_Y, CHIP_COL_WEATHER - WX_L - 30, ROW2_H, 3, "c14", 0, "Font 3, ohne \"innen\""),
    "wifi_icon":      (CHIP_COL_WEATHER, CHIP_Y0 + ICON_DY, 24, 24, 7, "c10", 1, "oben in der rechten Spalte der Wetterkarte"),
    # Unten in der Wetter-Spalte: Benachrichtigung als Status-Icon (Chip-Schrift per Patch 8)
    "bt_notific":     (CHIP_COL_WEATHER, CHIP_Y0 + 3 * CHIP_STEP + ICON_DY, 24, 24, 7, "c10", 1, "unten in der rechten Spalte, Farbe setzt der Blueprint"),
    # Im festen Kreis zwischen den Pillen: QR-Knopf (nur sichtbar, wenn ein QR-Code eingestellt ist).
    # Dom hat ihn am Panel auf 209/274, 37x37 gesetzt (1 px tiefer als ICON_DY ergibt)
    "bt_qrcode":      (CIRCLE[0] + 7, CIRCLE[1] + 7 + ICON_DY + 1, 37, 37, 8, "c14", 1, "im Kreis zwischen den Pillen"),
}
# Kein Platz im Layout (bt_icon nur bei BLE-Firmware): im Overscan-Streifen rechts geparkt (x >= 455 ist hinter dem Rahmen)
PARKED = ["bt_icon", "bt_entities", "bt_utilities", "button01", "button02", "button03", "button04",
          "button05", "button06", "button07", "meridiem", "left_bt_text", "right_bt_text"]
CHIP_NAMES = ["chip_relay1", "chip_relay2", "chip_climate"] + [f"chip0{i}" for i in range(1, 8)]
CHIP_SLOTS = [(CHIP_COL_CLOCK, CHIP_Y0 + r * CHIP_STEP) for r in range(4)] + \
             [(CHIP_COL_WEATHER, CHIP_Y0 + r * CHIP_STEP) for r in (1, 2)]
for n, (x, y) in zip(CHIP_NAMES, CHIP_SLOTS):
    LAYOUT[n] = (x, y + ICON_DY, 24, 24, 7, "c20", 1, "")
# Rev 14: Chip 7-10 haben keinen Platz und werden geparkt. Frueher lagen sie deckungsgleich auf Platz 1-4:
# beim Neuaufbau der Seite (nach dem Bildschirmschoner) malte der Nextion sie leer ueber die echten Chips.
PARKED += CHIP_NAMES[6:]
for i, n in enumerate(PARKED):   # 18 px hoch, damit alle 17 untereinander in 0..320 passen
    LAYOUT[n] = (456, i * 18, 24, 18, None, None, None, "geparkt (Overscan, unsichtbar)")

CENTERED_TILES = "--links" not in sys.argv  # Rev 13: Kacheln mittig (Dom 24.10.); --links nur zum Vergleich
CIRCLES = {}
for (name, col), x in zip(TILES, TILE_X):
    cx = x + (TILE_W - 30) // 2 if CENTERED_TILES else x + TILE_PX
    CIRCLES[name] = (cx, TILE_Y + P, 30, 30, col)
    LAYOUT[name + "_icon"] = (cx, TILE_Y + P + ICON_DY, 30, 30, 7, "p_" + col, 1, "im Kreis")
    if CENTERED_TILES:
        LAYOUT[name] = (x + 4, TILE_Y + 46, TILE_W - 8, 28, 3, "c20", 1, "")
        LAYOUT[name + "_label"] = (x + 4, CAPTION_Y + 1, TILE_W - 8, 18, 0, "c14", 1, "Text, Scope global, max. 20 Zeichen")
    else:
        LAYOUT[name] = (x + TILE_PX, TILE_Y + 46, TILE_W - TILE_PX - 4, 28, 3, "c20", 0, "")
        LAYOUT[name + "_label"] = (x + TILE_PX, CAPTION_Y + 1, TILE_W - TILE_PX - 4, 18, 0, "c14", 0,
                                   "Text, Scope global, max. 20 Zeichen")

CSS_VARS = ";".join(f"--{k}:{v}" for k, v in C.items())


def tint(col, pct=28):
    return f"color-mix(in srgb,var(--{col}) {pct}%,var(--card))"


def bg_html(extra="", pills_on=(False, False), alarm=False):
    parts = []
    for key, (x, y, w, h) in CARDS.items():
        red = f"border-color:var(--p_red);background:{tint('p_red', ALARM_TINT)};" if alarm and key == "clock" else ""
        parts.append(f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{red}"></div>')
    for (name, col), x in zip(TILES, TILE_X):
        parts.append(f'<div class="card" style="left:{x}px;top:{TILE_Y}px;width:{TILE_W}px;height:{TILE_H}px"></div>')
        ix, iy, iw, ih, _ = CIRCLES[name]
        parts.append(f'<div class="circle" style="left:{ix}px;top:{iy}px;width:{iw}px;height:{ih}px;'
                     f'background:{tint("p_" + col, CIRCLE_TINT)}"></div>')
    for (x, y, w, h), on in zip(PILLS, pills_on):
        # aktiv: gelber Rand + leichte Toenung (Variante B), statt des Firmware-Strichs
        on_css = f"border-color:var(--p_yellow);background:{tint('p_yellow', 14)};" if on else ""
        parts.append(f'<div class="card pill" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                     f'border-radius:{h // 2}px;{on_css}"></div>')
    x, y, w, h = CIRCLE
    parts.append(f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:50%"></div>')
    return f'''<!doctype html><html><head><meta charset="utf-8">
<style>:root{{{CSS_VARS}}}*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:480px;height:320px;overflow:hidden;background:var(--bg)}}
.card{{position:absolute;background:var(--card);border:2px solid var(--c6);border-radius:16px}}
.circle{{position:absolute;border-radius:50%}}
.wx{{position:absolute}} .wx svg{{width:100%;height:100%;filter:saturate({WX_SATURATE})}}
</style></head><body>{"".join(parts)}{extra}</body></html>'''


def shot(html, png, w=480, h=320, scale=1):
    src = os.path.join(OUT, "_tmp.html")
    io.open(src, "w", encoding="utf-8").write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--force-device-scale-factor={scale}",
                    "--virtual-time-budget=8000", f"--screenshot={png}", "file:///" + src.replace("\\", "/")],
                   check=True, capture_output=True)
    im = Image.open(png).convert("RGB")
    if im.size != (w * scale, h * scale):
        raise SystemExit(f"{png}: Größe {im.size}, erwartet {(w * scale, h * scale)}")
    im.save(png)
    return im


def wx_div(key):
    x, y, w, h = WX
    return f'<div class="wx" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{icons[key]}</div>'


# --- Vorschau mit den echten Panel-Fonts (Nextion: xcen nach Vorschub-Summe, ycen nach Zellhoehe) ---
_fonts = {}


def font(fid):
    if fid not in _fonts:
        _fonts[fid] = decode_font(open(os.path.join(FONTS, f"{fid:02d}.zi"), "rb").read())
    return _fonts[fid]


def nx_text(im, text, box, fid, col, xcen, ycen=1):
    """Zeichnet `text` wie der Nextion: passt ein Zeichen nicht mehr in die Box, faellt es weg."""
    x, y, w, h = box
    f = font(fid)
    chars, width = [], 0
    for ch in f.characters_of(text.encode("utf-8")):
        if width + ch.advance > w:
            break
        chars.append(ch)
        width += ch.advance
    pen = x + [0, (w - width) // 2, w - width][xcen]
    top = y + [0, (h - f.height) // 2, h - f.height][ycen]
    rgb = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
    px = im.load()
    for ch in chars:
        cov = ch.coverages()
        for i, c in enumerate(cov):
            if c:
                gx, gy = pen - ch.left + i % ch.width, top + i // ch.width
                if x <= gx < x + w and y <= gy < y + h:
                    a = c / 7
                    px[gx, gy] = tuple(round(b * (1 - a) + v * a) for b, v in zip(px[gx, gy], rgb))
        pen += ch.advance
    return width


ICON = {k: chr(int(v, 16)) for k, v in
        re.findall(r'([\w-]+): "\\u([0-9A-Fa-f]{4})"', open(ICON_CODES, encoding="utf-8").read())}

# Legacy-Dark-Slot -> Icon (weather.h, Spalte legacy_dark)
WX_SLOTS = {1: "exceptional", 2: "sunny", 3: "cloudy", 4: "rainy", 5: "pouring", 6: "snowy",
            7: "snowy-rainy", 8: "fog", 9: "windy", 10: "lightning", 11: "partlycloudy",
            12: "partlycloudy (Nacht)", 13: "lightning-rainy", 14: "lightning-rainy", 15: "clear-night"}

if __name__ == "__main__":
    if CENTERED_TILES:
        shot(bg_html(), os.path.join(OUT, f"home_bg_{BG_SLOT}.png"))
        shot(bg_html(pills_on=(True, True)), os.path.join(OUT, f"home_on_{ON_SLOT}.png"))
        shot(bg_html(alarm=True), os.path.join(OUT, f"home_alarm_{ALARM_SLOT}.png"))
        x, y, w, h = WX
        for slot, key in WX_SLOTS.items():
            tmp = os.path.join(OUT, "_wx.png")
            im = shot(bg_html(wx_div(key)), tmp)
            im.crop((x, y, x + w, y + h)).save(os.path.join(OUT, f"home_wx_{slot + WX_OFFSET}.png"))
        os.remove(tmp)

    # Vorschau: Hintergrund + Wetterbild aus Chrome, Texte/Icons mit den Panel-Fonts, dann 2x
    sample = dict(time="10:47", date="Sa, 24. Okt", outdoor_temp="9°", indr_temp="22,3°",
                  value01="189W", value01_label="PV", value02="0W", value02_label="Export",
                  value03="3 Tage", value03_label="Wertstoff", value04="44,7°", value04_label="Wasser")
    mdi = dict(indr_temp_icon="home", wifi_icon="wifi", bt_qrcode="qrcode", bt_notific="bell",
               value01_icon="solar-power-variant-outline", value02_icon="transmission-tower-export",
               value03_icon="recycle-variant", value04_icon="thermometer-water",
               chip_relay1="toaster-oven", chip_relay2="dishwasher", chip_climate="email-plus")
    chip_cols = dict(bt_notific="p_red", chip_relay1="p_orange", chip_relay2="p_blue", chip_climate="p_orange")
    png = "preview.png" if CENTERED_TILES else "preview_links.png"
    tmp = os.path.join(OUT, "_pv.png")
    im = shot(bg_html(wx_div("rainy"), pills_on=(True, False)), tmp)
    os.remove(tmp)
    for name, (x, y, w, h, fid, col, xcen, _) in LAYOUT.items():
        if name in sample:
            nx_text(im, sample[name], (x, y, w, h), fid, C[col], xcen)
        elif name in mdi:
            nx_text(im, ICON[mdi[name]], (x, y, w, h), fid, C[chip_cols.get(name, col)], xcen)
    for (x, y, w, h), label in zip(HW_LABELS, ["Hell", "Normal"]):
        nx_text(im, label, (x, y, w, h), 1, C["c20"], 1)
    im.resize((960, 640), Image.NEAREST).save(os.path.join(OUT, png))
    # Timer-Vorschau (Patch 10): links laeuft der Timer, rechts ist er abgelaufen (rote Phase des Blinkens)
    for alarm, t, lbl, out in ((False, "4:32", "Timer", "preview_timer.png"), (True, "0:00", "Abgelaufen", "preview_alarm.png")):
        im2 = shot(bg_html(wx_div("rainy"), alarm=alarm), tmp)
        os.remove(tmp)
        timer_sample = dict(sample, time=t, date=lbl)
        for name, (x, y, w, h, fid, col, xcen, _) in LAYOUT.items():
            if name in timer_sample:
                nx_text(im2, timer_sample[name], (x, y, w, h), fid, C[col], xcen)
            elif name in mdi:
                nx_text(im2, ICON[mdi[name]], (x, y, w, h), fid, C[chip_cols.get(name, col)], xcen)
        for (x, y, w, h), label in zip(HW_LABELS, ["Hell", "Normal"]):
            nx_text(im2, label, (x, y, w, h), 1, C["c20"], 1)
        im2.resize((960, 640), Image.NEAREST).save(os.path.join(OUT, out))
    os.remove(os.path.join(OUT, "_tmp.html"))
    if not CENTERED_TILES:
        print("ok (nur Vorschau)")
        raise SystemExit

    # Positionsliste
    def rgb565(hexcol):
        r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    rows = ["| Bauteil | x | y | w | h | Font | pco (RGB565) | xcen | Hinweis |", "|---|---|---|---|---|---|---|---|---|"]
    for name, (x, y, w, h, fid, col, xcen, note) in LAYOUT.items():
        pco = f"{rgb565(C[col])} ({col})" if col else "–"
        rows.append(f"| `{name}` | {x} | {y} | {w} | {h} | {'' if fid is None else fid} | {pco} | "
                    f"{'' if xcen is None else xcen} | {note} |")
    io.open(os.path.join(OUT, "positions.md"), "w", encoding="utf-8").write(
        f"# Home-Seite: Bauteil-Positionen\n\nAlle Text-Bauteile: sta = crop image, picc = {BG_SLOT}. "
        f"Seite home: Back. Picture ID = {BG_SLOT}.\n\n" + "\n".join(rows) + "\n")
    print("Panel-Palette:", {k: C["p_" + k] for k in ACCENTS})
    print("ok")
