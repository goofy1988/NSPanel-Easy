"""Rendert MDI-Icons im Kachelkreis (Panel-Font 7, Layout aus home_assets.py), 8x vergroessert.

python tools/icon_compare.py <icon> [<icon> ...]   ->  assets/icon_compare.png
"""
import os
import sys

names = sys.argv[1:]
sys.argv = sys.argv[:1]

sys.path.insert(0, r"C:\Users\dom\nspanel_tft")
import home_assets as ha  # noqa: E402
from PIL import Image  # noqa: E402

bg = os.path.join(ha.OUT, "_cmp.png")
base = ha.shot(ha.bg_html(), bg)
os.remove(bg)
os.remove(os.path.join(ha.OUT, "_tmp.html"))
x, y, w, h, fid, col, xcen, _ = ha.LAYOUT["value03_icon"]
cx, cy = ha.CIRCLES["value03"][:2]
tiles = []
for n in names:
    im = base.copy()
    ha.nx_text(im, ha.ICON[n], (x, y, w, h), fid, ha.C[col], xcen)
    tiles.append(im.crop((cx - 4, cy - 4, cx + 34, cy + 34)).resize((304, 304), Image.NEAREST))
out = Image.new("RGB", (304 * len(tiles), 304))
for i, t in enumerate(tiles):
    out.paste(t, (i * 304, 0))
out.save(os.path.join(ha.OUT, "icon_compare.png"))
print("ok", names)
