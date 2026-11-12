#!/usr/bin/env python3
"""The timeline name column may shrink further, so the switch columns always fit."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NAME_MIN_V1"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("name column minimum already lowered")
        return
    old = "    let name_w = (width - vis.fixed() + NAME_EXTRA.with(|c| c.get())).max(120.0);"
    if src.count(old) != 1:
        raise SystemExit(f"anchor: {src.count(old)}")
    src = src.replace(old, "    // " + MARKER + "\n    let name_w = 96.0;", 1)
    path.write_text(src, encoding="utf-8")
    print("name column is a fixed 96px, so the switches sit right beside it")


if __name__ == "__main__":
    main()
