r"""Rounded-2-Patch 14 fuer NSPanel Easy. Aufruf im Repo-Root nach rounded2_patch13.py: python ../rounded2_patch14.py

Home verliert den Hintergrund (Bild 134) nach einem Theme-Wechsel und manchmal nach dem Booten:
- Das Macro theme_apply setzt home.b[0].pic=pic_background_main (0). Die Firmware stellte danach
  mit "home.pic=134" zurueck. Das versteht der Nextion nur, solange home die aktuelle Seite ist
  (dann ist "home" das Seitenobjekt). Auf der Settings-Seite oder beim Booten ist es ein
  unbekannter Name, der Befehl faellt still weg. Richtig ist home.b[0].pic wie im Macro.
- Die TFT hat keine Light-Bilder mehr (nx_slim_apply.py, 1 x 1 Pixel). Die Firmware bleibt
  deshalb immer im Dark-Theme, auch wenn "Light" gewaehlt ist.
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


sub('esphome/nspanel_esphome_hw_display.yaml', r'''          current_theme = (background_type->current_option() == "${THEME_LIGHT_LABEL}") ?
                                                                ThemeMode::LIGHT : ThemeMode::DARK;''', r'''          // Rounded 2: the TFT ships no light-theme pictures, so the panel always stays dark
          if (background_type->current_option() == "${THEME_LIGHT_LABEL}") {
            ESP_LOGW("${TAG_HW_DISPLAY}", "Rounded 2 has no light theme, staying dark");
          }
          current_theme = ThemeMode::DARK;''')
sub('esphome/nspanel_esphome_hw_display.yaml', r'''          disp1->send_command_printf("home.pic=%" PRIu8, HOME_BACKGROUND_PIC);''', r'''          // b[0] is the page object; "home.pic" only resolves while home is the current page
          disp1->send_command_printf("home.b[0].pic=%" PRIu8, HOME_BACKGROUND_PIC);''')
print("ok")
