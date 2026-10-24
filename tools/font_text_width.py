"""Breite (Vorschub-Summe) und Tinten-Hoehe eines Textes in einem Nextion-Font.

python tools/font_text_width.py <dump>/fonts <font-id> "Text" ["Text" ...]
"""
import os
import sys

sys.path.insert(0, r"C:\Users\dom\nspanel_tft\tools\nxwright")
from nxwright.project.zi_font import decode_font  # noqa: E402


def load(fonts_dir, fid):
    return decode_font(open(os.path.join(fonts_dir, f"{fid:02d}.zi"), "rb").read())


def measure(font, text):
    chars = font.characters_of(text.encode("utf-8"))
    width = sum(c.advance for c in chars)
    rows = []
    for c in chars:
        cov = c.coverages()
        rows += [i // c.width for i, v in enumerate(cov) if v > 2]
    return width, (min(rows), max(rows)) if rows else (None, None)


if __name__ == "__main__":
    font = load(sys.argv[1], int(sys.argv[2]))
    for t in sys.argv[3:]:
        w, (y0, y1) = measure(font, t)
        print(f"font {sys.argv[2]} (h {font.height}) {t!r}: {w} px breit, Tinte y {y0}..{y1}")
