#!/usr/bin/env python3
"""Tighter chrome so the picture gets the room: less padding, one comp name, no repeated prefix.

Nothing is removed that can be clicked. The heights that only hold a label shrink, the tab strip
and the panel gap shrink, and the viewer's tab reads "合成1" instead of "合成 合成1" (the panel name
and the composition's name were both prefixed with 合成).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIGHT_CHROME_V1"

TIMELINE_OLD = """    let header_h = 48.0;
    let ruler_h = 34.0;
    let colhdr_h = 22.0;
    let footer_h = 24.0;
"""
TIMELINE_NEW = """    // EFFECTCRAFT_OURS_TIGHT_CHROME_V1 — 只压留白，不删控件：每个数字都还放得下里面的东西
    let header_h = 40.0;
    let ruler_h = 28.0;
    let colhdr_h = 18.0;
    let footer_h = 20.0;
"""

THEME_OLD = "            gap: 4.0,\n            tab_h: 30.0,\n            row_h: 19.0,\n"
THEME_NEW = "            // EFFECTCRAFT_OURS_TIGHT_CHROME_V1 — 面板间隙 4→2、标签条 30→24\n            gap: 2.0,\n            tab_h: 24.0,\n            row_h: 19.0,\n"

TITLE_OLD = """    Some(format!("{} {}", crate::i18n::command_label("window.panel", "Composition"), app.session.project.item(c)?.name))
"""
TITLE_NEW = """    // EFFECTCRAFT_OURS_TIGHT_CHROME_V1 — 面板名已经是「预览」，再套一层「合成」就成了「合成 合成1」
    Some(app.session.project.item(c)?.name.clone())
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    timeline = root / "crates/ui-egui/src/panels/timeline.rs"
    src = timeline.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(TIMELINE_OLD) != 1:
            raise SystemExit(f"timeline geometry anchor: {src.count(TIMELINE_OLD)}")
        timeline.write_text(src.replace(TIMELINE_OLD, TIMELINE_NEW, 1), encoding="utf-8")
        print("timeline chrome is 14 px shorter")

    theme = root / "crates/ui-egui/src/theme.rs"
    src = theme.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(THEME_OLD) != 1:
            raise SystemExit(f"theme anchor: {src.count(THEME_OLD)}")
        theme.write_text(src.replace(THEME_OLD, THEME_NEW, 1), encoding="utf-8")
        print("tabs 24 px, panel gap 2 px")

    viewers = root / "crates/ui-egui/src/panels/viewers.rs"
    src = viewers.read_text(encoding="utf-8")
    if TITLE_OLD in src:
        viewers.write_text(src.replace(TITLE_OLD, TITLE_NEW, 1), encoding="utf-8")
        print("viewer tab is the composition name alone")


if __name__ == "__main__":
    main()
