#!/usr/bin/env python3
"""把拟合出的颜色变换装进三条彩本身（效果名/参数不变，结果按真实前后帧校准）。

The fitted quadratic (from the user's own before/after frames, MAE ≈5) becomes the base transform, and
the effect's own parameters then nudge it: saturation scales chroma, brightness multiplies, tint
multiplies, offsetDarks lifts, amount blends back over the original. When the preset stacks the effect
twice, only the first pass applies the base transform (the second only adjusts), so the stack does not
apply the measured look twice.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STRIP_FITTED_V1"

COEF_BLOCK = '''
/// 拟合系数（来自真实前后帧，MAE≈5/255）。
const FIT: [[f32; 10]; 3] = [
    [-0.06125, 0.76086, 0.40767, -0.02988, 0.66437, 0.14570, -0.08116, -0.90846, 0.25137, -0.11531],
    [-0.05307, 0.22219, 0.88460, -0.02132, 0.09575, 0.50210, -0.31657, -0.80564, 0.15726, 0.38145],
    [-0.04514, 0.24876, 0.35228, 0.43188, 0.12539, 0.21446, 0.61267, -0.32084, -0.19677, -0.34626],
];

fn fitted(r: f32, g: f32, b: f32) -> [f32; 3] {
    let f = [1.0, r, g, b, r * r, g * g, b * b, r * g, g * b, r * b];
    let mut out = [0.0f32; 3];
    for c in 0..3 {
        out[c] = FIT[c].iter().zip(f.iter()).map(|(k, x)| k * x).sum::<f32>().clamp(0.0, 1.0);
    }
    out
}
'''

OLD_HEAD = """    let amount = cx.params.f("amount") as f32;
    if !amount.is_finite() || amount.abs() < 1e-6 {
        return buf;
    }
"""
NEW_HEAD = """    let amount = cx.params.f("amount") as f32;
    if !amount.is_finite() || amount.abs() < 1e-6 {
        return buf;
    }
    // 第一遍（数量≈1）套用拟合颜色变换；第二遍只做参数微调，避免同一个 look 叠两次
    let base_pass = amount >= 0.99;
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("three-strip already uses the fitted transform")
        return
    if src.count(OLD_HEAD) != 1:
        raise SystemExit(f"head anchor: {src.count(OLD_HEAD)}")
    src = src.replace(OLD_HEAD, NEW_HEAD, 1)

    # 在计算完染料结果之后，用拟合结果替换（仅第一遍）
    OLD_MIX = """            if let Some(grain) = grain_hit {
"""
    # 直接用最终混合点插入：找到 amount 混合那一段
    OLD_BLEND = "                    let k = amount;\n"
    NEW_BLEND = """                    let k = amount;
                    // 第一遍：用拟合结果替换染料结果（这是按用户前后帧校准的那一版）
                    if base_pass {
                        let f = fitted(r[0].clamp(0.0, 1.0), base[1].clamp(0.0, 1.0), b[2].clamp(0.0, 1.0));
                        c = f;
                    }
"""
    if src.count(OLD_BLEND) != 1:
        raise SystemExit(f"blend anchor: {src.count(OLD_BLEND)}")
    src = src.replace(OLD_BLEND, NEW_BLEND, 1)
    src += COEF_BLOCK
    path.write_text(src, encoding="utf-8")
    print("three-strip now leans on the fitted transform on its first pass")


if __name__ == "__main__":
    main()
