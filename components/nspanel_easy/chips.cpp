// chips.cpp

#ifdef NSPANEL_EASY_CHIPS

#include "chips.h"
#include "nextion_components.h"

#include "esphome/components/nextion/nextion.h"

#include <string>

#ifdef NSPANEL_EASY_SUBSCRIBE
#include "esphome/core/log.h"
#endif  // NSPANEL_EASY_SUBSCRIBE

namespace esphome::nspanel_easy {

static const char *const TAG = "nspanel.chips";

ChipState chip_states[CHIP_COUNT] = {};
bool chips_mirror_page = false;

// Rounded 2: visible chips are packed to the left, so a hidden chip leaves no gap.
// Display slot n shows the n-th visible chip; the slot cache skips redundant writes.
struct ChipSlot {
  char icon[4];
  uint16_t color;
};
static ChipSlot chip_slots[CHIP_COUNT] = {};
static bool chip_slots_valid = false;

static void chip_slot_set(uint8_t slot, const char *icon, uint16_t color) {
  ChipSlot &the_slot = chip_slots[slot];
  const bool show = icon[0] != '\0';
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
  the_slot.icon[sizeof(the_slot.icon) - 1] = '\0';
  the_slot.color = color;
}

void chips_invalidate() { chip_slots_valid = false; }

// mdi:blank / mdi:void arrive as U+FFFF (UTF-8 EF BF BF): drawn empty, so they take no slot
static bool chip_icon_blank(const char *icon) { return strcmp(icon, "\xEF\xBF\xBF") == 0; }

void chip_render(uint8_t idx) {
  if (idx >= CHIP_COUNT || nextion_display == nullptr) {
    return;
  }

  // Any chip change can shift the ones to its right, so the whole row is laid out again
  uint8_t slot = 0;
  for (uint8_t i = 0; i < CHIP_COUNT; ++i) {
    const ChipState &the_chip = chip_states[i];
    if (the_chip.visible && the_chip.icon[0] != '\0' && !chip_icon_blank(the_chip.icon)) {
      chip_slot_set(slot++, the_chip.icon, the_chip.color);
    }
  }
  for (; slot < CHIP_COUNT; ++slot) {
    chip_slot_set(slot, "", 0);
  }
  chip_slots_valid = true;
}

#ifdef NSPANEL_EASY_SUBSCRIBE

void chip_sub_render(const SubBinding &binding, const SubRuntime &rt, const char *state, bool visible) {
  const uint8_t idx = find_chip_index(binding.component);
  if (idx == UINT8_MAX) {
    ESP_LOGW(TAG, "'%s' is not a chip component", binding.component);
    return;
  }

  if (nextion_display == nullptr) {
    return;  // Boot has not handed the display over yet
  }

  ChipState &the_chip = chip_states[idx];
  the_chip.subscribed = true;  // Blocks blueprint pushes for this slot

  // Nothing to draw until the blueprint has pushed appearance for this session.
  // Appearance is not persisted, so a chip stays hidden after a boot until then.
  if (!rt.has_appearance) {
    return;
  }

  bool changed = false;

  if (visible) {
    const bool active = (rt.last_state == SUB_STATE_ON);
    const char *icon = active ? rt.icon_on : rt.icon_off;
    uint16_t color = active ? rt.color_on : rt.color_off;

    // An icon pushed by the blueprint wins; otherwise resolve from the domain
    // and state, which is what the multi-state domains rely on.
    if (icon[0] == '\0') {
      const SubAppearance look = resolve_sub_appearance(static_cast<SubDomain>(binding.domain), binding.device_class,
                                                        state, rt.color_on, rt.color_off);
      if (look.icon != nullptr) {
        icon = look.icon;
        color = look.color;
      }
    }

    if (icon[0] == '\0') {
      ESP_LOGW(TAG, "%s has no icon, keeping it hidden", binding.component);
      return;
    }

    if (strcmp(the_chip.icon, icon) != 0) {
      strncpy(the_chip.icon, icon, sizeof(the_chip.icon) - 1);
      the_chip.icon[sizeof(the_chip.icon) - 1] = '\0';
      changed = true;
    }
    if (the_chip.color != color) {
      the_chip.color = color;
      changed = true;
    }
  }  // if visible — appearance is left untouched while hidden

  if (the_chip.visible != visible) {
    the_chip.visible = visible;
    changed = true;
  }

  if (changed) {
    chip_render(idx);
  }
}

#endif  // NSPANEL_EASY_SUBSCRIBE

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_CHIPS
