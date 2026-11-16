#!/usr/bin/env python3
"""拟合要吃原始颜色，不能吃「错位后的红/蓝」通道。

`fitted(r[0], base[1], b[2])` took the red of the pixel 2 px to the right and the blue 2 px to the left —
the strip-shifted channels — so the fitted transform saw the wrong input colours. It must read the
pixel's own r, g, b.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FIT_ORIGINAL_INPUT_V1"

OLD = "let f = fitted(r[0].clamp(0.0, 1.0), base[1].clamp(0.0, 1.0), b[2].clamp(0.0, 1.0));"
NEW = "let f = fitted(base[0].clamp(0.0, 1.0), base[1].clamp(0.0, 1.0), base[2].clamp(0.0, 1.0));"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("fit already reads the original pixel")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("fit reads the pixel's own colour")


if __name__ == "__main__":
    main()
