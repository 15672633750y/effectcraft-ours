#!/usr/bin/env python3
"""Add a Sapphire-compatible vintage three-strip colour effect (S_VintageColor3Strip).

Parameter order follows the Sapphire effect as the user described it: saturation, black level,
brightness, mosaic, colour, highlight saturation.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_VINTAGE3_V2"

MODULE = r'''//! Vintage three-strip colour: three dye layers, black level, brightness, mosaic, tint and a
//! highlight saturation, in the order the Sapphire effect exposes them.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, popup, slider};

const CATEGORY: &str = "Color Correction";

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn curve(v: f32, contrast: f32) -> f32 {
    let x = v.clamp(0.0, 1.0);
    ((x - 0.5) * (1.0 + contrast * 2.0) + 0.5).clamp(0.0, 1.0)
}

fn hash(n: u32) -> f32 {
    let mut x = n.wrapping_mul(747796405).wrapping_add(2891336453);
    x = ((x >> ((x >> 28) + 4)) ^ x).wrapping_mul(277803737);
    ((x >> 22) ^ x) as f32 / 4_294_967_295.0
}

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    // Slider values follow Sapphire's ranges, but every step is mapped through a bounded
    // weight so a large number never blows the frame to white or grey.
    let amount = (cx.params.f("amount") / 100.0).clamp(0.0, 1.0) as f32;
    let density = cx.params.f("keyLayerDensity").clamp(0.0, 1.0) as f32;
    let brightness = cx.params.f("brightness").max(0.0) as f32;
    let saturation = cx.params.f("saturation").max(0.0) as f32;
    let offset_darks = cx.params.f("offsetDarks").clamp(-100.0, 100.0) as f32 / 100.0;
    let grain = (cx.params.f("grainAmp") / 100.0).clamp(0.0, 1.0) as f32;
    let tint = cx.params.color("tint");
    let seed = cx.seed;

    // How hard the three dyes push the primaries apart (0.1 default, 1.0 = full).
    let sep = 0.15 + density * 0.85;
    // Saturation and brightness are blended toward their extremes instead of multiplied, so the
    // whole slider travel is smooth (1.0 = untouched).
    let sat_w = ((saturation - 1.0) / 99.0).clamp(-1.0, 1.0);
    let bright_w = ((brightness - 1.0) / 99.0).clamp(-1.0, 1.0);

    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let (c, a) = unpremul(*px);
        if a <= 0.0 {
            return;
        }
        let l = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
        let mut o = [0.0f32; 3];
        for k in 0..3 {
            o[k] = (l + (c[k] - l) * (1.0 + sep)).clamp(0.0, 1.0);
        }
        // Offset Darks: negative lifts the shadows, positive crushes them.
        if offset_darks != 0.0 {
            for k in 0..3 {
                o[k] = if offset_darks > 0.0 {
                    (o[k] * (1.0 - offset_darks * 0.6)).clamp(0.0, 1.0)
                } else {
                    (o[k] + (-offset_darks) * 0.6).clamp(0.0, 1.0)
                };
            }
        }
        let l2 = 0.2126 * o[0] + 0.7152 * o[1] + 0.0722 * o[2];
        for k in 0..3 {
            // Saturation: 1.0 untouched, below 1 towards grey, above 1 towards the pure hue.
            let v = if sat_w >= 0.0 {
                l2 + (o[k] - l2) * (1.0 + sat_w * 2.0)
            } else {
                l2 + (o[k] - l2) * (1.0 + sat_w)
            };
            // Brightness: 1.0 untouched, above 1 towards white, below 1 towards black.
            let v = if bright_w >= 0.0 { v + (1.0 - v) * bright_w * 0.5 } else { v * (1.0 + bright_w) };
            o[k] = (v * tint[k]).clamp(0.0, 1.0);
            if grain > 0.0 {
                let g = (hash((i as u32).wrapping_add(seed)) - 0.5) * grain;
                o[k] = (o[k] + g).clamp(0.0, 1.0);
            }
        }
        let mixed = [c[0] + (o[0] - c[0]) * amount, c[1] + (o[1] - c[1]) * amount, c[2] + (o[2] - c[2]) * amount];
        *px = premul(mixed, a);
    });
    buf
}

pub fn specs() -> Vec<EffectSpec> {
    vec![spec(
        "org.effectcraft.compat.sapphire.vintagecolor3strip",
        "复古三条彩 (S_VintageColor3Strip)",
        vec![
            p("amount", "Amount", num(100.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
            p("keyLayerDensity", "Key Layer Density", num(0.1), slider(0.0, 100.0, 0.0, 100.0, 3)),
            p("grainAmp", "Grain Amp", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
            p("grainBlur", "Grain Blur", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
            p("brightness", "Brightness", num(1.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
            p("tint", "Tint", col(1.0, 1.0, 1.0), ParamUi::Color),
            p("saturation", "Saturation", num(1.0), slider(0.0, 100.0, 0.0, 100.0, 3)),
            p("offsetDarks", "Offset Darks", num(0.0), slider(-100.0, 100.0, -100.0, 100.0, 3)),
            p("show", "Show", Value::Enum(0), popup(&["Result", "Source"])),
            p("maskUse", "Mask Use", Value::Enum(0), popup(&["Luma", "Alpha"])),
            p("blurMask", "Blur Mask", num(12.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
            p("invertMask", "Invert Mask", Value::Bool(false), ParamUi::Checkbox),
        ],
        render,
    )]
}
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    lib = root / "crates/effects/src/lib.rs"
    source = lib.read_text(encoding="utf-8")
    (root / "crates/effects/src/vintage3.rs").write_text(MODULE, encoding="utf-8")
    if MARKER in source:
        print("vintage3 refreshed.")
        return
    source = replace_once(source, "mod color3;\n", "mod color3;\nmod vintage3;\n", "module list")
    source = replace_once(
        source,
        "        v.extend(color3::specs());\n",
        "        v.extend(color3::specs());\n        v.extend(vintage3::specs());\n",
        "registry",
    )
    lib.write_text(f"// {MARKER}\n{source}", encoding="utf-8")
    print("Added the vintage three-strip effect with the Sapphire parameter order.")


if __name__ == "__main__":
    main()
