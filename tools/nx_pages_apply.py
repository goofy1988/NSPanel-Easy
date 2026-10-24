"""Setzt die Rounded-2-Seiten aus pages_assets.py in einer NSPanel-HMI um.

    python nx_pages_apply.py <quelle.HMI> <ziel.HMI>

- Bild 0 (pic_background_main, Dark) wird schwarz, Bild 46/47 (Button-Karten aus/an) neu.
- Bild 152 (notification) und 153 (qrcode) werden angehaengt bzw. ersetzt. Die beiden Seiten
  nutzen sie statt pic_background_main (im Event-Code ersetzt, deshalb nur Dark-Theme).
- Bild 154 = Seitenhintergrund buttonpage01-04 mit Zurueck-Kreis. Dort setzt der Event-Code die
  Bilder nur im Light-Theme, deshalb werden die statischen Attribute (Dark) auf 154 gesetzt.
- Der Zurueck-Pfeil bekommt die Kreisfarbe (back_pco) statt color_pco_navigation.
- assets/pages_positions.json setzt x/y/w/h (endx/endy neu), Font, xcen/ycen und Extra-Attribute
  auf buttonpage01-04, notification und qrcode.
- Die Quelle wird nur gelesen. Danach wird das Ziel erneut ausgelesen und verglichen.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nx_home_apply import ASSETS, blocks_of, name_of, nx, set_attr  # noqa: E402

IMAGES = {0: "page_bg_0.png", 46: "buttons_off_46.png", 47: "buttons_on_47.png",
          152: "notification_152.png", 153: "qrcode_153.png", 154: "buttonpage_154.png"}
PAGES = {"buttonpage01": "buttonpage", "buttonpage02": "buttonpage", "buttonpage03": "buttonpage",
         "buttonpage04": "buttonpage", "notification": "notification", "qrcode": "qrcode"}
OWN_BACKGROUND = {"notification": 152, "qrcode": 153}
BUTTONPAGE_BG = 154


def apply(dump):
    images = dump / "images"
    have = len(list(images.glob("*.png")))
    for i, src in IMAGES.items():
        if i > have:
            raise SystemExit(f"Bild {i}: die IDs muessen lueckenlos sein (vorhanden 0..{have - 1})")
        shutil.copyfile(ASSETS / src, images / f"{i:04d}.png")
        have = max(have, i + 1)

    data = json.loads((ASSETS / "pages_positions.json").read_text(encoding="utf-8"))
    for page_name, kind in PAGES.items():
        page = next((dump / "pages").glob(f"*-{page_name}.txt"))
        text = page.read_text(encoding="utf-8")
        if page_name in OWN_BACKGROUND:
            text = text.replace("pic_background_main", str(OWN_BACKGROUND[page_name]))
            old = "button_back.pco=color_pco_navigation"
            if text.count(old) != 1:
                raise SystemExit(f"{page_name}: {old} {text.count(old)}x statt 1x")
            text = text.replace(old, f"button_back.pco={data['back_pco']}")
        blocks = blocks_of(text)
        index = {name_of(b): i for i, b in enumerate(blocks) if name_of(b)}
        pos = data["positions"][kind]
        extra = data["extra"].get(kind, {})
        for name, (x, y, w, h, font, xcen, ycen) in pos.items():
            if name not in index:
                raise SystemExit(f"{page_name}: Bauteil {name} fehlt")
            b = blocks[index[name]]
            for k, v in (("x", x), ("y", y), ("w", w), ("h", h), ("endx", x + w - 1), ("endy", y + h - 1),
                         ("font", font), ("xcen", xcen), ("ycen", ycen)):
                if v is not None:
                    b = set_attr(b, k, v)
            for k, v in extra.get(name, {}).items():
                b = set_attr(b, k, v)
            if kind == "buttonpage" and name in ("page_label", "page_index", "button_back"):
                b = set_attr(b, "picc", BUTTONPAGE_BG)
                if name == "button_back":
                    b = set_attr(set_attr(b, "picc2", BUTTONPAGE_BG), "pco", data["back_pco"])
            blocks[index[name]] = b
        if kind == "buttonpage":
            blocks[index[page_name]] = set_attr(blocks[index[page_name]], "pic", BUTTONPAGE_BG)
        page.write_text("".join(blocks).rstrip("\n") + "\n", encoding="utf-8")
        print(f"{page_name}: {len(pos)} Bauteile gesetzt")


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
        for sub in ("pages", "images"):
            for f in (dump / sub).iterdir():
                if f.suffix == ".i" or f.name == "index.txt":
                    continue
                a, b = f.read_bytes().replace(b"\r\n", b"\n"), (check / sub / f.name).read_bytes().replace(b"\r\n", b"\n")
                if a != b:
                    sys.exit(f"Prüfung fehlgeschlagen: {sub}/{f.name}")
    print(f"OK: {dst}")


if __name__ == "__main__":
    main()
