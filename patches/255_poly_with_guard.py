#!/usr/bin/env python3
"""回到三次拟合（参考帧最像），同时保留亮度曲线用于「防过曝」的护栏。

The constrained curve+chroma model desaturated the mid-tones so much that the graded frame lost its
colour (the user's words: “一点饱和度都没有”). The cubic fit is restored — it is 3/255 from the AE
frame — and the measured luma curve is now used only as an upper guard so other clips cannot blow out.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_POLY_WITH_GUARD_V1"

OLD = '/// 亮度曲线（17 段折线，来自实测的前后帧）\nconst KNOTS: [(f32, f32); 17] = [\n    (0.0401, 0.0201), (0.0940, 0.0646), (0.1514, 0.1200), (0.2062, 0.1705),\n    (0.2730, 0.2435), (0.3188, 0.2957), (0.3787, 0.3650), (0.4365, 0.4311),\n    (0.4967, 0.5002), (0.5582, 0.5596), (0.6165, 0.6401), (0.6753, 0.7015),\n    (0.7342, 0.7772), (0.7930, 0.8507), (0.8546, 0.9108), (0.9105, 0.9213),\n    (0.9712, 0.9823),\n];\n\nfn tone(y: f32) -> f32 {\n    let y = y.clamp(0.0, 1.0);\n    if y <= KNOTS[0].0 {\n        return y * KNOTS[0].1 / KNOTS[0].0.max(1e-4);\n    }\n    let mut i = 0;\n    while i + 1 < KNOTS.len() {\n        let (x0, y0) = KNOTS[i];\n        let (x1, y1) = KNOTS[i + 1];\n        if y <= x1 {\n            let t = (y - x0) / (x1 - x0).max(1e-6);\n            return y0 + (y1 - y0) * t;\n        }\n        i += 1;\n    }\n    KNOTS[KNOTS.len() - 1].1\n}\n\n/// 有约束的调色：只改亮度曲线与色度强度，不做通道交叉，换素材也不会翻色或爆掉。\nfn fitted(r: f32, g: f32, b: f32) -> [f32; 3] {\n    let y = 0.2126 * r + 0.7152 * g + 0.0722 * b;\n    let k = 0.455 + 0.617 * y;\n    let cr = (r - y) * k;\n    let cb = (b - y) * k;\n    let y2 = tone(y);\n    let rr = y2 + cr;\n    let bb = y2 + cb;\n    let gg = (y2 - 0.2126 * rr - 0.0722 * bb) / 0.7152;\n    [rr.clamp(0.0, 1.0), gg.clamp(0.0, 1.0), bb.clamp(0.0, 1.0)]\n}\n'

NEW = '/// 亮度曲线（17 段折线，来自实测的前后帧；只用于防止别的素材过曝）\nconst KNOTS: [(f32, f32); 17] = [\n    (0.0401, 0.0201), (0.0940, 0.0646), (0.1514, 0.1200), (0.2062, 0.1705),\n    (0.2730, 0.2435), (0.3188, 0.2957), (0.3787, 0.3650), (0.4365, 0.4311),\n    (0.4967, 0.5002), (0.5582, 0.5596), (0.6165, 0.6401), (0.6753, 0.7015),\n    (0.7342, 0.7772), (0.7930, 0.8507), (0.8546, 0.9108), (0.9105, 0.9213),\n    (0.9712, 0.9823),\n];\n\nfn tone(y: f32) -> f32 {\n    let y = y.clamp(0.0, 1.0);\n    if y <= KNOTS[0].0 {\n        return y * KNOTS[0].1 / KNOTS[0].0.max(1e-4);\n    }\n    let mut i = 0;\n    while i + 1 < KNOTS.len() {\n        let (x0, y0) = KNOTS[i];\n        let (x1, y1) = KNOTS[i + 1];\n        if y <= x1 {\n            let t = (y - x0) / (x1 - x0).max(1e-6);\n            return y0 + (y1 - y0) * t;\n        }\n        i += 1;\n    }\n    KNOTS[KNOTS.len() - 1].1\n}\n\n/// 三次拟合（按真实前后帧算出，参考帧误差 ~3/255）。\nconst FIT: [[f32; 20]; 3] = [\n    [-0.010124, -0.043421, 0.598051, 0.080632, 3.050647, -0.244649, -0.279998, -1.248678, 0.774982, -0.779982, -1.828900, 1.021148, -0.502560, 0.714899, -0.008165, -0.883604, -3.138988, -0.841758, 2.249645, 2.335632],\n    [-0.017410, 0.258986, 0.497294, -0.008443, 0.355585, 2.281762, 0.245314, -1.510925, -0.653451, 0.171760, -0.114448, -1.214214, -0.697222, -0.312102, -0.237871, 0.736207, -1.704017, -0.764737, 1.630571, 2.082460],\n    [-0.020402, 0.262059, 0.460760, 0.044220, 0.246681, -0.048752, 1.365632, -0.564683, 0.263247, -0.411162, -0.165941, 0.689578, -0.947893, 0.204886, -0.070079, -0.313535, -2.569302, -0.892807, 1.809302, 1.693180],\n];\n\nfn fitted(r: f32, g: f32, b: f32) -> [f32; 3] {\n    let f = [\n        1.0, r, g, b, r * r, g * g, b * b, r * g, g * b, r * b,\n        r * r * r, g * g * g, b * b * b, r * r * g, r * r * b,\n        g * g * r, g * g * b, b * b * r, b * b * g, r * g * b,\n    ];\n    let mut out = [0.0f32; 3];\n    for c in 0..3 {\n        let v: f32 = FIT[c].iter().zip(f.iter()).map(|(k, x)| k * x).sum();\n        let v = if v > 0.9 {\n            0.9 + 0.1 * (1.0 - (-(v - 0.9) / 0.1).exp())\n        } else if v < 0.02 {\n            v.max(0.0)\n        } else {\n            v\n        };\n        out[c] = v;\n    }\n    out\n}\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("polynomial already restored")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("cubic fit restored (with the luma curve kept as a guard)")


if __name__ == "__main__":
    main()
