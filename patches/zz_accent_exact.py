#!/usr/bin/env python3
"""选中底色回到「轻微带主题色」的默认观感（纯色会把文字压住）。

Pure accent fills made the selected labels hard to read, so selection goes back to the theme's own
blend: the row keeps its dark ground with a hint of the accent, exactly like the rest of the interface.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCENT_EXACT_V1"

EDITS = [
    ("            t.row_selected = t.row.lerp_to_gamma(rgb, 0.58);",
     "            t.row_selected = t.row.lerp_to_gamma(rgb, 0.38);"),
    ("            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.50);",
     "            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.30);"),
    ("            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.68);",
     "            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.42);"),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("selection already back to the soft tint")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("selection uses the soft accent tint again")


if __name__ == "__main__":
    main()
