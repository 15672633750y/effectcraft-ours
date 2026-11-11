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
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, slider};

const CATEGORY: &str = "Color Correction";

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn curve(v: f32, contrast: f32) -> f32 {
    let x = v.clamp(0.0, 1.0);
    ((x - 0.5) * (1.0 + contrast * 2.0) + 0.5).clamp(0.0, 1.0)
}

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let saturation = cx.params.f("saturation").max(0.0) as f32;
    let black = cx.params.f("blackLevel").clamp(-1.0, 1.0) as f32;
    let brightness = cx.params.f("brightness").max(0.0) as f32;
    let mosaic = cx.params.f("mosaic").max(0.0) as f32;
    let tint = cx.params.color("color");
    let saturation2 = cx.params.f("saturation2").max(0.0) as f32;

    let iw = buf.img.width.max(1) as usize;
    let ih = buf.img.height.max(1) as usize;

    // Mosaic: each block samples its top-left pixel, which is enough for the effect's slider.
    if mosaic >= 1.0 {
        let block = mosaic.round() as usize;
        let src = buf.img.data.clone();
        buf.img.data.par_chunks_mut(iw).enumerate().for_each(|(y, row)| {
            let sy = (y / block) * block;
            for x in 0..iw {
                let sx = (x / block) * block;
                row[x] = src[sy * iw + sx];
            }
        });
    }

    // Classic three-strip dyes, fixed: cyan, magenta and yellow transmittances.
    let dye_r = [0.92f32, 0.96, 1.00];
    let dye_g = [1.00f32, 0.94, 0.97];
    let dye_b = [1.00f32, 0.97, 0.88];

    buf.img.data.par_iter_mut().for_each(|px| {
        let (c, a) = unpremul(*px);
        if a <= 0.0 {
            return;
        }
        let dr = (1.0 - c[0]).clamp(0.0, 1.0);
        let dg = (1.0 - c[1]).clamp(0.0, 1.0);
        let db = (1.0 - c[2]).clamp(0.0, 1.0);
        let mut o = [0.0f32; 3];
        for k in 0..3 {
            o[k] = dye_r[k].clamp(0.0001, 1.0).powf(dr)
                * dye_g[k].clamp(0.0001, 1.0).powf(dg)
                * dye_b[k].clamp(0.0001, 1.0).powf(db);
        }

        // Black level: positive darkens the shadows and keeps white at white.
        if black != 0.0 {
            for k in 0..3 {
                let v = o[k];
                o[k] = if black > 0.0 {
                    ((v - black * 0.35).max(0.0) / (1.0 - black * 0.35)).clamp(0.0, 1.0)
                } else {
                    (v + (-black) * (1.0 - v)).clamp(0.0, 1.0)
                };
            }
        }

        // Brightness, then the two saturations (the second only on the highlights).
        let l = 0.2126 * o[0] + 0.7152 * o[1] + 0.0722 * o[2];
        for k in 0..3 {
            let mut v = (o[k] * brightness).clamp(0.0, 1.0);
            v = (l + (v - l) * saturation).clamp(0.0, 1.0);
            let hl = ((v - 0.5) / 0.5).clamp(0.0, 1.0);
            let l2 = 0.2126 * o[0] + 0.7152 * o[1] + 0.0722 * o[2];
            let v2 = (l2 + (v - l2) * saturation2).clamp(0.0, 1.0);
            o[k] = v + (v2 - v) * hl;
        }

        // Colour: a plain multiply, white leaves the image alone.
        for k in 0..3 {
            o[k] = (o[k] * tint[k]).clamp(0.0, 1.0);
        }

        *px = premul(o, a);
    });
    buf
}

pub fn specs() -> Vec<EffectSpec> {
    vec![spec(
        "org.effectcraft.compat.sapphire.vintagecolor3strip",
        "复古三条彩 (S_VintageColor3Strip)",
        vec![
            p("saturation", "Saturation", num(1.0), slider(0.0, 3.0, 0.0, 3.0, 3)),
            p("blackLevel", "Black Level", num(0.0), slider(-1.0, 1.0, -1.0, 1.0, 3)),
            p("brightness", "Brightness", num(1.0), slider(0.0, 3.0, 0.0, 3.0, 3)),
            p("mosaic", "Mosaic", num(0.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
            p("color", "Color", col(1.0, 1.0, 1.0), ParamUi::Color),
            p("saturation2", "Saturation 2", num(1.0), slider(0.0, 3.0, 0.0, 3.0, 3)),
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
