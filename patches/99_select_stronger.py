#!/usr/bin/env python3
"""选中底色更明显：行选中 / 时间轴选中 / 效果标题选中 的主题色混合比例调高（之前偏暗）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_STRONGER_V1"

EDITS = [('            t.row_selected = t.row.lerp_to_gamma(rgb, 0.38);', '            t.row_selected = t.row.lerp_to_gamma(rgb, 0.58);'), ('            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.30);', '            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.50);'), ('            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.42);', '            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.68);')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("selection already stronger")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("selection highlights carry more of the accent")


if __name__ == "__main__":
    main()
