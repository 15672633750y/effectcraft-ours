#!/usr/bin/env python3
"""三条彩的拟合升级到三次（20 项）：MAE 从 5.1 降到 4.8/4.9/4.6，暗部与对比更贴。

Fitted on the same before/after pair (含暗角，所以单次应用就是 AE 那条链的结果)；三次项主要改善
暗部的对比与色相偏移。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STRIP_CUBIC_V1"

OLD = """const FIT: [[f32; 10]; 3] = [
    [-0.06125, 0.76086, 0.40767, -0.02988, 0.66437, 0.14570, -0.08116, -0.90846, 0.25137, -0.11531],
    [-0.05307, 0.22219, 0.88460, -0.02132, 0.09575, 0.50210, -0.31657, -0.80564, 0.15726, 0.38145],
    [-0.04514, 0.24876, 0.35228, 0.43188, 0.12539, 0.21446, 0.61267, -0.32084, -0.19677, -0.34626],
];
"""

NEW = """const FIT: [[f32; 20]; 3] = [
    [-0.010124, -0.043421, 0.598051, 0.080632, 3.050647, -0.244649, -0.279998, -1.248678, 0.774982, -0.779982, -1.828900, 1.021148, -0.502560, 0.714899, -0.008165, -0.883604, -3.138988, -0.841758, 2.249645, 2.335632],
    [-0.017410, 0.258986, 0.497294, -0.008443, 0.355585, 2.281762, 0.245314, -1.510925, -0.653451, 0.171760, -0.114448, -1.214214, -0.697222, -0.312102, -0.237871, 0.736207, -1.704017, -0.764737, 1.630571, 2.082460],
    [-0.020402, 0.262059, 0.460760, 0.044220, 0.246681, -0.048752, 1.365632, -0.564683, 0.263247, -0.411162, -0.165941, 0.689578, -0.947893, 0.204886, -0.070079, -0.313535, -2.569302, -0.892807, 1.809302, 1.693180],
];
"""

FEAT_OLD = """    let f = [1.0, r, g, b, r * r, g * g, b * b, r * g, g * b, r * b];
"""
FEAT_NEW = """    let f = [
        1.0, r, g, b, r * r, g * g, b * b, r * g, g * b, r * b,
        r * r * r, g * g * g, b * b * b, r * r * g, r * r * b,
        g * g * r, g * g * b, b * b * r, b * b * g, r * g * b,
    ];
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("cubic fit already installed")
        return
    for old, new in ((OLD, NEW), (FEAT_OLD, FEAT_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("three-strip fit upgraded to cubic (MAE ~4.7)")


if __name__ == "__main__":
    main()
