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

void chip_render(uint8_t idx) {
  if (idx >= CHIP_COUNT || nextion_display == nullptr) {
    return;
  }

  // Any chip change can shift the ones to its right, so the whole row is laid out again
  uint8_t slot = 0;
  for (uint8_t i = 0; i < CHIP_COUNT; ++i) {
    const ChipState &the_chip = chip_states[i];
    if (the_chip.visible && the_chip.icon[0] != '\\0') {
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
            // Rounded 2: EU labels centred in the pills of the home background (y 266-318)
            left = is_eu ? LabelPosition{47, 280} : LabelPosition{16, 446};
            right = is_eu ? LabelPosition{288, 280} : LabelPosition{184, 446};''')
sub('esphome/nspanel_esphome_hw_display.yaml', '''          disp1->send_command("call theme_apply");
''', '''          disp1->send_command("call theme_apply");
          // Rounded 2: theme_apply points home at pic_background_main; home has its own background
          static const char *const HOME_CROPPED[] = {
              "time", "date", "outdoor_temp", "indr_temp", "indr_temp_icon", "meridiem",
              "left_bt_text", "right_bt_text", "wifi_icon", "bt_icon",
              "value01", "value01_icon", "value02", "value02_icon",
              "value03", "value03_icon", "value04", "value04_icon",
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
print("ok")
