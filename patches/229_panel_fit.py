#!/usr/bin/env python3
"""面板尺寸按内容算：9 个方块三列三行 + 标题，之前底部被裁掉一截。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_FIT_V1"
OLD = "    let size = egui::vec2(196.0, 132.0);\n"
NEW = "    let size = egui::vec2(196.0, 184.0);\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panel already fits")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("panel is tall enough for three rows")


if __name__ == "__main__":
    main()
