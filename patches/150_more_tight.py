#!/usr/bin/env python3
"""Two more places where empty chrome ate the picture area.

* The Project panel's preview header is 74 points tall even with nothing selected — a thumbnail
  frame around a one-line hint. With no selection it is 30 now; picking an item brings the
  thumbnail back.
* `TAB_STRIP` (used by the layout maths that sizes frames) still assumed a 30-point tab strip after
  `149_layout_tight` made tabs 24, so every frame was 6 points taller than its tabs; the Preview
  frame's 46-point body also shrinks to 40.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIGHT_CHROME_V2"

HEAD_OLD = "    let head = Rect::from_min_size(rect.min, vec2(rect.width(), 74.0));\n"
HEAD_NEW = """    // EFFECTCRAFT_OURS_TIGHT_CHROME_V2 — 没选中项目时不需要缩略图那么高的头
    let head_h = if app.session.state.project_selection.is_empty() { 30.0 } else { 74.0 };
    let head = Rect::from_min_size(rect.min, vec2(rect.width(), head_h));
"""

TAB_OLD = "pub const TAB_STRIP: f32 = 30.0;\n"
TAB_NEW = "pub const TAB_STRIP: f32 = 24.0; // EFFECTCRAFT_OURS_TIGHT_CHROME_V2 — 与 Tokens::tab_h 一致\n"

PREVIEW_OLD = "pub const PREVIEW_FRAME: f32 = TAB_STRIP + 46.0;\n"
PREVIEW_NEW = "pub const PREVIEW_FRAME: f32 = TAB_STRIP + 40.0;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    proj = root / "crates/ui-egui/src/panels/project.rs"
    src = proj.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(HEAD_OLD) != 1:
            raise SystemExit(f"project head anchor: {src.count(HEAD_OLD)}")
        proj.write_text(src.replace(HEAD_OLD, HEAD_NEW, 1), encoding="utf-8")
        print("project header shrinks without a selection")

    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER not in src:
        for old, new in ((TAB_OLD, TAB_NEW), (PREVIEW_OLD, PREVIEW_NEW)):
            if src.count(old) != 1:
                raise SystemExit(f"dock anchor {old.strip()[:30]!r}: {src.count(old)}")
            src = src.replace(old, new, 1)
        dock.write_text(src, encoding="utf-8")
        print("tab strip constant and preview frame agree with the shorter tabs")


if __name__ == "__main__":
    main()
