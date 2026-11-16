#!/usr/bin/env python3
"""选中色回到主题自带的「默认」观感：不再掺主题色，浅蓝灰底 + 现有文字色（AE 那样）。

A custom accent used to tint every selection, which left the selected effect header looking dark and
muddy. Selection now keeps the theme's own colour (the same one the interface uses when no custom accent
is set), so a selected row reads like After Effects' default selection.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCENT_EXACT_V1"

EDITS = [
    ("            t.row_selected = t.row.lerp_to_gamma(rgb, 0.38);",
     "            t.row_selected = Tokens::for_kind(kind).row_selected;"),
    ("            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.30);",
     "            t.tl_graph_selected = Tokens::for_kind(kind).tl_graph_selected;"),
    ("            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.42);",
     "            t.fx_header_active = Tokens::for_kind(kind).fx_header_active;"),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src and "Tokens::for_kind(kind).row_selected" in src:
        print("selection already uses the theme default")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    if MARKER not in src:
        src = src.replace("pub fn from_prefs", "// " + MARKER + "\npub fn from_prefs", 1)
    path.write_text(src, encoding="utf-8")
    print("selection colours are the theme defaults")


if __name__ == "__main__":
    main()
