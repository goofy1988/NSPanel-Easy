"""Setzt assets/ und assets/positions.md auf der Seite home einer NSPanel-HMI um.

    python nx_home_apply.py <quelle.HMI> <ziel.HMI>

- Bilder 134-149 werden durch assets/home_bg_134.png bzw. home_wx_NNN.png ersetzt,
  150 (home_on_150.png) und 151 (home_alarm_151.png) werden angehängt bzw. ersetzt.
- EXTRA_ATTRS setzt einzelne Attribute, die positions.md nicht kennt (z. B. txt_maxl).
- Jede Zeile der Tabelle in positions.md setzt x/y/w/h, Font, pco und xcen des
  Bauteils, berechnet endx/endy neu und setzt bei Text-Bauteilen sta=0 (crop) und picc=134.
- Bauteile aus der Tabelle, die es auf home nicht gibt, werden als Kopie von value01
  angelegt (txt_maxl 20, bco 0, sendkey 0).
- Die Quelle wird nur gelesen. Das Ziel darf nicht die Quelle sein.
- Danach wird das Ziel erneut ausgelesen und mit dem bearbeiteten Dump verglichen.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NX = HERE / "nxwright" / ".venv" / "Scripts" / "nxwright.exe"
ASSETS = HERE.parent / "assets"
# Attribute, die nicht in positions.md stehen. time: Timer-Restzeit "12:05 h" = 7 Bytes (Patch 10)
EXTRA_ATTRS = {"time": {"txt_maxl": 8}}


def nx(*args):
    subprocess.run([str(NX), *map(str, args)], check=True)


def blocks_of(text):
    return re.split(r"(?=^object \d+ )", text, flags=re.M)


def name_of(block):
    m = re.match(r"object \d+ (\S+)", block)
    return m.group(1) if m else None


def set_attr(block, key, value):
    new, n = re.subn(rf"^(  {key}(?::\w+)? = ).*$", lambda m: m.group(1) + str(value), block, count=1, flags=re.M)
    if not n:
        raise KeyError(f"{name_of(block)}: {key} fehlt")
    return new


def read_positions():
    rows = {}
    for line in (ASSETS / "positions.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 8 or not cells[0].startswith("`"):
            continue
        name = cells[0].strip("`")
        pco = cells[6].split()[0] if cells[6] and cells[6][0].isdigit() else None
        rows[name] = dict(x=cells[1], y=cells[2], w=cells[3], h=cells[4],
                          font=cells[5] or None, pco=pco, xcen=cells[7] or None)
    return rows


def apply(dump):
    for i in range(134, 152):
        src = {134: "home_bg_134.png", 150: "home_on_150.png", 151: "home_alarm_151.png"}.get(i, f"home_wx_{i}.png")
        shutil.copyfile(ASSETS / src, dump / "images" / f"{i:04d}.png")

    page = next((dump / "pages").glob("*-home.txt"))
    blocks = blocks_of(page.read_text(encoding="utf-8"))
    index = {name_of(b): i for i, b in enumerate(blocks) if name_of(b)}
    template = blocks[index["value01"]]
    last = max(int(re.match(r"object (\d+)", b).group(1)) for b in blocks if name_of(b))
    pos = read_positions()

    added = []
    for name in pos:
        if name in index:
            continue
        last += 1
        b = re.sub(r"^object \d+ \S+", f"object {last} {name}", template, count=1)
        b = set_attr(b, "id", last)
        b = set_attr(b, "objname", f'"{name}"')
        b = set_attr(b, "txt_maxl", 20)
        b = set_attr(b, "bco", 0)
        b = set_attr(b, "sendkey", 0)
        if not blocks[-1].endswith("\n\n"):
            blocks[-1] = blocks[-1].rstrip("\n") + "\n\n"
        blocks.append(b)
        index[name] = len(blocks) - 1
        added.append(name)

    for name, p in pos.items():
        i = index[name]
        b = blocks[i]
        for k in ("x", "y", "w", "h", "font", "pco", "xcen"):
            if p[k] is not None:
                b = set_attr(b, k, p[k])
        b = set_attr(b, "endx", int(p["x"]) + int(p["w"]) - 1)
        b = set_attr(b, "endy", int(p["y"]) + int(p["h"]) - 1)
        if re.search(r"^  picc = ", b, re.M):
            b = set_attr(b, "sta", 0)
            b = set_attr(b, "picc", 134)
        for k, v in EXTRA_ATTRS.get(name, {}).items():
            b = set_attr(b, k, v)
        blocks[i] = b

    page.write_text("".join(blocks).rstrip("\n") + "\n", encoding="utf-8")
    print(f"home: {len(pos)} Bauteile gesetzt, neu: {', '.join(added) or '-'}")


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
