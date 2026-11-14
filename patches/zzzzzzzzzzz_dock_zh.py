#!/usr/bin/env python3
"""The three dock context-menu items that were still English: Move Group To, Close Other Panels in
Group, Maximize Frame. The docking library (craft_ui) exposes their labels on the style; nothing
ever set them. Runs after 54_dock_menu_zh.py, which translates the other labels."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DOCK_ZH_V1"

ANCHOR = '    style.close_group_label = "关闭面板组".into();'
ADD = '''
    // EFFECTCRAFT_OURS_DOCK_ZH_V1 — 面板组右键菜单的其余三项
    style.maximize_label = "最大化面板组".into();
    style.close_others_label = "关闭组内其他面板".into();
    style.move_group_label = "移动面板组到".into();
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("dock menu already complete")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + ADD, 1)
    path.write_text(src, encoding="utf-8")
    print("dock menu: maximize / close others / move group are Chinese")


if __name__ == "__main__":
    main()
