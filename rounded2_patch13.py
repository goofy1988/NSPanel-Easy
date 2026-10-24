r"""Rounded-2-Patch 13 fuer NSPanel Easy. Aufruf im Repo-Root nach rounded2_patch12.py: python ../rounded2_patch13.py

Button-Karten: der Nextion richtet mehrzeiligen Text als Block aus, nicht je Zeile. Bei
"Trigger\rGaragentor" stehen deshalb beide Zeilen links buendig untereinander. Die Firmware
rueckt kuerzere Zeilen mit Leerzeichen ein (Font 0: Zeichen im Mittel 7 px, Leerzeichen 4 px).
Die HMI braucht dafuer txt_maxl 40 an buttonNNtext (pages_assets.py).
"""
def sub(path, old, new):
    s = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if s.count(old) != 1:
        raise SystemExit(f"{path}: {s.count(old)} Treffer statt 1")
    open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


sub('esphome/nspanel_esphome_page_buttons.yaml', r'''          if (is_page_render) {
            disp1->set_component_text(comp_text, wrapText(label.c_str(), 10, ${LANG_BYTES_PER_CHAR}).c_str());
          }''', r'''          if (is_page_render) {
            // Rounded 2: the Nextion centers a multi-line text as a block, so shorter lines are
            // indented with spaces (font 0: a character is about 7 px wide, a space 4 px)
            const std::string wrapped = wrapText(label.c_str(), 10, ${LANG_BYTES_PER_CHAR});
            std::vector<std::string> lines;
            size_t from = 0;
            for (size_t at; (at = wrapped.find("\\r", from)) != std::string::npos; from = at + 2) {
              lines.push_back(wrapped.substr(from, at - from));
            }
            lines.push_back(wrapped.substr(from));
            auto chars = [](const std::string &s) {
              size_t n = 0;
              for (unsigned char c : s) n += (c & 0xC0) != 0x80;
              return n;
            };
            size_t widest = 0;
            for (const auto &line : lines) widest = std::max(widest, chars(line));
            std::string centered;
            for (size_t i = 0; i < lines.size(); i++) {
              if (i > 0) centered += "\\r";
              centered.append(((widest - chars(lines[i])) * 7 + 4) / 8, ' ');
              centered += lines[i];
            }
            disp1->set_component_text(comp_text, centered.c_str());
          }''')
print("ok")
