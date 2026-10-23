"""NSPanel Easy Home-Seite im Rounded-2-Stil: Assets fuer den Nextion Editor.

Erzeugt in C:\\Users\\dom\\nspanel_tft\\assets\\:
  home_bg_134.png          Home-Hintergrund 480x320 (neuer Bild-Slot 134)
  home_wx_<slot>.png       15 Wetter-Icons, deckend aus dem Hintergrund geschnitten (Slots 135-149)
  preview.png              Vorschau mit Beispielwerten (2x), nur zum Anschauen
  positions.md             Bauteil-Liste fuer den Editor (x, y, w, h, Font, Farbe RGB565)

Alle Koordinaten stehen nur in LAYOUT; Hintergrund, Icons, Vorschau und Liste lesen von dort.
"""
import io, json, os, subprocess
from PIL import Image

OUT = r"C:\Users\dom\nspanel_tft\assets"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
os.makedirs(OUT, exist_ok=True)
icons = json.load(open(r"C:\Users\dom\wetter_icons.json", encoding="utf-8"))

C = dict(bg="#080A0F", card="#101318", c6="#303339", c10="#74777F", c14="#B7BBC2",
         c16="#D4D7E0", c20="#F9FCFF", red="#FDA19A", orange="#F5AB77",
         yellow="#FCC364", green="#89D298", blue="#92C1FD", purple="#D6A9F1")

BG_SLOT = 134          # neuer Home-Hintergrund (Liste endet in 10.7 bei 133)
WX_OFFSET = BG_SLOT    # Home-Wetterbild = Legacy-Dark-Slot (1..15) + 134 -> 135..149

# Karten (nur Hintergrund)
# Sichtbar ist nur x 0-455 (Overscan rechts ~25 px, am Foto 23.10. an den HW-Leisten gemessen)
CARDS = dict(clock=(10, 10, 252, 142), weather=(272, 10, 173, 142))
TILE_X = [10, 121, 232, 343]
TILE_Y, TILE_W, TILE_H = 162, 102, 92
TILES = [("value01", "yellow", "PV"), ("value02", "green", "Einspeisung"),
         ("value03", "orange", "Müll"), ("value04", "blue", "Warmwasser")]
# Pillen zentriert auf die Firmware-Leisten (hardware.h: EU 47/288, y 312, w 120)
PILLS = [(17, 266, 180, 52), (258, 266, 180, 52)]
HW_BARS = [(47, 312, 120, 3), (288, 312, 120, 3)]
HW_LABELS = [(47, 280, 120, 24), (288, 280, 120, 24)]   # Patch: y 286 -> 280, mittig in der Pille
WX = (280, 22, 56, 56)                                   # Wetterbild = Icon-Groesse
STATIC_TEXT = [("Trittau", 282, 88, 13, "c14")]

# Bauteile (name: x, y, w, h, font, Farbe-Key, xcen 0=links 1=mitte 2=rechts, Hinweis)
LAYOUT = {
    "time":           (20, 48, 236, 62, 6, "c20", 0, ""),
    "date":           (20, 112, 236, 30, 2, "c14", 0, ""),
    "outdoor_temp":   (338, 20, 102, 60, 4, "c20", 2, "rechtsbündig"),
    "weather":        (*WX, None, None, None, "Picture, pic = Slot 135"),
    "indr_temp_icon": (280, 112, 30, 30, 7, "c14", 1, "Font 8 → 7"),
    "indr_temp":      (312, 112, 128, 30, 2, "c16", 0, ""),
    "wifi_icon":      (230, 16, 30, 30, 7, "c10", 1, ""),
    "bt_icon":        (410, 16, 30, 30, 7, "c10", 1, ""),
    "bt_qrcode":      (205, 272, 45, 42, 8, "c10", 1, ""),
}
CHIP_NAMES = ["chip_relay1", "chip_relay2", "chip_climate"] + [f"chip0{i}" for i in range(1, 8)]
for i, n in enumerate(CHIP_NAMES):
    # 7 Plätze passen in die Uhr-Karte; 8-10 werden bei Dom nie belegt und liegen dahinter
    x = 18 + i * 30 if i < 7 else 18 + (i - 7) * 30
    LAYOUT[n] = (x, 16, 30, 30, 7, "c20", 1, "" if i < 7 else "nur Reserve, deckt Platz 1-3")
for (name, col, _), x in zip(TILES, TILE_X):
    LAYOUT[name + "_icon"] = (x + 10, TILE_Y + 10, 30, 30, 7, col, 1, "im Kreis")
    LAYOUT[name] = (x + 10, TILE_Y + 46, TILE_W - 16, 24, 2, "c20", 0, "")

CSS_VARS = ";".join(f"--{k}:{v}" for k, v in C.items())


def tint(col, pct=14):
    return f"color-mix(in srgb,var(--{col}) {pct}%,var(--card))"


def bg_html(extra=""):
    parts = []
    for x, y, w, h in CARDS.values():
        parts.append(f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
    for (name, col, label), x in zip(TILES, TILE_X):
        parts.append(f'<div class="card" style="left:{x}px;top:{TILE_Y}px;width:{TILE_W}px;height:{TILE_H}px"></div>')
        ix, iy, iw, ih = LAYOUT[name + "_icon"][:4]
        parts.append(f'<div class="circle" style="left:{ix}px;top:{iy}px;width:{iw}px;height:{ih}px;'
                     f'background:{tint(col)}"></div>')
        parts.append(f'<div class="lbl" style="left:{x + 12}px;top:{TILE_Y + 72}px">{label}</div>')
    for x, y, w, h in PILLS:
        parts.append(f'<div class="card pill" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                     f'border-radius:{h // 2}px"></div>')
    for t, x, y, size, col in STATIC_TEXT:
        parts.append(f'<div class="lbl" style="left:{x}px;top:{y}px;font-size:{size}px;color:var(--{col})">{t}</div>')
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css">
<style>:root{{{CSS_VARS}}}*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:480px;height:320px;overflow:hidden;background:var(--bg);font-family:Inter,sans-serif}}
.card{{position:absolute;background:var(--card);border:1px solid rgba(255,255,255,.06);border-radius:16px}}
.circle{{position:absolute;border-radius:50%}}
.lbl{{position:absolute;font-size:12px;color:var(--c14);white-space:nowrap;line-height:1}}
.dyn{{position:absolute;display:flex;align-items:center;white-space:nowrap;overflow:hidden;line-height:1}}
.wx{{position:absolute}} .wx svg{{width:100%;height:100%}}
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


# Legacy-Dark-Slot -> Icon (weather.h, Spalte legacy_dark)
WX_SLOTS = {1: "exceptional", 2: "sunny", 3: "cloudy", 4: "rainy", 5: "pouring", 6: "snowy",
            7: "snowy-rainy", 8: "fog", 9: "windy", 10: "lightning", 11: "partlycloudy",
            12: "partlycloudy (Nacht)", 13: "lightning-rainy", 14: "lightning-rainy", 15: "clear-night"}

if __name__ == "__main__":
    shot(bg_html(), os.path.join(OUT, f"home_bg_{BG_SLOT}.png"))
    x, y, w, h = WX
    for slot, key in WX_SLOTS.items():
        tmp = os.path.join(OUT, "_wx.png")
        im = shot(bg_html(wx_div(key)), tmp)
        im.crop((x, y, x + w, y + h)).save(os.path.join(OUT, f"home_wx_{slot + WX_OFFSET}.png"))
    os.remove(tmp)

    # Vorschau: Beispielwerte in Inter, so wie die Nextion-Fonts sie später zeigen
    sizes = {1: 18, 2: 20, 4: 34, 6: 66, 7: 22, 8: 26}
    sample = dict(time="15:42", date="Freitag, 23. Okt.", outdoor_temp="9,4°C", indr_temp="21,4°C",
                  value01="1.240 W", value02="380 W", value03="B+P 2T", value04="31,9 °C")
    mdi = dict(indr_temp_icon="home-thermometer-outline", wifi_icon="wifi", bt_qrcode="qrcode",
               value01_icon="solar-power-variant-outline", value02_icon="transmission-tower-export",
               value03_icon="delete-sweep-outline", value04_icon="thermometer-water",
               chip_relay1="toaster-oven", chip_relay2="dishwasher")   # Chips links gepackt
    chip_cols = dict(chip_relay1="orange", chip_relay2="blue")
    extra = wx_div("rainy")
    for name, (x, y, w, h, font, col, xcen, _) in LAYOUT.items():
        if name in sample:
            just = ["flex-start", "center", "flex-end"][xcen]
            weight = 300 if font in (4, 6) else 400
            extra += (f'<div class="dyn" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;justify-content:{just};'
                      f'font-size:{sizes[font]}px;font-weight:{weight};color:var(--{col})">{sample[name]}</div>')
        elif name in mdi:
            c = chip_cols.get(name, col)
            extra += (f'<div class="dyn" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;justify-content:center;'
                      f'font-size:{sizes[font]}px;color:var(--{c})"><span class="mdi mdi-{mdi[name]}"></span></div>')
    for (x, y, w, h), label, on in zip(HW_LABELS, ["Hell", "Normal"], [True, False]):
        extra += (f'<div class="dyn" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;justify-content:center;'
                  f'font-size:18px;color:var(--{"c20" if on else "c10"})">{label}</div>')
    for (x, y, w, h), on in zip(HW_BARS, [True, False]):
        extra += (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:1px;'
                  f'background:var(--{"yellow" if on else "c6"})"></div>')
    shot(bg_html(extra), os.path.join(OUT, "preview.png"), scale=2)
    os.remove(os.path.join(OUT, "_tmp.html"))

    # Positionsliste
    def rgb565(hexcol):
        r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    rows = ["| Bauteil | x | y | w | h | Font | pco (RGB565) | xcen | Hinweis |", "|---|---|---|---|---|---|---|---|---|"]
    for name, (x, y, w, h, font, col, xcen, note) in LAYOUT.items():
        pco = f"{rgb565(C[col])} ({col})" if col else "–"
        rows.append(f"| `{name}` | {x} | {y} | {w} | {h} | {'' if font is None else font} | {pco} | "
                    f"{'' if xcen is None else xcen} | {note} |")
    io.open(os.path.join(OUT, "positions.md"), "w", encoding="utf-8").write(
        f"# Home-Seite: Bauteil-Positionen\n\nAlle Text-Bauteile: sta = crop image, picc = {BG_SLOT}. "
        f"Seite home: Back. Picture ID = {BG_SLOT}.\n\n" + "\n".join(rows) + "\n")
    print("ok")
