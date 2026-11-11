#!/usr/bin/env python3
"""Give the transform properties Chinese display names at the source.

Scripts and expressions address properties by id (`anchor`, `position`, …) and effects by id, so
renaming only the display strings is safe for automation while every panel shows Chinese.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TRANSFORM_NAMES_SOURCE_V1"

PAIRS = [
    ("anchor", "Anchor Point", "锚点"),
    ("position", "Position", "位置"),
    ("scale", "Scale", "缩放"),
    ("rotation", "Rotation", "旋转"),
    ("opacity", "Opacity", "不透明度"),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/project/src/build.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("transform names already localised at the source")
        return
    total = 0
    for prop_id, english, chinese in PAIRS:
        pattern = re.compile(r'("' + prop_id + r'",\s*)"' + re.escape(english) + r'"')
        src, n = pattern.subn(r'\1"' + chinese + '"', src)
        total += n
        print(f"{prop_id}: {n} display names -> {chinese}")
    if total == 0:
        raise SystemExit("no transform property names matched")
    path.write_text(f"// {MARKER}\n{src}", encoding="utf-8")


if __name__ == "__main__":
    main()
