#!/usr/bin/env python3
"""Smaller layer switches: 15px per switch instead of 27px.

The earlier pass grew the switches for thumbs (30px, then 27px) and eight of them ate 222px before
the name column started — on a phone that is most of the timeline. 15px cells with 13px icons are
about what After Effects draws; the 3px extra hit area from `zzz_fx_hit_size.py` stays, so a finger
still lands on them.

This runs after every other patch that touches the switch sizes (`90_`, `zzz_`), so it always sees
the final values.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SMALL_SWITCHES_V1"

EDITS = [
    ("const SW: f32 = 27.0;", "const SW: f32 = 15.0;"),
    (
        "let br = Rect::from_center_size(pos2(cw.switches + SW * i as f32 + SW / 2.0, cy), vec2(23.0, 23.0));",
        "let br = Rect::from_center_size(pos2(cw.switches + SW * i as f32 + SW / 2.0, cy), vec2(13.0, 13.0));",
    ),
    (
        "let fr_ = Rect::from_center_size(pos2(cw.switches + SW * 3.0 + SW / 2.0, cy), vec2(16.0, 16.0));",
        "let fr_ = Rect::from_center_size(pos2(cw.switches + SW * 3.0 + SW / 2.0, cy), vec2(13.0, 13.0));",
    ),
    (
        "let br = Rect::from_center_size(pos2(cw.av + 10.0 + 18.0 * i as f32, cy), vec2(15.0, 15.0));",
        "let br = Rect::from_center_size(pos2(cw.av + 9.0 + 17.0 * i as f32, cy), vec2(14.0, 14.0));",
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("small switches already installed")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:50]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    src = f"// {MARKER}\n{src}"
    path.write_text(src, encoding="utf-8")
    print("layer switches are 15px wide with 13px icons")


if __name__ == "__main__":
    main()
