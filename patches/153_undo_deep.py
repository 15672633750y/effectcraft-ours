#!/usr/bin/env python3
"""A much deeper undo/redo history, from the moment a file is opened.

The history kept 32 steps by default and the settings clamped the value to 99, so a long session
could not be taken back to its start. The default is 500 now and the setting goes up to 2000. Each
step is a project snapshot, so "unlimited" would be unbounded memory: 500 covers a whole editing
session for a normal project and still leaves the phone's memory alone.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DEEP_UNDO_V1"

SECTIONS_OLD = "    undo_levels: u32 = 32,\n"
SECTIONS_NEW = "    // EFFECTCRAFT_OURS_DEEP_UNDO_V1 — 默认 500 步，打开文件起到关闭都在历史里\n    undo_levels: u32 = 500,\n"

CLAMP_OLD = "        g.undo_levels = g.undo_levels.clamp(1, 99);\n"
CLAMP_NEW = "        // EFFECTCRAFT_OURS_DEEP_UNDO_V1 — 上限放到 2000 步\n        g.undo_levels = g.undo_levels.clamp(1, 2000);\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    sections = root / "crates/engine/src/settings/prefs/sections.rs"
    src = sections.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(SECTIONS_OLD) != 1:
            raise SystemExit(f"sections anchor: {src.count(SECTIONS_OLD)}")
        sections.write_text(src.replace(SECTIONS_OLD, SECTIONS_NEW, 1), encoding="utf-8")
        print("default undo depth is 500")

    document = root / "crates/engine/src/settings/prefs/document.rs"
    src = document.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(CLAMP_OLD) != 1:
            raise SystemExit(f"clamp anchor: {src.count(CLAMP_OLD)}")
        document.write_text(src.replace(CLAMP_OLD, CLAMP_NEW, 1), encoding="utf-8")
        print("undo depth can reach 2000")


if __name__ == "__main__":
    main()
