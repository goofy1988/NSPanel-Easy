"""Rounded-2-Patch 10 fuer NSPanel Easy: Timer auf der Uhrkarte (Plan: timer_patch10_plan.md).
Aufruf im Repo-Root nach rounded2_patch.py: python ../rounded2_patch10.py

HA sendet timer_set(state, remaining), das Panel zaehlt selbst, blinkt nach Ablauf 1 min rot
(Bild 151) und meldet "stop" als Event esphome.nspanel_easy (type timer) an HA.
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


DT = 'esphome/nspanel_esphome_datetime.yaml'
sub(DT, '''  TIME_FORMAT_DEFAULT: "%H:%M"
''', '''  TIME_FORMAT_DEFAULT: "%H:%M"
  R2_TIMER_TEXT_ACTIVE: Timer  # Rounded 2 timer: date line while running, paused, finished
  R2_TIMER_TEXT_PAUSED: Timer pausiert
  R2_TIMER_TEXT_FINISHED: Abgelaufen
''')
sub(DT, '''          disp1->set_component_text("home.meridiem", has_meridiem ? meridiem_text : " ");
          disp1->set_component_text("home.time", now.strftime(time_format_str).c_str());''',
    '''          disp1->set_component_text("home.meridiem", has_meridiem ? meridiem_text : " ");
          // Rounded 2: while the timer view owns the clock card, the timer writes time and date
          if (id(r2_timer_state) != 0 and id(r2_timer_view)) return;
          disp1->set_component_text("home.time", now.strftime(time_format_str).c_str());''')
sub(DT, '''time:  # Keeps time display updated
''', r'''  # Rounded 2 timer: the clock card shows a Home Assistant timer (state 0 idle, 1 active, 2 paused, 3 alarm)
  - id: r2_timer_render
    mode: restart
    then:
      - lambda: |-
          if (system_flags.tft_upload_active or current_page_id != get_page_id("home")) return;
          const uint8_t st = id(r2_timer_state);
          if (st == 0 or !id(r2_timer_view)) return;
          int32_t secs = 0;
          if (st == 1) {
            const int32_t left_ms = static_cast<int32_t>(id(r2_timer_end_ms) - millis());
            secs = left_ms > 0 ? (left_ms + 999) / 1000 : 0;
          } else if (st == 2) {
            secs = id(r2_timer_remaining);
          }
          if (secs == id(r2_timer_shown) and !id(r2_timer_dirty)) return;
          id(r2_timer_shown) = secs;
          char text[16];
          if (secs < 3600) {
            snprintf(text, sizeof(text), "%" PRId32 ":%02" PRId32, secs / 60, secs % 60);
          } else {  // from one hour on hours and minutes only
            snprintf(text, sizeof(text), "%" PRId32 ":%02" PRId32 " h", secs / 3600, (secs / 60) % 60);
          }
          const uint8_t font = secs >= 36000 ? 5 : 6;  // "23:59 h" is wider than the card in 72 px
          if (font != id(r2_timer_font)) {
            disp1->set_component_font(hmi::home::TIME.name, font);
            id(r2_timer_font) = font;
          }
          disp1->set_component_text(hmi::home::TIME.name, text);
          if (id(r2_timer_dirty)) {
            disp1->set_component_text(hmi::home::DATE.name,
                                      st == 1 ? "${R2_TIMER_TEXT_ACTIVE}" :
                                      st == 2 ? "${R2_TIMER_TEXT_PAUSED}" : "${R2_TIMER_TEXT_FINISHED}");
            id(r2_timer_dirty) = false;
          }

  - id: r2_timer_card
    mode: restart
    parameters:
      red: bool
    then:
      - lambda: |-
          // Clock card from picture 151 (red) or the page background, then its components on top
          if (current_page_id != get_page_id("home")) return;
          disp1->send_command_printf("xpic 10,10,212,140,10,10,%s", red ? "151" : "home.pic");
          static const char *const parts[] = {"time", "date", "chip_relay1", "chip_relay2", "chip_climate", "chip01"};
          for (const char *part : parts) {
            disp1->send_command_printf("%s.picc=%s", part, red ? "151" : "134");
          }

  - id: r2_timer_end
    mode: restart
    parameters:
      notify: bool
    then:
      - lambda: |-
          const bool was_alarm = id(r2_timer_state) == 3;
          const bool owned = id(r2_timer_state) != 0 and id(r2_timer_view);
          id(r2_timer_state) = 0;
          if (notify) fire_ha_event("timer", {{"action", "stop"}});
          if (current_page_id != get_page_id("home")) return;
          disp1->send_command("settings_timer.tim=1000");  // long press opens the settings again
          if (was_alarm) r2_timer_card->execute(false);
          if (owned) {
            disp1->set_component_font(hmi::home::TIME.name, 6);
            id(r2_timer_font) = 6;
            refresh_datetime->execute();
          }

  - id: r2_timer_alarm
    mode: restart
    then:
      - lambda: |-
          id(r2_timer_state) = 3;
          id(r2_timer_view) = true;
          id(r2_timer_dirty) = true;
          id(r2_timer_shown) = -1;
          id(r2_timer_alarm_until) = millis() + 60000;  // blink for one minute
          id(r2_timer_blink) = false;
          wakeup->execute(true);
          if (current_page_id != get_page_id("home")) {
            goto_page->execute(get_page_id("home"));
          } else {
            disp1->send_command("settings_timer.tim=65000");
            r2_timer_render->execute();
          }

  - id: !extend page_change
    then:
      - lambda: |-
          if (!is_home_page() or id(r2_timer_state) == 0) return;
          // settings_timer is local to home, every page load resets it to one second
          disp1->send_command("settings_timer.tim=65000");
          id(r2_timer_font) = 6;
          id(r2_timer_dirty) = true;
          id(r2_timer_shown) = -1;
          r2_timer_render->execute();

time:  # Keeps time display updated
''')
sub(DT, '''            refresh_datetime->execute();
...
''', r'''            refresh_datetime->execute();

globals:  # Rounded 2 timer
  - id: r2_timer_state  # 0 idle, 1 active, 2 paused, 3 alarm
    type: uint8_t
    restore_value: false
    initial_value: '0'
  - id: r2_timer_view  # true: the clock card shows the timer, false: the clock
    type: bool
    restore_value: false
    initial_value: 'true'
  - id: r2_timer_dirty  # the date line needs the state text
    type: bool
    restore_value: false
    initial_value: 'false'
  - id: r2_timer_end_ms
    type: uint32_t
    restore_value: false
    initial_value: '0'
  - id: r2_timer_remaining
    type: int32_t
    restore_value: false
    initial_value: '0'
  - id: r2_timer_shown
    type: int32_t
    restore_value: false
    initial_value: '-1'
  - id: r2_timer_font
    type: uint8_t
    restore_value: false
    initial_value: '6'
  - id: r2_timer_alarm_until
    type: uint32_t
    restore_value: false
    initial_value: '0'
  - id: r2_timer_blink
    type: bool
    restore_value: false
    initial_value: 'false'
  - id: r2_timer_press_ms
    type: uint32_t
    restore_value: false
    initial_value: '0'

interval:
  - interval: 500ms
    then:
      - lambda: |-
          const uint8_t st = id(r2_timer_state);
          if (st == 1) {
            if (static_cast<int32_t>(id(r2_timer_end_ms) - millis()) <= 0) {
              r2_timer_alarm->execute();
            } else {
              r2_timer_render->execute();
            }
          } else if (st == 3) {
            if (static_cast<int32_t>(id(r2_timer_alarm_until) - millis()) <= 0) {
              r2_timer_end->execute(false);
              return;
            }
            r2_timer_render->execute();
            id(r2_timer_blink) = !id(r2_timer_blink);
            r2_timer_card->execute(id(r2_timer_blink));
          }

display:
  - id: !extend disp1
    on_touch:
      then:
        - lambda: |-
            // Rounded 2 timer: tap the clock card to switch clock and timer, hold it to stop the timer
            const uint8_t st = id(r2_timer_state);
            if (st == 0) return;
            if (st == 3) {
              if (!touch_event) r2_timer_end->execute(true);  // any tap ends the alarm
              return;
            }
            if (page_id != get_page_id("home") or
                (component_id != hmi::home::TIME.id and component_id != hmi::home::DATE.id)) return;
            if (touch_event) {
              id(r2_timer_press_ms) = millis();
              return;
            }
            if (millis() - id(r2_timer_press_ms) >= 800) {
              r2_timer_end->execute(true);
              return;
            }
            id(r2_timer_view) = !id(r2_timer_view);
            if (id(r2_timer_view)) {
              id(r2_timer_dirty) = true;
              id(r2_timer_shown) = -1;
              r2_timer_render->execute();
            } else {
              disp1->set_component_font(hmi::home::TIME.name, 6);
              id(r2_timer_font) = 6;
              refresh_datetime->execute();
            }

api:
  actions:
    # Rounded 2: show a Home Assistant timer on the clock card (blueprint "Rounded 2 Panel-Timer")
    - action: timer_set
      variables:
        state: string  # active, paused, finished or idle
        remaining: int  # seconds left (active, paused)
      then:
        - lambda: |-
            ESP_LOGD("${TAG_DATETIME}", "Action: timer_set %s %" PRId32, state.c_str(), static_cast<int32_t>(remaining));
            const uint8_t st = id(r2_timer_state);
            if (state == "active" or state == "paused") {
              if (st == 3) r2_timer_end->execute(false);  // a new timer replaces the alarm
              if (id(r2_timer_state) == 0) id(r2_timer_view) = true;
              const uint8_t new_st = (state == "active") ? 1 : 2;
              if (new_st != id(r2_timer_state)) id(r2_timer_dirty) = true;
              id(r2_timer_state) = new_st;
              id(r2_timer_remaining) = remaining > 0 ? remaining : 0;
              id(r2_timer_end_ms) = millis() + static_cast<uint32_t>(id(r2_timer_remaining)) * 1000;
              id(r2_timer_shown) = -1;
              if (current_page_id == get_page_id("home")) disp1->send_command("settings_timer.tim=65000");
              r2_timer_render->execute();
            } else if (state == "finished") {
              if (st != 3) r2_timer_alarm->execute();
            } else if (state == "idle") {
              if (st != 0) r2_timer_end->execute(false);
            }
...
''')
print("ok")
