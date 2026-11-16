#!/usr/bin/env python3
"""把暗角从拟合调色里拆出去：默认中心增益 1.0、边缘衰减 0.0（纯颜色），暗角交给 S_Vignette。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SPLIT_VIGNETTE_V1"

EDITS = (
    ('p("centerGain", "中心增益", num(1.06), slider(0.5, 2.0, 0.9, 1.2, 4)),',
     'p("centerGain", "中心增益", num(1.0), slider(0.5, 2.0, 0.9, 1.2, 4)),'),
    ('p("edgeFalloff", "边缘衰减", num(0.556), slider(0.0, 2.0, 0.0, 2.0, 4)),',
     'p("edgeFalloff", "边缘衰减", num(0.0), slider(0.0, 2.0, 0.0, 2.0, 4)),'),
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/color_aefit.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("vignette already split out")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("fitted colour is now colour-only; vignette lives in S_Vignette")


if __name__ == "__main__":
    main()
