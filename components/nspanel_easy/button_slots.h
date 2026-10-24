// button_slots.h

#pragma once

#include <cstdint>
#include <cstdio>
#include <string>

/**
 * @file button_slots.h
 * @brief Rounded 2: configured buttons on a button page move up to close the gaps.
 *
 * The Blueprint addresses a button by its configured slot ("buttonpage01", "button05"). The
 * firmware shows the configured slots one after another from the top left and translates
 * in both directions: renders and the confirm mask on the way to the display, clicks on the
 * way back. Home Assistant and the Blueprint only ever see the configured slot.
 */

namespace esphome::nspanel_easy {

/// Configured slots per button page, as sent by the Blueprint (is_buttonpageNN). 0 = not known yet.
inline uint8_t buttonpage_masks[4] = {0, 0, 0, 0};

/// "buttonpage01" to "buttonpage04" -> 0 to 3, anything else -> -1.
inline int buttonpage_index(const std::string &page) {
  if (page.size() != 12 || page.compare(0, 10, "buttonpage") != 0) return -1;
  if (page[10] != '0' || page[11] < '1' || page[11] > '4') return -1;
  return page[11] - '1';
}

/// "button01" to "button08" -> 0 to 7, anything else -> -1.
inline int buttonpage_slot(const std::string &component) {
  if (component.size() != 8 || component.compare(0, 6, "button") != 0) return -1;
  if (component[6] != '0' || component[7] < '1' || component[7] > '8') return -1;
  return component[7] - '1';
}

inline std::string buttonpage_slot_name(int slot) {
  char name[9];
  snprintf(name, sizeof(name), "button%02d", slot + 1);
  return name;
}

/// Configured slot -> shown position; -1 when the slot is not configured. Unknown mask: unchanged.
inline int buttonpage_position(uint8_t mask, int slot) {
  if (mask == 0) return slot;
  if ((mask & (1U << slot)) == 0) return -1;
  return __builtin_popcount(mask & ((1U << slot) - 1));
}

/// Shown position -> configured slot; -1 when nothing is shown there. Unknown mask: unchanged.
inline int buttonpage_configured_slot(uint8_t mask, int position) {
  if (mask == 0) return position;
  for (int slot = 0; slot < 8; slot++) {
    if ((mask & (1U << slot)) != 0 && position-- == 0) return slot;
  }
  return -1;
}

/// Bits per configured slot (e.g. the confirm mask) -> bits per shown position.
inline uint8_t buttonpage_compact_bits(uint8_t mask, uint8_t bits) {
  if (mask == 0) return bits;
  uint8_t out = 0;
  for (int slot = 0, position = 0; slot < 8; slot++) {
    if ((mask & (1U << slot)) == 0) continue;
    if ((bits & (1U << slot)) != 0) out |= 1U << position;
    position++;
  }
  return out;
}

}  // namespace esphome::nspanel_easy
