"""Rounded-2-Patch fuer NSPanel Easy. Aufruf im Repo-Root: python ../rounded2_patch.py
1) Chips links packen  2) Home-Wetterbild aus Slots 135-149  3) HW-Tastenlabels auf home.pic
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))

sub('components/nspanel_easy/chips.cpp', '''void chip_render(uint8_t idx) {
  if (idx >= CHIP_COUNT || nextion_display == nullptr) {
    return;
  }

  const ChipState &the_chip = chip_states[idx];
  const char *text = the_chip.visible ? the_chip.icon : "";

  nextion_display->set_component_text(CHIP_NAMES_HOME[idx], text);
  if (the_chip.visible) {
    nextion_display->set_component_font_color(CHIP_NAMES_HOME[idx], the_chip.color);
  }

  if (chips_mirror_page) {
    nextion_display->set_component_text(CHIP_NAMES[idx], text);
    if (the_chip.visible) {
      nextion_display->set_component_font_color(CHIP_NAMES[idx], the_chip.color);
    }
  }
}
''', '''// Rounded 2: visible chips are packed to the left, so a hidden chip leaves no gap.
// Display slot n shows the n-th visible chip; the slot cache skips redundant writes.
struct ChipSlot {
  char icon[4];
  uint16_t color;
};
static ChipSlot chip_slots[CHIP_COUNT] = {};
static bool chip_slots_valid = false;

static void chip_slot_set(uint8_t slot, const char *icon, uint16_t color) {
  ChipSlot &the_slot = chip_slots[slot];
  const bool show = icon[0] != '\\0';
  if (chip_slots_valid && strcmp(the_slot.icon, icon) == 0 && (!show || the_slot.color == color)) {
    return;  // Slot already shows this chip
  }

  nextion_display->set_component_text(CHIP_NAMES_HOME[slot], icon);
  if (show) {
    nextion_display->set_component_font_color(CHIP_NAMES_HOME[slot], color);
  }
  if (chips_mirror_page) {
    nextion_display->set_component_text(CHIP_NAMES[slot], icon);
    if (show) {
      nextion_display->set_component_font_color(CHIP_NAMES[slot], color);
    }
  }

  strncpy(the_slot.icon, icon, sizeof(the_slot.icon) - 1);
  the_slot.icon[sizeof(the_slot.icon) - 1] = '\\0';
  the_slot.color = color;
}

void chips_invalidate() { chip_slots_valid = false; }

// mdi:blank / mdi:void arrive as U+FFFF (UTF-8 EF BF BF): drawn empty, so they take no slot
static bool chip_icon_blank(const char *icon) { return strcmp(icon, "\\xEF\\xBF\\xBF") == 0; }

void chip_render(uint8_t idx) {
  if (idx >= CHIP_COUNT || nextion_display == nullptr) {
    return;
  }

  // Any chip change can shift the ones to its right, so the whole row is laid out again
  uint8_t slot = 0;
  for (uint8_t i = 0; i < CHIP_COUNT; ++i) {
    const ChipState &the_chip = chip_states[i];
    if (the_chip.visible && the_chip.icon[0] != '\\0' && !chip_icon_blank(the_chip.icon)) {
      chip_slot_set(slot++, the_chip.icon, the_chip.color);
    }
  }
  for (; slot < CHIP_COUNT; ++slot) {
    chip_slot_set(slot, "", 0);
  }
  chip_slots_valid = true;
}
''')
sub('components/nspanel_easy/chips.h', 'void chip_render(uint8_t idx);\n',
    'void chip_render(uint8_t idx);\n\n/// @brief Forget what the display shows, so the next chip_render() rewrites every slot.\nvoid chips_invalidate();\n')
sub('esphome/nspanel_esphome_chips.yaml', '''          for (uint8_t i = 0; i < CHIP_COUNT; ++i) {
            chip_render(i);
          }''', '''          chips_invalidate();  // The display restarted: its slots hold the TFT defaults again
          chip_render(0);      // Lays out the whole row''')
sub('components/nspanel_easy/page_home.cpp', '''  const uint16_t pic = sun_info.is_up ? variant.sun_up : variant.sun_down;
''', '''  uint16_t pic = sun_info.is_up ? variant.sun_up : variant.sun_down;
  // Rounded 2: home has its own copies of the legacy dark pictures, drawn opaque on the weather card
  static constexpr uint16_t HOME_WEATHER_PIC_OFFSET = 134;
  if (current_theme != ThemeMode::LIGHT && pic >= 1 && pic <= 15) {
    pic += HOME_WEATHER_PIC_OFFSET;
  }
''')
sub('esphome/nspanel_esphome_hw_buttons.yaml', '''            background = "pic_background_main";
            fill = XSTR_FILL_CROP_IMAGE;
            left = is_eu ? LabelPosition{47, 286} : LabelPosition{16, 446};
            right = is_eu ? LabelPosition{288, 286} : LabelPosition{184, 446};''',
    '''            background = "home.pic";  // Rounded 2: home has its own background picture
            fill = XSTR_FILL_CROP_IMAGE;
            // Rounded 2: EU labels centred in the pills of the home background (10-191 / 262-443, y 268-317)
            left = is_eu ? LabelPosition{41, 280} : LabelPosition{16, 446};
            right = is_eu ? LabelPosition{293, 280} : LabelPosition{184, 446};''')
sub('esphome/nspanel_esphome_hw_display.yaml', '''          disp1->send_command("call theme_apply");
''', '''          disp1->send_command("call theme_apply");
          // Rounded 2: theme_apply points home at pic_background_main; home has its own background
          static const char *const HOME_CROPPED[] = {
              "time", "date", "outdoor_temp", "indr_temp", "indr_temp_icon", "meridiem",
              "left_bt_text", "right_bt_text", "wifi_icon", "bt_icon",
              "value01", "value01_icon", "value01_label", "value02", "value02_icon", "value02_label",
              "value03", "value03_icon", "value03_label", "value04", "value04_icon", "value04_label",
              "chip_relay1", "chip_relay2", "chip_climate",
              "chip01", "chip02", "chip03", "chip04", "chip05", "chip06", "chip07",
              "bt_notific", "bt_utilities", "bt_entities", "bt_qrcode",
              "button01", "button02", "button03", "button04", "button05", "button06", "button07"};
          static constexpr uint8_t HOME_BACKGROUND_PIC = 134;
          disp1->send_command_printf("home.pic=%" PRIu8, HOME_BACKGROUND_PIC);
          for (const char *name : HOME_CROPPED) {
            disp1->send_command_printf("home.%s.picc=%" PRIu8, name, HOME_BACKGROUND_PIC);
          }
          #ifdef NSPANEL_EASY_USE_WEATHER
          home_weather_resolve();  // theme_apply shifted the home weather picture by 48
          #endif  // NSPANEL_EASY_USE_WEATHER
''')
# 5) Home-Temperaturen: aussen "10°", innen "21,8°" (Rev 13: ohne "innen", das Haus-Icon sagt es)
sub('components/nspanel_easy/page_home.cpp',
    'static void format_temperature(float value, char *out, size_t size) {\n',
    '// Rounded 2: decimals and suffix per component, Celsius without the "C"\n'
    'static void format_temperature(float value, int decimals, const char *suffix, char *out, size_t size) {\n')
sub('components/nspanel_easy/page_home.cpp',
    '  snprintf(buffer, sizeof(buffer), "%.1f%s\\u00b0C", value, separator);\n',
    '  (void) separator;\n'
    '  if (decimals == 0) {\n'
    '    value = roundf(value);\n'
    '    if (value == 0.0f) {\n'
    '      value = 0.0f;  // -0.3 rounds to -0; show "0°"\n'
    '    }\n'
    '  }\n'
    '  snprintf(buffer, sizeof(buffer), "%.*f\\u00b0%s", decimals, value, suffix);\n')
sub('components/nspanel_easy/page_home.cpp',
    '  format_temperature(*value, text, sizeof(text));\n  if (strcmp(indoor_temp_text',
    '  format_temperature(*value, 1, "", text, sizeof(text));\n  if (strcmp(indoor_temp_text')
sub('components/nspanel_easy/page_home.cpp',
    '    format_temperature(*value, text, sizeof(text));\n    if (strcmp(outdoor_temp_text',
    '    format_temperature(*value, 0, "", text, sizeof(text));\n    if (strcmp(outdoor_temp_text')
# 5b) Panel-eigener Fuehler (Doms Innentemperatur) im selben Format
sub('esphome/nspanel_esphome_hw_temperature.yaml',
    '''          snprintf(buffer, sizeof(buffer), "%.1f%s${temp_units}", temp_nspanel->state,
                                                                  id(units_separator).c_str());
''', '''          // Rounded 2: "21,8°", the house icon next to it says "indoor"
          snprintf(buffer, sizeof(buffer), "%.1f\\u00b0", temp_nspanel->state);
''')
# 6) Home-Kacheln: "Wert|Beschriftung" auf value01-04 -> Wert in valueNN, Beschriftung in valueNN_label (Rounded-2-TFT)
sub('esphome/nspanel_esphome_api.yaml', """            action_component_text_list->execute(
              page.c_str(),
              id.c_str(),
              txt_list
            );
""", """            // Rounded 2: "value|caption" on a home value tile also fills its caption valueNN_label
            if (page == "home" && (id == "value01" || id == "value02" || id == "value03" || id == "value04")) {
              const std::string &last = txt_list.back();
              const size_t bar = last.find('|');
              if (bar != std::string::npos) {
                action_component_text->execute(std::string("home"), std::string(id.c_str()) + "_label",
                                               last.substr(bar + 1));
                action_component_text_list->execute(page.c_str(), id.c_str(),
                                                    std::vector<std::string>{last.substr(0, bar)});
                return;
              }
            }  // if home value tile

            action_component_text_list->execute(
              page.c_str(),
              id.c_str(),
              txt_list
            );
""")
# 7) Home (EU): aktive Taste = ganze Pille aus Bild 150 (gelber Rand + Toenung) statt Strich
HOME_PILLS = '''            // Rounded 2: on the EU home page the whole pill shows the state instead of the bar. It is copied
            // from the active (picture 150) or the normal (home.pic) background, then the labels are redrawn.
            static constexpr uint8_t HOME_PILL_ON_PIC = 150;
            struct HomePill {
              uint16_t x, y, w, h;
            };
            static constexpr HomePill HOME_PILLS[2] = {{10, 268, 182, 50}, {262, 268, 182, 50}};
            auto draw_home_pill = [](const HomePill &pill, bool on) {
              char pic[12];
              if (on) {
                snprintf(pic, sizeof(pic), "%" PRIu8, HOME_PILL_ON_PIC);
              } else {
                snprintf(pic, sizeof(pic), "home.pic");
              }
              disp1->send_command_printf("xpic %" PRIu16 ",%" PRIu16 ",%" PRIu16 ",%" PRIu16 ",%" PRIu16 ",%" PRIu16 ",%s",
                                         pill.x, pill.y, pill.w, pill.h, pill.x, pill.y, pic);
            };
'''
sub('esphome/nspanel_esphome_hw_buttons.yaml', '''          // Left button
          if (button_mask & 1 and id(hardware_settings).button_left_enabled) {''',
    HOME_PILLS + '''            if (display_mode_idx == 1 and current_page_id == get_page_id("home")) {
              if (button_mask & 1) {
                draw_home_pill(HOME_PILLS[0], id(hardware_settings).button_left_enabled and
                                                  id(hardware_settings).button_left_state);
              }
              if (button_mask & 2) {
                draw_home_pill(HOME_PILLS[1], id(hardware_settings).button_right_enabled and
                                                  id(hardware_settings).button_right_state);
              }
              refresh_hardware_buttons_labels->execute(false);  // xpic painted over them
              return;
            }  // if (EU home page)

          // Left button
          if (button_mask & 1 and id(hardware_settings).button_left_enabled) {''')
# 7b) Bars fuer home abgewaehlt: Pillen auf den normalen Hintergrund zuruecksetzen
sub('esphome/nspanel_esphome_hw_buttons.yaml', '''              for (const HwButtonBarArea &area : HW_BUTTON_BAR_AREAS[display_mode_index]) {
                if (solid_background) {''', '''              if (display_mode_index == 0 and current_page_id == get_page_id("home")) {
                // Rounded 2: the pills show the state on home, reset both to the normal background
                disp1->send_command("xpic 10,268,182,50,10,268,home.pic");
                disp1->send_command("xpic 262,268,182,50,262,268,home.pic");
                refresh_hardware_buttons_labels->execute(false);
                return;
              }  // if (EU home page)
              for (const HwButtonBarArea &area : HW_BUTTON_BAR_AREAS[display_mode_index]) {
                if (solid_background) {''')
# 7c) Beschriftung einer aktiven Taste auf der getoenten Pille: Hintergrund aus Bild 150
sub('esphome/nspanel_esphome_hw_buttons.yaml', '''          draw_label(left, show ? id(button_left_label) : NO_LABEL, color_left);
          draw_label(right, show ? id(button_right_label) : NO_LABEL, color_right);''',
    '''          // Rounded 2: on the EU home page an active button's label sits on the tinted pill of picture 150
          const bool home_pills = is_eu and current_page_id == get_page_id("home");
          const char *const page_background = background;
          if (home_pills and id(hardware_settings).button_left_enabled and id(hardware_settings).button_left_state) {
            background = "150";
          }
          draw_label(left, show ? id(button_left_label) : NO_LABEL, color_left);
          background = page_background;
          if (home_pills and id(hardware_settings).button_right_enabled and id(hardware_settings).button_right_state) {
            background = "150";
          }
          draw_label(right, show ? id(button_right_label) : NO_LABEL, color_right);''')
# 8) Home: Benachrichtigung sitzt als Status-Icon in der Chip-Spalte (Platz des BT-Icons) -> Chip-Schrift
sub('esphome/nspanel_esphome_page_home.yaml',
    '            disp1->set_component_font(hmi::home::BT_NOTIFIC.name, id(home_custom_buttons_font_id));\n',
    '            // Rounded 2: bt_notific is a status icon in the chip column, it keeps the chip font\n')
sub('esphome/nspanel_esphome_chips.yaml',
    '          disp1->set_component_font(hmi::home::BT_ICON.name,   new_font);\n',
    '          disp1->set_component_font(hmi::home::BT_ICON.name,   new_font);\n'
    '          disp1->set_component_font(hmi::home::BT_NOTIFIC.name, new_font);  // Rounded 2: in the chip column\n')
# 9) Home: Aussentemperatur in Font 6 (72 px) passt fuer drei Zeichen ("28°"); "-10°" wuerde der
#    Nextion abschneiden, dafuer schaltet die Firmware auf Font 5 (48 px) zurueck.
sub('components/nspanel_easy/page_home.cpp',
    '/// @brief Whether the outdoor temperature component is currently shown.\n'
    'static Visibility outdoor_temp_shown = Visibility::UNKNOWN;\n',
    '/// @brief Whether the outdoor temperature component is currently shown.\n'
    'static Visibility outdoor_temp_shown = Visibility::UNKNOWN;\n'
    '\n'
    '/// @brief Rounded 2: the outdoor font the blueprint asked for, and the one last sent.\n'
    'static uint8_t outdoor_temp_font_wanted = UINT8_MAX;\n'
    'static uint8_t outdoor_temp_font_sent = UINT8_MAX;\n'
    '\n'
    '/// @brief Rounded 2: 72 px (font 6) holds three characters such as "28°" in the home layout;\n'
    '/// a longer text such as "-10°" falls back to 48 px (font 5) instead of losing characters.\n'
    'static void home_outdoor_temp_apply_font() {\n'
    '  static constexpr uint8_t FONT_72 = 6;\n'
    '  static constexpr uint8_t FONT_48 = 5;\n'
    '  if (nextion_display == nullptr || outdoor_temp_font_wanted == UINT8_MAX) {\n'
    '    return;\n'
    '  }\n'
    '  const bool wide = strlen(outdoor_temp_text) > 4;  // the degree sign takes two bytes\n'
    '  const uint8_t font = (wide && outdoor_temp_font_wanted == FONT_72) ? FONT_48 : outdoor_temp_font_wanted;\n'
    '  if (font != outdoor_temp_font_sent) {\n'
    '    nextion_display->set_component_font(hmi::home::OUTDOOR_TEMP.name, font);\n'
    '    outdoor_temp_font_sent = font;\n'
    '  }\n'
    '}\n'
    '\n'
    'void home_outdoor_temp_font(uint8_t font) {\n'
    '  outdoor_temp_font_wanted = font;\n'
    '  outdoor_temp_font_sent = UINT8_MAX;\n'
    '  home_outdoor_temp_apply_font();\n'
    '}\n')
sub('components/nspanel_easy/page_home.cpp',
    '      outdoor_temp_text[sizeof(outdoor_temp_text) - 1] = \'\\0\';\n'
    '      nextion_display->set_component_text(hmi::home::OUTDOOR_TEMP.name, outdoor_temp_text);\n',
    '      outdoor_temp_text[sizeof(outdoor_temp_text) - 1] = \'\\0\';\n'
    '      home_outdoor_temp_apply_font();  // Rounded 2: before the text, so it never shows clipped\n'
    '      nextion_display->set_component_text(hmi::home::OUTDOOR_TEMP.name, outdoor_temp_text);\n')
sub('components/nspanel_easy/page_home.h',
    '#endif  // NSPANEL_EASY_USE_WEATHER\n\n#endif  // NSPANEL_EASY_SUBSCRIBE\n',
    '#endif  // NSPANEL_EASY_USE_WEATHER\n\n'
    '/**\n'
    ' * @brief Rounded 2: set the outdoor temperature font the blueprint asks for.\n'
    ' *\n'
    ' * Font 6 (72 px) falls back to font 5 (48 px) while the text has more than three characters.\n'
    ' */\n'
    'void home_outdoor_temp_font(uint8_t font);\n\n'
    '#endif  // NSPANEL_EASY_SUBSCRIBE\n')
sub('esphome/nspanel_esphome_page_home.yaml',
    '            disp1->set_component_font(hmi::home::OUTDOOR_TEMP.name, static_cast<uint8_t>(val));\n',
    '            #ifdef NSPANEL_EASY_SUBSCRIBE\n'
    '            home_outdoor_temp_font(static_cast<uint8_t>(val));  // Rounded 2: falls back to 48 px for "-10°"\n'
    '            #else\n'
    '            disp1->set_component_font(hmi::home::OUTDOOR_TEMP.name, static_cast<uint8_t>(val));\n'
    '            #endif  // NSPANEL_EASY_SUBSCRIBE\n')
print("ok")
