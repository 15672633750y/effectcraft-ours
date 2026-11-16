#!/usr/bin/env python3
"""预设库也列出 .bin：系统保存对话框给的后缀就是 .bin。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_BIN_V1"

OLD = 'if low.ends_with(".ffx") || low.ends_with(".gp") || low.ends_with(".json") {'

NEW = 'if low.ends_with(".ffx") || low.ends_with(".gp") || low.ends_with(".json") || low.ends_with(".bin") {'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(".bin already listed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset library lists .bin too")


if __name__ == "__main__":
    main()
