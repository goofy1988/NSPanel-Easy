"""Rounded-2-Patch 12 fuer NSPanel Easy. Aufruf im Repo-Root nach rounded2_patch11.py: python ../rounded2_patch12.py

1) Tipp auf Wetter/Aussentemperatur auf home oeffnet die Vorhersage nicht mehr (wird nicht genutzt).
2) Button-Seiten (Dark): gedrueckte/aktive Karte ist dunkel mit gelbem Rand (Bild 47), Name und
   Helligkeit bleiben weiss statt Indigo. Light-Theme unveraendert.
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


sub('esphome/nspanel_esphome_page_weather.yaml', '''              goto_page->execute(get_page_id("weather01"));
              return;''', '''              return;  // Rounded 2: the forecast pages are not used, a tap does nothing''')
sub('esphome/nspanel_esphome_page_buttons.yaml',
    '          const uint16_t fg_color = effective_state ? Colors::RGB565_BLUE_INDIGO : Colors::RGB565_WHITE;',
    '          // Rounded 2: the dark pressed card is dark too (picture 47), so the text stays white\n'
    '          const uint16_t fg_color = (effective_state and current_theme == ThemeMode::LIGHT) ?\n'
    '                                    Colors::RGB565_BLUE_INDIGO : Colors::RGB565_WHITE;')
print("ok")
