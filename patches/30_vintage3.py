#!/usr/bin/env python3
"""Add a Sapphire-compatible "vintage three-strip colour" effect.

The effect is our own implementation of the classic three-strip look (separate red, green and
blue dye layers, each with its own tint, plus contrast, grain and vignette). It is registered
under Sapphire's id so an imported project that references S_VintageColor3Strip resolves to it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_VINTAGE3_V1"

MODULE = r'''//! Vintage three-strip colour, our own implementation of the classic Technicolor look.
//!
//! Three dye layers (red, green, blue) each pass their channel with its own tint, multiplied
//! together the way stacked dyes work, then contrast, saturation, grain and a vignette finish it.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, slider};

const CATEGORY: &str = "Color Correction";

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn pct() -> ParamUi { slider(0.0, 100.0, 0.0, 100.0, 1) }

fn hash(n: u32) -> f32 {
    let mut x = n.wrapping_mul(747796405).wrapping_add(2891336453);
    x = ((x >> ((x >> 28) + 4)) ^ x).wrapping_mul(277803737);
    ((x >> 22) ^ x) as f32 / 4_294_967_295.0
}

fn curve(v: f32, contrast: f32) -> f32 {
    // Symmetric S-curve around 0.5; contrast 0 leaves the value alone.
    let x = v.clamp(0.0, 1.0);
    let s = (x - 0.5) * (1.0 + contrast * 2.0) + 0.5;
    s.clamp(0.0, 1.0)
}

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let amount = (cx.params.f("amount") / 100.0).clamp(0.0, 1.0) as f32;
    let contrast = cx.params.f("contrast") as f32;
    let saturation = cx.params.f("saturation") as f32;
    let grain = cx.params.f("grain") as f32;
    let vignette = cx.params.f("vignette") as f32;
    let tint_r = cx.params.color("tintRed");
    let tint_g = cx.params.color("tintGreen");
    let tint_b = cx.params.color("tintBlue");
    let seed = cx.seed;
    let iw = buf.img.width.max(1) as usize;
    let (w, h) = (iw as f32, buf.img.height.max(1) as f32);
    let cx2 = w * 0.5;
    let cy2 = h * 0.5;
    let max_r = (cx2 * cx2 + cy2 * cy2).sqrt().max(1.0);

    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let (c, a) = unpremul(*px);
        if a <= 0.0 {
            return;
        }
        // Dye densities: how much of each dye passes this pixel.
        let dr = (1.0 - c[0]).clamp(0.0, 1.0);
        let dg = (1.0 - c[1]).clamp(0.0, 1.0);
        let db = (1.0 - c[2]).clamp(0.0, 1.0);
        let mut o = [0.0f32; 3];
        for k in 0..3 {
            let pr = tint_r[k].clamp(0.0001, 1.0);
            let pg = tint_g[k].clamp(0.0001, 1.0);
            let pb = tint_b[k].clamp(0.0001, 1.0);
            o[k] = pr.powf(dr) * pg.powf(dg) * pb.powf(db);
        }
        // Contrast and saturation.
        let l = 0.2126 * o[0] + 0.7152 * o[1] + 0.0722 * o[2];
        for k in 0..3 {
            let v = curve(o[k], contrast);
            o[k] = (l + (v - l) * saturation).clamp(0.0, 1.0);
        }
        // Grain.
        if grain > 0.0 {
            let g = (hash((i as u32).wrapping_add(seed)) - 0.5) * grain;
            for k in 0..3 { o[k] = (o[k] + g).clamp(0.0, 1.0); }
        }
        // Vignette.
        if vignette > 0.0 {
            let x = (i % iw) as f32 + 0.5;
            let y = (i / iw) as f32 + 0.5;
            let dx = x - cx2;
            let dy = y - cy2;
            let d = (dx * dx + dy * dy).sqrt() / max_r;
            let f = 1.0 - vignette * d * d;
            for k in 0..3 { o[k] = (o[k] * f.clamp(0.0, 1.0)).clamp(0.0, 1.0); }
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
            p("amount", "Amount", num(100.0), pct()),
            p("contrast", "Contrast", num(0.35), slider(-1.0, 1.0, -1.0, 1.0, 2)),
            p("saturation", "Saturation", num(1.15), slider(0.0, 3.0, 0.0, 3.0, 2)),
            p("grain", "Grain", num(0.10), slider(0.0, 1.0, 0.0, 1.0, 3)),
            p("vignette", "Vignette", num(0.25), slider(0.0, 1.0, 0.0, 1.0, 3)),
            p("tintRed", "Red Dye", col(0.93, 0.96, 1.0), ParamUi::Color),
            p("tintGreen", "Green Dye", col(1.0, 0.94, 0.97), ParamUi::Color),
            p("tintBlue", "Blue Dye", col(1.0, 0.97, 0.88), ParamUi::Color),
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
    if MARKER in source:
        print("vintage3 is already installed.")
        return
    (root / "crates/effects/src/vintage3.rs").write_text(MODULE, encoding="utf-8")
    source = replace_once(source, "mod color3;\n", "mod color3;\nmod vintage3;\n", "module list")
    source = replace_once(
        source,
        "        v.extend(color3::specs());\n",
        "        v.extend(color3::specs());\n        v.extend(vintage3::specs());\n",
        "registry",
    )
    source = f"// {MARKER}\n" + source
    lib.write_text(source, encoding="utf-8")
    print("Added S_VintageColor3Strip.")


if __name__ == "__main__":
    main()
