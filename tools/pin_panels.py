"""Pinnt alle NSPanel-Configs in /config/esphome auf einen Tag des Forks (auf dem HA-Host ausfuehren).

    sudo python3 pin_panels.py rounded2-2026.10.24

Legt je Datei <name>.yaml.bak_<datum> an. Aendert nur Substitutions ref_url/ref_name/
nextion_update_url und remote_package url/ref. Geflasht wird nichts.
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path

TAG = sys.argv[1]
FORK = "https://github.com/goofy1988/NSPanel-Easy"
TFT = f"https://raw.githubusercontent.com/goofy1988/NSPanel-Easy/{TAG}/hmi/nspanel_landscape.tft"
SUBS = (f"  # Rounded 2: Doms Fork, gepinnt auf Tag {TAG} (= Stand eg_k)\n"
        f"  ref_url: {FORK}\n  ref_name: {TAG}\n  nextion_update_url: {TFT}\n")
PANELS = ["eg-k", "eg-f", "og-a", "og-d", "og-sz", "ug-server"]

for name in PANELS:
    path = Path(f"/config/esphome/{name}-nspanel.yaml")
    text = path.read_text(encoding="utf-8")
    shutil.copyfile(path, f"{path}.bak_{date.today():%Y%m%d}")
    # alte Rounded-2-Substitutions entfernen (Kommentar + drei Zeilen), dann vor "# Customization area" neu
    text = re.sub(r"  # Rounded 2:.*\n(  (ref_url|ref_name|nextion_update_url):.*\n)+", "", text)
    text, n = re.subn(r"\n*(# Customization area)", "\n" + SUBS + r"\1", text, count=1)
    if n != 1:
        sys.exit(f"{name}: '# Customization area' nicht gefunden")
    text, n = re.subn(r"(  remote_package:\n    url: ).*\n    ref: .*\n",
                      rf"\g<1>{FORK}  # Fork, Rounded 2 = v2026.10.7 + Patches 1-13\n"
                      rf"    ref: {TAG}  # gepinnt {date.today():%d.%m.%Y}, Stand eg_k\n", text, count=1)
    if n != 1:
        sys.exit(f"{name}: remote_package nicht gefunden")
    path.write_text(text, encoding="utf-8")
    print(f"{name}: gepinnt auf {TAG}")
