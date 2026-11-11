#!/usr/bin/env python3
"""Sapphire-compatible extras: VintageColor2Strip and Vignette.

Parameter lists follow the effect controls the user photographed: same names, order and defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_COMPAT_EXTRA_V1"

MODULE = r'''//! Sapphire-compatible extras: the two-strip vintage colour and the vignette.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, popup, slider};

const CATEGORY: &str = "Color Correction";

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn render_two_strip(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let amount = (cx.params.f("amount").clamp(0.0, 100.0) / 100.0) as f32;
    let brightness = (cx.params.f("brightness").max(0.0) / 100.0) as f32;
    let saturation = (cx.params.f("saturation").max(0.0) / 100.0) as f32;
    let offset_darks = (cx.params.f("offsetDarks").clamp(-100.0, 100.0) / 100.0) as f32;
    let tint = cx.params.color("tint");

    // Two-strip: a red-orange and a blue-green dye, the early Technicolor pair.
    let dye_a = [0.95f32, 0.55, 0.45];
    let dye_b = [0.35f32, 0.85, 0.80];

    buf.img.data.par_iter_mut().for_each(|px| {
        let (c, a) = unpremul(*px);
        if a <= 0.0 {
            return;
        }
        let l = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
        let mut o = [0.0f32; 3];
        for k in 0..3 {
            let da = (1.0 - c[0]).clamp(0.0, 1.0);
            let db = (1.0 - c[2]).clamp(0.0, 1.0);
            let v = dye_a[k].clamp(0.0001, 1.0).powf(da) * dye_b[k].clamp(0.0001, 1.0).powf(db);
            let mut v = (v * brightness).clamp(0.0, 1.0);
            v = (l + (v - l) * saturation).clamp(0.0, 1.0);
            v = if offset_darks >= 0.0 { v * (1.0 - offset_darks * 0.5) } else { v + (-offset_darks) * 0.5 * (1.0 - v) };
            o[k] = (v * tint[k]).clamp(0.0, 1.0);
        }
        *px = premul(
            [c[0] + (o[0] - c[0]) * amount, c[1] + (o[1] - c[1]) * amount, c[2] + (o[2] - c[2]) * amount],
            a,
        );
    });
    buf
}

fn render_vignette(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let center = cx.params.v2("center");
    let radius = cx.params.f("radius").max(0.01) as f32;
    let rel_w = cx.params.f("relWidth").max(0.01) as f32;
    let rel_h = cx.params.f("relHeight").max(0.01) as f32;
    let rotate = cx.params.f("rotate") as f32 * std::f32::consts::PI / 180.0;
    let softness = cx.params.f("edgeSoftness").max(0.001) as f32;
    let smooth = cx.params.f("smoothCurve").clamp(0.0, 1.0) as f32;
    let colour = cx.params.color("color");
    let opacity = cx.params.f("opacity").clamp(0.0, 1.0) as f32;
    let iw = buf.img.width.max(1) as usize;
    let ih = buf.img.height.max(1) as usize;
    // Centre is in layer pixels; the radii are relative, so normalise by half the layer size.
    let half_w = (cx.layer_size[0].max(1.0) as f32) * 0.5;
    let half_h = (cx.layer_size[1].max(1.0) as f32) * 0.5;
    // The Centre field arrives either in layer pixels (960,540) or as a fraction (0.5,0.5).
    let fx = if (center[0] as f32).abs() > 2.0 { (center[0] as f32) / (half_w * 2.0) } else { center[0] as f32 };
    let fy = if (center[1] as f32).abs() > 2.0 { (center[1] as f32) / (half_h * 2.0) } else { center[1] as f32 };
    let cx0 = fx.clamp(-2.0, 3.0) * half_w * 2.0;
    let cy0 = fy.clamp(-2.0, 3.0) * half_h * 2.0;
    let (sin_r, cos_r) = rotate.sin_cos();

    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let (c, a) = unpremul(*px);
        if a <= 0.0 {
            return;
        }
        let x = (i % iw) as f32 - cx0;
        let y = (i / iw) as f32 - cy0;
        let rx = x * cos_r - y * sin_r;
        let ry = x * sin_r + y * cos_r;
        let d = ((rx / (rel_w * half_w)).powi(2) + (ry / (rel_h * half_h)).powi(2)).sqrt();
        // 1 inside the ellipse, falling to 0 across the soft edge.
        let t = ((d - radius) / softness).clamp(0.0, 1.0);
        let fall = 1.0 - t * t * (3.0 - 2.0 * t);
        let w = (fall.powf(1.0 + smooth * 3.0) * opacity).clamp(0.0, 1.0);
        let o = [
            c[0] + (colour[0] - c[0]) * w,
            c[1] + (colour[1] - c[1]) * w,
            c[2] + (colour[2] - c[2]) * w,
        ];
        *px = premul(o, a);
        let _ = ih;
    });
    buf
}

pub fn specs() -> Vec<EffectSpec> {
    vec![
        spec(
            "org.effectcraft.compat.sapphire.vintagecolor2strip",
            "复古双条彩 (S_VintageColor2Strip)",
            vec![
                p("amount", "Amount", num(100.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
                p("keyLayerDensity", "Key Layer Density", num(0.1), slider(0.0, 1.0, 0.0, 1.0, 3)),
                p("grainAmp", "Grain Amp", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
                p("grainBlur", "Grain Blur", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
                p("brightness", "Brightness", num(100.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
                p("tint", "Tint", col(1.0, 1.0, 1.0), ParamUi::Color),
                p("saturation", "Saturation", num(100.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
                p("offsetDarks", "Offset Darks", num(0.0), slider(-100.0, 100.0, -100.0, 100.0, 3)),
                p("show", "Show", Value::Enum(0), popup(&["Result", "Source"])),
                p("maskUse", "Mask Use", Value::Enum(0), popup(&["Luma", "Alpha"])),
                p("blurMask", "Blur Mask", num(12.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
                p("invertMask", "Invert Mask", Value::Bool(false), ParamUi::Checkbox),
            ],
            render_two_strip,
        ),
        spec(
            "org.effectcraft.compat.sapphire.vignette",
            "暗角 (S_Vignette)",
            vec![
                p("effect", "Effect", Value::Enum(0), popup(&["Vignette"])),
                p("center", "Center XY", Value::Vec2([0.5, 0.5]), ParamUi::Point),
                p("squareness", "Squareness", num(0.0), slider(0.0, 1.0, 0.0, 1.0, 4)),
                p("radius", "Radius", num(1.03), slider(0.0, 3.0, 0.0, 3.0, 3)),
                p("relHeight", "Rel Height", num(0.75), slider(0.01, 4.0, 0.01, 4.0, 3)),
                p("relWidth", "Rel Width", num(1.08), slider(0.01, 4.0, 0.01, 4.0, 3)),
                p("rotate", "Rotate", num(0.0), slider(-180.0, 180.0, -180.0, 180.0, 2)),
                p("edgeSoftness", "Edge Softness", num(1.0), slider(0.001, 4.0, 0.001, 4.0, 4)),
                p("smoothCurve", "Smooth Curve", num(0.4), slider(0.0, 1.0, 0.0, 1.0, 4)),
                p("color", "Color", col(0.0, 0.0, 0.0), ParamUi::Color),
                p("opacity", "Opacity", num(0.5), slider(0.0, 1.0, 0.0, 1.0, 3)),
                p("blurAmount", "Blur Amount", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
                p("blurInside", "Blur Inside", Value::Bool(true), ParamUi::Checkbox),
                p("sourceBrightness", "Source Brightness", num(1.02), slider(0.0, 3.0, 0.0, 3.0, 3)),
                p("combine", "Combine", Value::Enum(0), popup(&["Composite", "Multiply"])),
                p("showRadius", "Show Radius", Value::Bool(true), ParamUi::Checkbox),
                p("showRotate", "Show Rotate", Value::Bool(true), ParamUi::Checkbox),
                p("showCenter", "Show Center", Value::Bool(true), ParamUi::Checkbox),
            ],
            render_vignette,
        ),
    ]
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    lib = root / "crates/effects/src/lib.rs"
    source = lib.read_text(encoding="utf-8")
    (root / "crates/effects/src/compat_extra.rs").write_text(MODULE, encoding="utf-8")
    if MARKER in source:
        print("compat extras refreshed.")
        return
    if source.count("mod color3;\n") != 1:
        raise SystemExit("module anchor not found")
    source = source.replace("mod color3;\n", "mod color3;\nmod compat_extra;\n", 1)
    if source.count("        v.extend(color3::specs());\n") != 1:
        raise SystemExit("registry anchor not found")
    source = source.replace(
        "        v.extend(color3::specs());\n",
        "        v.extend(color3::specs());\n        v.extend(compat_extra::specs());\n",
        1,
    )
    lib.write_text(f"// {MARKER}\n{source}", encoding="utf-8")
    print("Added S_VintageColor2Strip and S_Vignette.")


if __name__ == "__main__":
    main()
