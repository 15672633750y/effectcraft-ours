#!/usr/bin/env python3
"""曲线窗口不显示控制点：图里只有一条线，直接按在线上拖就能改形状。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LINE_ONLY_V1"

EDITS = [('            // 两个可拖的圆点：左边管前段，右边管后段。\n            let ends = [pos2(px(pts[0]), pyv(pts[1])), pos2(px(pts[2]), pyv(pts[3]))];\n            for h in ends.iter() {\n                ui.painter().circle_filled(*h, 5.0, t.accent);\n                ui.painter().circle_stroke(*h, 5.0, egui::Stroke::new(1.2, t.panel_bg));\n            }\n', '            // EFFECTCRAFT_OURS_LINE_ONLY_V1 — 不画手柄，整条线就是可拖的地方\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("handles already gone")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("curve draws no handles")


if __name__ == "__main__":
    main()
