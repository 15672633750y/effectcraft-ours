#!/usr/bin/env python3
"""选中色严格等于外观里设的自定义色（不再和灰底混合）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCENT_EXACT_V1"

EDITS = [('            t.row_selected = t.row.lerp_to_gamma(rgb, 0.58);', '            t.row_selected = rgb;'), ('            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.50);', '            t.tl_graph_selected = rgb;'), ('            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.68);', '            t.fx_header_active = rgb;')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("accent already exact")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("selection colours are the exact accent")


if __name__ == "__main__":
    main()
