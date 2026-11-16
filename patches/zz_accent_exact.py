#!/usr/bin/env python3
"""选中色用 After Effects 的默认蓝灰（不跟主题色走，主题色只管按钮/焦点/播放头/波形）。

AE's own selection is a muted steel blue on the dark interface and a pale blue on the light one; the
custom accent must not repaint it, or selected rows turn muddy.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AE_SELECTION_V1"

EDITS = [
    ("            t.row_selected = t.row.lerp_to_gamma(rgb, 0.58);",
     "            let (sel_row, sel_graph, sel_header) = if matches!(kind, ThemeKind::Light) {\n"
     "                (Color32::from_rgb(0xa8, 0xc6, 0xf0), Color32::from_rgb(0xc8, 0xdc, 0xf4), Color32::from_rgb(0x9c, 0xbc, 0xe8))\n"
     "            } else {\n"
     "                (Color32::from_rgb(0x2f, 0x45, 0x5e), Color32::from_rgb(0x27, 0x39, 0x4e), Color32::from_rgb(0x36, 0x50, 0x6c))\n"
     "            };\n"
     "            t.row_selected = sel_row;"),
    ("            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.50);",
     "            t.tl_graph_selected = sel_graph;"),
    ("            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.68);",
     "            t.fx_header_active = sel_header;"),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("AE selection colours already in place")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("selection uses After Effects' default colours")


if __name__ == "__main__":
    main()
