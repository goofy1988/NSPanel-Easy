"""Rounded-2-Patch 11 fuer NSPanel Easy: Tipp auf eine Home-Kachel meldet HA ein button_click-Event.
Aufruf im Repo-Root nach rounded2_patch10.py: python ../rounded2_patch11.py

Die Kacheln value01-04 (Wert und Icon) senden ihre Beruehrung roh an die Firmware (sendkey 3),
bisher ohne Wirkung. Beim Loslassen feuert die Firmware jetzt esphome.nspanel_easy mit
type button_click, page home, command short_click, component valueNN.
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


sub('esphome/nspanel_esphome_page_home.yaml', '''          - script.execute: sun_state_update
...
''', '''          - script.execute: sun_state_update

display:
  - id: !extend disp1
    on_touch:
      then:
        - lambda: |-
            // Rounded 2: a tap on a home tile (value or icon) is reported to Home Assistant
            if (touch_event or page_id != get_page_id("home")) return;
            static const struct {
              uint8_t value_id, icon_id;
              const char *name;
            } tiles[] = {
              {hmi::home::VALUE01.id, hmi::home::VALUE01_ICON.id, "value01"},
              {hmi::home::VALUE02.id, hmi::home::VALUE02_ICON.id, "value02"},
              {hmi::home::VALUE03.id, hmi::home::VALUE03_ICON.id, "value03"},
              {hmi::home::VALUE04.id, hmi::home::VALUE04_ICON.id, "value04"},
            };
            for (const auto &tile : tiles) {
              if (component_id == tile.value_id or component_id == tile.icon_id) {
                fire_ha_event("button_click", {
                  {"page", "home"},
                  {"command", "short_click"},
                  {"component", tile.name}
                });
                return;
              }
            }
...
''')
print("ok")
