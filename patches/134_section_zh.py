#!/usr/bin/env python3
"""Properties panel section headings in Chinese: Layer Transform, Text Animation, Paragraph.

`section_header` painted its title straight to the painter, so the Properties panel kept showing
"Layer Transform" however complete the translation table was. The heading now goes through the
table (the accessible name too), like every other label.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SECTION_ZH_V1"

OLD = '''    p.text(pos2(x0, y + ROW_H / 2.0), Align2::LEFT_CENTER, title, Tokens::semibold(12.0), t.text);
    let r = Rect::from_min_size(pos2(x0, y), vec2(w, ROW_H));
    app.auto.add(auto, r, title);
'''
NEW = '''    // EFFECTCRAFT_OURS_SECTION_ZH_V1 — 图层变换 / 文本动画 / 段落 …
    let title = crate::i18n::tr(title);
    p.text(pos2(x0, y + ROW_H / 2.0), Align2::LEFT_CENTER, title, Tokens::semibold(12.0), t.text);
    let r = Rect::from_min_size(pos2(x0, y), vec2(w, ROW_H));
    app.auto.add(auto, r, title);
'''


MARKERS_OLD = 'let r = ui.small_button("+ Parameter");'
MARKERS_NEW = 'let r = ui.small_button(crate::i18n::tr("+ Parameter"));'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/properties.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("section headings already translated")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("property section headings go through the table")

    markers = root / "crates/ui-egui/src/panels/markers_ui.rs"
    m = markers.read_text(encoding="utf-8")
    if MARKERS_NEW not in m and m.count(MARKERS_OLD) == 1:
        markers.write_text(m.replace(MARKERS_OLD, MARKERS_NEW, 1), encoding="utf-8")
        print("markers + Parameter button goes through the table")


if __name__ == "__main__":
    main()
