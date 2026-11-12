#!/usr/bin/env python3
"""Dock/panel context menu in Chinese (Close Frame, Undock Frame, Maximize Frame, ...)."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DOCK_MENU_V1"
EDITS = [
    ('style.float_label = "Undock Panel".into();', 'style.float_label = "取消停靠面板".into();'),
    ('style.float_group_label = "Undock Frame".into();', 'style.float_group_label = "取消停靠面板组".into();'),
    ('style.close_group_label = "Close Frame".into();', 'style.close_group_label = "关闭面板组".into();'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("dock menu already translated")
        return
    changed = 0
    for old, new in EDITS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
    if changed != 3:
        raise SystemExit(f"only {changed} dock labels matched")
    src = src.replace("Style {", "// " + MARKER + "\nStyle {", 1)
    path.write_text(src, encoding="utf-8")
    print("dock menu labels are Chinese")


if __name__ == "__main__":
    main()
