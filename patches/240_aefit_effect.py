#!/usr/bin/env python3
"""「王者调色（拟合）」：用真实前后帧拟合出的二次多项式还原 AE 的调色结果。

The coefficients come from the user's own exports (原图.png → 调色.png, 57,600 samples):
per-channel quadratic fit, mean absolute error ≈5/255 with the vignette and sharpen left in the
reference. It is *not* Sapphire's formula (closed source) — it is an empirical match, which is why the
effect is named as a fitted one and keeps a Strength slider.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AEFIT_V1"

MODULE = r'''//! 拟合调色：用二次多项式逼近 AE 里那条调色链的输出（系数来自真实前后帧）。

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;

use crate::{Buf, EffectCtx, EffectSpec, num, p, slider};

fn spec() -> EffectSpec {
    EffectSpec {
        id: "ec.color.aefit",
        name: "王者调色 (拟合)",
        category: "Color",
        params: vec![
            p("strength", "强度", num(1.0), slider(0.0, 1.0, 0.0, 1.0, 3)),
            p("centerGain", "中心增益", num(1.06), slider(0.5, 2.0, 0.9, 1.2, 4)),
            p("edgeFalloff", "边缘衰减", num(0.556), slider(0.0, 2.0, 0.0, 2.0, 4)),
        ],
        render,
        gpu: false,
        float: true,
    }
}

/// 特征: 1, r, g, b, r², g², b², rg, gb, rb（0–1 归一化）
const COEF: [[f64; 10]; 3] = [
    [-0.06125, 0.76086, 0.40767, -0.02988, 0.66437, 0.14570, -0.08116, -0.90846, 0.25137, -0.11531],
    [-0.05307, 0.22219, 0.88460, -0.02132, 0.09575, 0.50210, -0.31657, -0.80564, 0.15726, 0.38145],
    [-0.04514, 0.24876, 0.35228, 0.43188, 0.12539, 0.21446, 0.61267, -0.32084, -0.19677, -0.34626],
];

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let s = cx.params.f("strength").clamp(0.0, 1.0) as f32;
    if s <= 0.0 {
        return buf;
    }
    let cg = cx.params.f("centerGain").clamp(0.5, 2.0) as f32;
    let ef = cx.params.f("edgeFalloff").clamp(0.0, 2.0) as f32;
    let (wf, hf) = (buf.img.width as f32, buf.img.height as f32);
    let width = buf.img.width as usize;
    for (i, px) in buf.img.data.iter_mut().enumerate() {
        let a = px[3];
        if a <= 0.0 {
            continue;
        }
        // 实测径向：中心 +6%，r=0.6 附近 −14%（这就是那条暗角）
        let dx = (i % width) as f32 / wf - 0.5;
        let dy = (i / width) as f32 / hf - 0.5;
        let rr = (dx * dx + dy * dy).sqrt() * 2.0;
        let gain = (cg - ef * rr * rr).clamp(0.0, 4.0);
        let r = (px[0] / a.max(1e-6)).clamp(0.0, 1.0);
        let g = (px[1] / a.max(1e-6)).clamp(0.0, 1.0);
        let b = (px[2] / a.max(1e-6)).clamp(0.0, 1.0);
        let f = [1.0, r as f64, g as f64, b as f64, (r * r) as f64, (g * g) as f64, (b * b) as f64, (r * g) as f64, (g * b) as f64, (r * b) as f64];
        let mut out = [0.0f32; 3];
        for c in 0..3 {
            let v: f64 = COEF[c].iter().zip(f.iter()).map(|(k, x)| k * x).sum();
            out[c] = v.clamp(0.0, 1.0) as f32;
        }
        for c in 0..3 {
            let orig = px[c];
            let target = out[c] * a.max(1e-6) * gain;
            px[c] = (orig * (1.0 - s) + target * s).max(0.0);
        }
    }
    buf
}

pub fn specs() -> Vec<EffectSpec> {
    vec![spec()]
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/color_aefit.rs"
    mod_rs = root / "crates/effects/src/lib.rs"
    src = mod_rs.read_text(encoding="utf-8")
    if MARKER in src:
        print("fitted colour effect already registered")
        return
    path.write_text(MODULE, encoding="utf-8")
    anchor = "mod ffx_vintage;\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"mod anchor: {src.count(anchor)}")
    src = src.replace(anchor, anchor + "mod color_aefit;\n", 1)
    reg = "        v.extend(ffx_vintage::specs());\n"
    if src.count(reg) != 1:
        raise SystemExit(f"reg anchor: {src.count(reg)}")
    src = src.replace(reg, reg + "        v.extend(color_aefit::specs());\n", 1)
    mod_rs.write_text(src, encoding="utf-8")
    print("fitted colour effect added")


if __name__ == "__main__":
    main()
