#!/usr/bin/env python3
"""不再画右下角那个悬浮球：头像现在就是工具栏第一个按钮。

The floating ball was a detour; the avatar lives in the toolbar slot now, so its call is removed
(the code stays harmless behind it). Edge-snap/floating can come back later if wanted.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NO_BALL_CALL_V1"
OLD = "        shortcut_ball(ui, full);\n"
NEW = "        // EFFECTCRAFT_OURS_NO_BALL_CALL_V1 — 头像已移到工具栏第一个按钮\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("ball call already removed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("floating ball no longer drawn")


if __name__ == "__main__":
    main()
