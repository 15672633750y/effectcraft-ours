#!/usr/bin/env python3
"""自定义曲线要能拉出过冲/回弹：图的可视范围放宽到 −0.5~1.5，中段峰值不再被夹到 0..1。

The free-drag graph could already move its control points out of range, but the value that reaches
`keys.velocity` clamped the mid-curve peak to 0.05..1.0, so an overshoot or a dip collapsed back to a
plain ease. The graph is wider now and the peak is passed through (clamped to −1.5..2.5).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVE_OVERSHOOT_V1"

EDITS = [('            let ymin = -0.35f32;\n            let ymax = 1.35f32;\n', '            let ymin = -0.5f32;\n            let ymax = 1.5f32;\n'), ('                    let peak = ys[4].clamp(0.05, 1.0);\n', '                    // 允许过冲/回弹：中段可以超过 1 或低于 0，别夹掉\n                    let peak = ys[4].clamp(-1.5, 2.5);\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("curve overshoot already allowed")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("custom curves can overshoot and dip")


if __name__ == "__main__":
    main()
