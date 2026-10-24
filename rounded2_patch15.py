r"""Rounded-2-Patch 15 fuer NSPanel Easy. Aufruf im Repo-Root nach rounded2_patch14.py: python ../rounded2_patch15.py

Button-Seiten: die belegten Buttons ruecken von oben links nach, Luecken in der Blueprint-
Belegung (z. B. nur button02 und button05) bleiben nicht mehr leer stehen. Die Firmware rechnet
in beide Richtungen um (components/nspanel_easy/button_slots.h, liegt schon im Repo):
- is_buttonpageNN=Maske (Blueprint, mem command) -> Firmware merkt sich die Maske, die TFT
  bekommt die lueckenlose Maske.
- Aktion `button` (Darstellung) -> belegter Slot wird auf seine Position umgeschrieben.
- component_val confirm (Bestaetigungs-Bits der aktuellen Seite) -> auf Positionen umgerechnet.
- Klicks der TFT (short/long, auch aus der Bestaetigungsseite) -> zurueck auf den belegten Slot.
Blueprint und TFT bleiben unveraendert. Solange keine Maske bekannt ist, wird nichts umgerechnet.
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


# Maske merken, TFT bekommt die lueckenlose Maske
sub('esphome/nspanel_esphome_api.yaml', r'''            for (const auto& cmd : txt_list) {
              if (cmd.empty()) continue;
              action_component_text->execute(page, component, cmd);
            }''', r'''            for (const auto& cmd : txt_list) {
              if (cmd.empty()) continue;
              // Rounded 2: configured buttons move up, the TFT only sees the compacted mask
              if (cmd.size() > 16 && cmd.compare(0, 3, "is_") == 0 && cmd[15] == '=') {
                const int page_idx = nspanel_easy::buttonpage_index(cmd.substr(3, 12));
                const auto mask = parse_number<int>(cmd.substr(16));
                if (page_idx >= 0 && mask.has_value()) {
                  const uint8_t m = static_cast<uint8_t>(*mask);
                  nspanel_easy::buttonpage_masks[page_idx] = m;
                  const uint8_t compact = static_cast<uint8_t>((1U << __builtin_popcount(m)) - 1);
                  ESP_LOGD("${TAG_API}", "%s: slots 0x%02X shown as 0x%02X", cmd.substr(3, 12).c_str(), m, compact);
                  action_component_text->execute(page, component, cmd.substr(0, 16) + std::to_string(compact));
                  continue;
                }
              }
              action_component_text->execute(page, component, cmd);
            }''')

# Bestaetigungs-Bits der aktuellen Button-Seite auf Positionen umrechnen
sub('esphome/nspanel_esphome_api.yaml', r'''        - lambda: |-
            action_component_val->execute(
              page.c_str(),
              id.c_str(),
              val
            );''', r'''        - lambda: |-
            int32_t value = val;
            // Rounded 2: the confirm bits of a button page follow the buttons that moved up
            if (id == "confirm") {
              const int page_idx = nspanel_easy::buttonpage_index(page.empty() ? current_page->state : page);
              if (page_idx >= 0) {
                value = nspanel_easy::buttonpage_compact_bits(nspanel_easy::buttonpage_masks[page_idx],
                                                              static_cast<uint8_t>(val));
              }
            }
            action_component_val->execute(
              page.c_str(),
              id.c_str(),
              value
            );''')

# Darstellung: belegter Slot -> Position
sub('esphome/nspanel_esphome_page_buttons.yaml', r'''            action_button->execute(
              page_id,
              id.c_str(),''', r'''            // Rounded 2: configured buttons move up to close the gaps
            std::string button_name = id.c_str();
            const int page_idx = buttonpage_index(page.c_str());
            const int slot = buttonpage_slot(button_name);
            if (page_idx >= 0 && slot >= 0) {
              const int position = buttonpage_position(buttonpage_masks[page_idx], slot);
              if (position < 0) {
                ESP_LOGW("${TAG_PAGE_BUTTONS}", "%s.%s is not configured, skipping", page.c_str(), id.c_str());
                return;
              }
              button_name = buttonpage_slot_name(position);
            }

            action_button->execute(
              page_id,
              button_name.c_str(),''')

# Klicks: Position -> belegter Slot
sub('esphome/nspanel_esphome_hw_display.yaml', r'''              // A page package may claim the click, e.g. to ask for confirmation
              if (click_interceptor and click_interceptor(page, event, params[2])) {''', r'''              // Rounded 2: a click on a button page reports the configured slot, not the position
              std::string component = params[2];
              const int page_idx = buttonpage_index(page);
              const int position = buttonpage_slot(component);
              if (page_idx >= 0 && position >= 0) {
                const int slot = buttonpage_configured_slot(buttonpage_masks[page_idx], position);
                if (slot < 0) {
                  ESP_LOGW("${TAG_HW_DISPLAY}", "%s: nothing shown at %s", page.c_str(), component.c_str());
                  return;
                }
                component = buttonpage_slot_name(slot);
              }

              // A page package may claim the click, e.g. to ask for confirmation
              if (click_interceptor and click_interceptor(page, event, component)) {''')
sub('esphome/nspanel_esphome_hw_display.yaml', r'''                {"command", event.c_str()},
                {"component", params[2].c_str()}''', r'''                {"command", event.c_str()},
                {"component", component.c_str()}''')
print("ok")
