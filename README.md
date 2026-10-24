# Rounded 2 / Graphit – Werkbank für NSPanel Easy

Design-Werkzeuge und Ergebnis zum Firmware-Branch `rounded2` (gepinnt: Tag `rounded2-2026.10.24b`).

- `AGENTS.md`: Regeln, Bild-IDs, Patches, Fallstricke
- `home_assets.py`, `pages_assets.py`: erzeugen `assets/` (Bilder, Positionen, Vorschauen)
- `rounded2_patch*.py`: Firmware-Patches auf v2026.10.7 (Reihenfolge: patch, 10, 11, 12, 13, 14)
- `tools/`: nxwright-Skripte (HMI ohne Nextion Editor) und `pin_panels.py`. nxwright selbst:
  https://github.com/nixiewright/nxwright, Commit 46f3eb4
- `Rounded2Project/nspanel_landscape_v2026.10.7_rounded2i.HMI`: finale HMI,
  `nspanel_landscape.tft`: daraus kompiliert (24.10.2026)

Kette: Basis-HMI v2026.10.7 → nx_home_apply → `_rounded2d` → nx_pages_apply → nx_slim_apply → `_rounded2i`
