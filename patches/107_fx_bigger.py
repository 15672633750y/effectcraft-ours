#!/usr/bin/env python3
"""The effect header's fx toggle is drawn 16px; make it a real touch target."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FX_BIGGER_V1"
EDITS = [
    ('let fxr = Rect::from_center_size(pos2(r.min.x + 14.0, r.center().y), vec2(16.0, 16.0));',
     'let fxr = Rect::from_center_size(pos2(r.min.x + 20.0, r.center().y), vec2(26.0, 26.0));'),
    ('let tw = Rect::from_center_size(pos2(r.min.x + 32.0, r.center().y), vec2(12.0, 12.0));',
     'let tw = Rect::from_center_size(pos2(r.min.x + 44.0, r.center().y), vec2(18.0, 18.0));'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/effect_controls/panel.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("fx toggle already enlarged")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: expected 1, found {src.count(old)}: {old[:50]}")
        src = src.replace(old, new, 1)
    src = src.replace("use crate::widgets::", "// " + MARKER + "\nuse crate::widgets::", 1)
    path.write_text(src, encoding="utf-8")
    print("effect header fx toggle is 26px, twirl 18px")


if __name__ == "__main__":
    main()
