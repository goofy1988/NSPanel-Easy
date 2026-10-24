"""Verkleinert eine NSPanel-HMI fuer Rounded 2 (nur Dark-Theme, europaeische Sprachen).

    python nx_slim_apply.py <quelle.HMI> <ziel.HMI>

- Fonts 0-4 (Sarasa 16-36, je 10569 Zeichen) behalten nur Latein mit Erweiterungen, Griechisch,
  Kyrillisch, Vietnamesisch und die Zeichen U+2000-U+2BFF (Satzzeichen, Waehrung, Pfeile, Formen).
  CJK, Hangul, Arabisch, Hebraeisch, Thai usw. fallen weg. Die Icon-Fonts 7, 8, 10 bleiben ganz.
- Die Bilder, die nur das Light-Theme nutzt (Macro theme_apply, Button-Seiten 79/80), werden zu
  1 x 1 Pixel. Die IDs bleiben, damit Firmware und Event-Code stimmen.
- Die Quelle wird nur gelesen. Danach wird das Ziel erneut ausgelesen und verglichen.
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "nxwright"))
from nx_home_apply import nx  # noqa: E402
from nxwright.project.zi_font import Glyph, decode_font, encode_font  # noqa: E402
from PIL import Image  # noqa: E402

TEXT_FONTS = (0, 1, 2, 3, 4)
LIGHT_PICS = [48, *range(49, 64), 64, 72, 73, 79, 80, 105, 107, 109, 111, 112, 113]


def keep(code):
    return code < 0x250 or 0x370 <= code < 0x500 or 0x1E00 <= code < 0x1F00 or 0x2000 <= code < 0x2C00


def slim_font(path):
    font = decode_font(path.read_bytes())
    if font.advances is not None:
        raise SystemExit(f"{path.name}: volle utf-8-Tabelle, nicht vorgesehen")
    glyphs = [Glyph(c.code, c.advance, c.left, c.right, tuple(c.coverages()))
              for code, c in sorted(font.characters.items()) if keep(code)]
    before = path.stat().st_size
    path.write_bytes(encode_font(font.name, font.encoding, font.height, font.rotation, glyphs, font.smoothed))
    print(f"Font {path.stem}: {len(font.characters)} -> {len(glyphs)} Zeichen, "
          f"{before / 1e6:.2f} -> {path.stat().st_size / 1e6:.2f} MB")


def apply(dump):
    for fid in TEXT_FONTS:
        slim_font(dump / "fonts" / f"{fid:02d}.zi")
    saved = 0
    for pid in LIGHT_PICS:
        png = dump / "images" / f"{pid:04d}.png"
        w, h = Image.open(png).size
        saved += w * h * 2
        Image.new("RGB", (1, 1), (0, 0, 0)).save(png)
    print(f"{len(LIGHT_PICS)} Light-Bilder auf 1 x 1, ~{saved / 1e6:.2f} MB")


def main():
    src, dst = map(lambda p: Path(p).resolve(), sys.argv[1:3])
    if src == dst:
        sys.exit("Ziel darf nicht die Quelle sein.")
    with tempfile.TemporaryDirectory() as tmp:
        dump, check = Path(tmp) / "dump", Path(tmp) / "check"
        nx("dump", src, dump)
        apply(dump)
        nx("write", "--overwrite", src, dump, dst)
        nx("dump", dst, check)
        for sub in ("pages", "images", "fonts"):
            for f in (dump / sub).iterdir():
                if f.suffix == ".i" or f.name == "index.txt":
                    continue
                a, b = f.read_bytes().replace(b"\r\n", b"\n"), (check / sub / f.name).read_bytes().replace(b"\r\n", b"\n")
                if a != b:
                    sys.exit(f"Prüfung fehlgeschlagen: {sub}/{f.name}")
    print(f"OK: {dst}")


if __name__ == "__main__":
    main()
