#!/usr/bin/env python3
"""Two more effects the user's presets need: S_VintageColor3Strip and S_Vignette.

They were missing, so the presets imported their parameter lists and the parameters did nothing —
"调了没反应", and the picture never changed over time because no pixel was ever computed from them.

* **S_VintageColor3Strip** — three-strip vintage colour: the red and blue strips are read a couple
  of pixels sideways (the registration error of a three-strip camera), then brightness, saturation,
  tint, lifted blacks ("Offset Darks") and film grain are applied. `Amount` blends the whole thing
  back over the original, so 0 is untouched and 1 is the full effect.
* **S_Vignette** — an elliptical vignette with the parameters Sapphire shows: centre, radius,
  relative width/height, rotation, squareness (circle ↔ square), edge softness, smooth curve, colour,
  opacity, source brightness and the Combine mode (Composite / Multiply / Screen).

Both are CPU effects over the shared `Buf`, so they keyframe like any other parameter.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FFX_VINTAGE_VIGNETTE_V1"

MODULE = r'''//! FFX presets: a three-strip vintage colour effect and a Sapphire-style vignette.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, popup, slider};

fn spec(id: &'static str, name: &'static str, category: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category, params, render, gpu: false, float: true }
}

#[inline]
fn luma(c: [f32; 3]) -> f32 {
    0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
}

fn hash(mut x: u32) -> f32 {
    x = x.wrapping_mul(747796405).wrapping_add(2891336453);
    x = ((x >> ((x >> 28) + 4)) ^ x).wrapping_mul(277803737);
    ((x >> 22) ^ x) as f32 / 4_294_967_295.0
}

pub(crate) fn specs() -> Vec<EffectSpec> {
    vec![
        spec(
            "S_VintageColor3Strip",
            "复古三色调 (S_VintageColor3Strip)",
            "Color Correction",
            vec![
                p("amount", "Amount", num(1.0), slider(0.0, 2.0, 0.0, 1.0, 3)),
                p("keyLayerDensity", "Key Layer Density", num(0.1), slider(0.0, 1.0, 0.0, 1.0, 3)),
                p("grainAmp", "Grain Amp", num(0.0), slider(0.0, 1.0, 0.0, 0.2, 4)),
                p("grainBlur", "Grain Blur", num(0.0), slider(0.0, 20.0, 0.0, 5.0, 2)),
                p("brightness", "Brightness", num(1.0), slider(0.0, 4.0, 0.0, 2.0, 3)),
                p("tint", "Tint", col(1.0, 1.0, 1.0), ParamUi::Color),
                p("saturation", "Saturation", num(1.0), slider(0.0, 4.0, 0.0, 2.0, 3)),
                p("offsetDarks", "Offset Darks", num(0.0), slider(-50.0, 50.0, -50.0, 50.0, 3)),
                p("show", "Show", Value::Enum(0), popup(&["Result", "Luma", "Matte"])),
                p("maskUse", "Mask Use", Value::Enum(0), popup(&["Luma", "Alpha", "None"])),
                p("blurMask", "Blur Mask", num(12.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
                p("invertMask", "Invert Mask", Value::Bool(false), ParamUi::Checkbox),
            ],
            render_vintage,
        ),
        spec(
            "S_Vignette",
            "暗角 (S_Vignette)",
            "Stylize",
            vec![
                p("effect", "Effect", Value::Enum(0), popup(&["Vignette", "Ellipse", "Rectangle"])),
                p("centerXY", "Center XY", Value::Vec2([960.0, 540.0]), ParamUi::Point),
                p("squareness", "Squareness", num(0.0), slider(0.0, 1.0, 0.0, 1.0, 4)),
                p("radius", "Radius", num(1.03), slider(0.0, 4.0, 0.0, 2.0, 3)),
                p("relHeight", "Rel Height", num(0.75), slider(0.1, 4.0, 0.1, 2.0, 3)),
                p("relWidth", "Rel Width", num(1.08), slider(0.1, 4.0, 0.1, 2.0, 3)),
                p("rotate", "Rotate", num(0.0), slider(-180.0, 180.0, -180.0, 180.0, 2)),
                p("edgeSoftness", "Edge Softness", num(1.0), slider(0.0, 4.0, 0.0, 2.0, 4)),
                p("smoothCurve", "Smooth Curve", num(0.4), slider(0.0, 1.0, 0.0, 1.0, 4)),
                p("color", "Color", col(0.0, 0.0, 0.0), ParamUi::Color),
                p("opacity", "Opacity", num(0.5), slider(0.0, 1.0, 0.0, 1.0, 3)),
                p("blurAmount", "Blur Amount", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
                p("blurInside", "Blur Inside", Value::Bool(true), ParamUi::Checkbox),
                p("sourceBrightness", "Source Brightness", num(1.02), slider(0.0, 4.0, 0.0, 2.0, 3)),
                p("combine", "Combine", Value::Enum(0), popup(&["Composite", "Multiply", "Screen"])),
                p("showRadius", "Show Radius", Value::Bool(true), ParamUi::Checkbox),
                p("showRotate", "Show Rotate", Value::Bool(true), ParamUi::Checkbox),
                p("showCenter", "Show Center", Value::Bool(true), ParamUi::Checkbox),
            ],
            render_vignette,
        ),
    ]
}

/// Three-strip vintage colour: offset red/blue strips, then brightness, saturation and tint.
fn render_vintage(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let amount = cx.params.f("amount").clamp(0.0, 2.0) as f32;
    if amount <= 0.0 {
        return buf;
    }
    let bright = cx.params.f("brightness").clamp(0.0, 4.0) as f32;
    let sat = cx.params.f("saturation").clamp(0.0, 4.0) as f32;
    let tint = cx.params.color("tint");
    let darks = (cx.params.f("offsetDarks") / 100.0) as f32;
    let grain = cx.params.f("grainAmp").clamp(0.0, 1.0) as f32;
    let show = cx.params.e("show");
    let invert = cx.params.b("invertMask");
    let seed = cx.seed;
    let (w, h) = (buf.img.width as i64, buf.img.height as i64);
    let data = std::mem::take(&mut buf.img.data);
    let at = |x: i64, y: i64| -> [f32; 4] {
        let xx = x.clamp(0, w - 1) as usize;
        let yy = y.clamp(0, h - 1) as usize;
        data[yy * w as usize + xx]
    };
    // A three-strip camera never registered its strips perfectly: shift red and blue sideways.
    let sep = (amount * 2.0).round() as i64;
    let out: Vec<[f32; 4]> = (0..data.len())
        .into_par_iter()
        .map(|i| {
            let x = (i % w as usize) as i64;
            let y = (i / w as usize) as i64;
            let (base, a) = unpremul(data[i]);
            if a <= 0.0 {
                return data[i];
            }
            let (r, _) = unpremul(at(x + sep, y));
            let (b, _) = unpremul(at(x - sep, y));
            let mut c = [r[0], base[1], b[2]];
            // Vintage prints lift their blacks and lose saturation.
            c = [c[0] + darks, c[1] + darks, c[2] + darks];
            let l = luma(c);
            c = [l + (c[0] - l) * sat, l + (c[1] - l) * sat, l + (c[2] - l) * sat];
            c = [c[0] * tint[0] * bright, c[1] * tint[1] * bright, c[2] * tint[2] * bright];
            if grain > 0.0 {
                let g = (hash(seed ^ (x as u32).wrapping_mul(374761393) ^ (y as u32).wrapping_mul(668265263)) - 0.5) * 2.0;
                let g = g * grain * 0.25;
                c = [c[0] + g, c[1] + g, c[2] + g];
            }
            let mut mask = luma(c).clamp(0.0, 1.0);
            if invert {
                mask = 1.0 - mask;
            }
            match show {
                1 => premul([mask, mask, mask], a),
                2 => premul([mask, mask, mask], 1.0),
                _ => {
                    let shown = premul(c, a);
                    let k = amount.clamp(0.0, 1.0);
                    [
                        data[i][0] + (shown[0] - data[i][0]) * k,
                        data[i][1] + (shown[1] - data[i][1]) * k,
                        data[i][2] + (shown[2] - data[i][2]) * k,
                        data[i][3] + (shown[3] - data[i][3]) * k,
                    ]
                }
            }
        })
        .collect();
    buf.img.data = out;
    buf
}

/// Sapphire's vignette: an ellipse (or rect) darkened, multiplied or screened over the frame.
fn render_vignette(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let centre = cx.params.v2("centerXY");
    let radius = cx.params.f("radius").max(0.001) as f32;
    let relw = cx.params.f("relWidth").max(0.01) as f32;
    let relh = cx.params.f("relHeight").max(0.01) as f32;
    let squareness = cx.params.f("squareness").clamp(0.0, 1.0) as f32;
    let rot = (cx.params.f("rotate") as f32).to_radians();
    let soft = cx.params.f("edgeSoftness").max(0.001) as f32;
    let smooth = cx.params.f("smoothCurve").clamp(0.0, 1.0) as f32;
    let colour = cx.params.color("color");
    let opacity = cx.params.f("opacity").clamp(0.0, 1.0) as f32;
    let srcb = cx.params.f("sourceBrightness").clamp(0.0, 4.0) as f32;
    let combine = cx.params.e("combine");
    if opacity <= 0.0 && (srcb - 1.0).abs() < 1e-6 {
        return buf;
    }
    let (wf, hf) = (buf.img.width as f32, buf.img.height as f32);
    let width = buf.img.width as usize;
    let (cx0, cy0) = ((centre[0] as f32 / wf).clamp(0.0, 1.0), (centre[1] as f32 / hf).clamp(0.0, 1.0));
    let (sin, cos) = rot.sin_cos();
    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let x = (i % width) as f32 / wf - cx0;
        let y = (i / width) as f32 / hf - cy0;
        let (rx, ry) = (x * cos + y * sin, -x * sin + y * cos);
        // Relative width/height stretch the ellipse; radius scales it as a whole.
        let (dx, dy) = (rx / (relw * radius * 0.5).max(1e-4), ry / (relh * radius * 0.5).max(1e-4));
        let circle = (dx * dx + dy * dy).sqrt();
        let square = dx.abs().max(dy.abs());
        let d = circle + (square - circle) * squareness;
        // 0 inside the hole, 1 outside; smoothCurve bends the ramp between them.
        let edge = (1.0 - soft * 0.5).max(0.0);
        let mut t = ((d - edge) / soft.max(1e-4)).clamp(0.0, 1.0);
        t = t * t * (3.0 - 2.0 * t);
        t = t + (t * t - t) * smooth;
        let wgt = (t * opacity).clamp(0.0, 1.0);
        let (c, a) = unpremul(*px);
        let c = [c[0] * srcb, c[1] * srcb, c[2] * srcb];
        let mixed = match combine {
            1 => [c[0] * (1.0 - wgt + colour[0] * wgt), c[1] * (1.0 - wgt + colour[1] * wgt), c[2] * (1.0 - wgt + colour[2] * wgt)],
            2 => [
                1.0 - (1.0 - c[0]) * (1.0 - colour[0] * wgt),
                1.0 - (1.0 - c[1]) * (1.0 - colour[1] * wgt),
                1.0 - (1.0 - c[2]) * (1.0 - colour[2] * wgt),
            ],
            _ => [c[0] * (1.0 - wgt) + colour[0] * wgt, c[1] * (1.0 - wgt) + colour[1] * wgt, c[2] * (1.0 - wgt) + colour[2] * wgt],
        };
        *px = premul(mixed, a);
    });
    buf
}
'''

MOD_ANCHOR = "mod color3;\n"
LIB_ANCHOR = "        v.extend(color3::specs());\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    if not path.exists():
        path.write_text(MODULE, encoding="utf-8")
        print("ffx_vintage.rs written")
    lib = root / "crates/effects/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    if MARKER in src:
        print("vintage/vignette already registered")
        return
    if src.count(MOD_ANCHOR) != 1:
        raise SystemExit(f"mod anchor: {src.count(MOD_ANCHOR)}")
    src = src.replace(MOD_ANCHOR, MOD_ANCHOR + "mod ffx_vintage;\n", 1)
    if src.count(LIB_ANCHOR) != 1:
        raise SystemExit(f"registry anchor: {src.count(LIB_ANCHOR)}")
    src = src.replace(LIB_ANCHOR, "        v.extend(ffx_vintage::specs());\n" + LIB_ANCHOR, 1)
    lib.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
    print("registered S_VintageColor3Strip and S_Vignette")


if __name__ == "__main__":
    main()
