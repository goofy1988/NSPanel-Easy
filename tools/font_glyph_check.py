"""Misst, wie MDI-Glyphen in einem Nextion-Icon-Font sitzen (Tinte vs. Vorschub-Box).

python tools/font_glyph_check.py <dump>/fonts/07.zi [icon-name ...]
dx/dy = Versatz der Tinten-Mitte gegen die Box-Mitte in px (+ = rechts/unten).
"""
import re
import sys

sys.path.insert(0, r"C:\Users\dom\nspanel_tft\tools\nxwright")
from nxwright.project.zi_font import decode_font  # noqa: E402

ICONS = r"C:\Users\dom\nspanel_tft\easy_src_10.7\docs\icons\all_icons.json"
codes = {k: int(v, 16) for k, v in
         re.findall(r'([\w-]+): "\\u([0-9A-Fa-f]{4})"', open(ICONS, encoding="utf-8").read())}


def ink(font, ch):
    cov, w = ch.coverages(), ch.width
    pts = [(i % w - ch.left, i // w) for i, c in enumerate(cov) if c > 2]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def offsets(font, ch):
    x0, x1, y0, y1 = ink(font, ch)
    return (x0 + x1) / 2 - (ch.advance - 1) / 2, (y0 + y1) / 2 - (font.height - 1) / 2


if __name__ == "__main__":
    font = decode_font(open(sys.argv[1], "rb").read())
    print(font.name, font.height, len(font.characters), "Zeichen")
    for name in sys.argv[2:]:
        ch = font.characters.get(codes.get(name, -1))
        if ch is None:
            print(f"{name:32} fehlt")
            continue
        x0, x1, y0, y1 = ink(font, ch)
        dx, dy = offsets(font, ch)
        print(f"{name:32} adv={ch.advance:2} L={ch.left} R={ch.right} ink x {x0}..{x1} y {y0}..{y1} "
              f"dx={dx:+.1f} dy={dy:+.1f}")
    # Verteilung ueber alle Glyphen
    ds = [offsets(font, c) for c in font.characters.values() if c.advance > 4]
    for i, axis in enumerate("xy"):
        vals = sorted(d[i] for d in ds)
        print(f"d{axis}: Median {vals[len(vals) // 2]:+.1f}, 5 % {vals[len(vals) // 20]:+.1f}, "
              f"95 % {vals[-len(vals) // 20]:+.1f}")
