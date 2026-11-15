#!/usr/bin/env python3
"""悬浮球拖动改用指针位移（widget 每帧跟着球移动，drag_delta 会变成 0）。

`drag_delta()` is measured against the widget's rect, which moves with the ball every pass, so the
delta came out as zero and the ball never moved. The pointer's own delta does not depend on the rect.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BALL_DRAG_V1"
OLD = '''    if resp.dragged() {
        pos += resp.drag_delta();
'''
NEW = '''    if resp.dragged() {
        // EFFECTCRAFT_OURS_BALL_DRAG_V1 — 用指针位移，避免跟着 rect 移动时 delta 归零
        pos += ui.input(|i| i.pointer.delta());
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("drag already uses the pointer delta")
        return
    n = src.count(OLD)
    if n < 1:
        raise SystemExit(f"anchor: {n}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("ball follows the finger")


if __name__ == "__main__":
    main()
