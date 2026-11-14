#!/usr/bin/env python3
"""The four Sapphire effects the user's presets ask for: Glow, Rays, TextureFlux, DropShadow.

小遇调色.ffx and cze流光文字.ffx reference S_Glow, S_Rays, S_TextureFlux and S_DropShadow; none of
them existed, so the presets imported as empty groups. These are real implementations over the
shared blur helpers (a glow that is blurred brightness added back, a drop shadow that is the matte
blurred and offset, radial rays marched from a centre, and a noise-warped texture), not stubs.

Parameters keep the names the presets reference where one could be identified (Glow Width,
Glow From Alpha, Glow Under Source, Light Rays|Dark Rays, Shadow Color, Softness …), so a preset
that sets them changes the picture.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SAPPHIRE_FX_V1"

MODULE = r'''//! Sapphire-compatible Glow / Rays / TextureFlux / DropShadow.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{gauss_plane, premul, unpremul, Plane};
use crate::{Buf, EffectCtx, EffectSpec, col, num, p, popup, slider};

fn spec(id: &'static str, name: &'static str, category: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category, params, render, gpu: false, float: true }
}

fn luma(c: [f32; 3]) -> f32 {
    0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
}

fn hash(mut x: u32) -> f32 {
    x = x.wrapping_mul(747796405).wrapping_add(2891336453);
    x = ((x >> ((x >> 28) + 4)) ^ x).wrapping_mul(277803737);
    ((x >> 22) ^ x) as f32 / 4_294_967_295.0
}

/// Value noise in 0..1 at (x, y).
fn noise(x: f32, y: f32, seed: u32) -> f32 {
    let (xi, yi) = (x.floor(), y.floor());
    let (fx, fy) = (x - xi, y - yi);
    let (sx, sy) = (fx * fx * (3.0 - 2.0 * fx), fy * fy * (3.0 - 2.0 * fy));
    let at = |dx: i32, dy: i32| {
        let u = (xi as i64 + i64::from(dx)) as u32;
        let v = (yi as i64 + i64::from(dy)) as u32;
        hash(u.wrapping_mul(374761393).wrapping_add(v.wrapping_mul(668265263)).wrapping_add(seed))
    };
    let (a, b, c, d) = (at(0, 0), at(1, 0), at(0, 1), at(1, 1));
    let top = a + (b - a) * sx;
    let bottom = c + (d - c) * sx;
    top + (bottom - top) * sy
}

fn specs() -> Vec<EffectSpec> {
    vec![
        spec(
            "S_Glow",
            "辉光 (S_Glow)",
            "Stylize",
            vec![
                p("glow", "Glow", num(100.0), slider(0.0, 300.0, 0.0, 300.0, 0)),
                p("glowWidth", "Glow Width", num(25.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
                p("brightness", "Brightness", num(100.0), slider(0.0, 200.0, 0.0, 200.0, 0)),
                p("glowColor", "Glow Color", col(1.0, 1.0, 1.0), ParamUi::Color),
                p("glowFromAlpha", "Glow From Alpha", Value::Bool(false), ParamUi::Checkbox),
                p("glowUnderSource", "Glow Under Source", Value::Bool(false), ParamUi::Checkbox),
            ],
            render_glow,
        ),
        spec(
            "S_Rays",
            "光芒 (S_Rays)",
            "Generate",
            vec![
                p("rayKind", "Light Rays|Dark Rays", Value::Enum(0), popup(&["Light Rays", "Dark Rays"])),
                p("centerX", "Center X", num(50.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
                p("centerY", "Center Y", num(50.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
                p("length", "Length", num(50.0), slider(0.0, 100.0, 0.0, 100.0, 0)),
                p("raysBrightness", "Rays Brightness", num(100.0), slider(0.0, 300.0, 0.0, 300.0, 0)),
                p("threshold", "Threshold", num(20.0), slider(0.0, 100.0, 0.0, 100.0, 0)),
            ],
            render_rays,
        ),
        spec(
            "S_TextureFlux",
            "纹理流 (S_TextureFlux)",
            "Distort",
            vec![
                p("amount", "Amount", num(35.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
                p("frequency", "Frequency", num(25.0), slider(1.0, 100.0, 1.0, 100.0, 1)),
                p("speed", "Speed", num(20.0), slider(-100.0, 100.0, -100.0, 100.0, 0)),
                p("detail", "Detail", num(3.0), slider(1.0, 6.0, 1.0, 6.0, 0)),
                p("seed", "Random Seed", num(1.0), slider(0.0, 100.0, 0.0, 100.0, 0)),
            ],
            render_texture_flux,
        ),
        spec(
            "S_DropShadow",
            "投影 (S_DropShadow)",
            "Perspective",
            vec![
                p("distance", "Distance", num(12.0), slider(0.0, 200.0, 0.0, 200.0, 1)),
                p("direction", "Direction", num(135.0), slider(0.0, 360.0, 0.0, 360.0, 0)),
                p("softness", "Softness", num(14.0), slider(0.0, 100.0, 0.0, 100.0, 1)),
                p("opacity", "Opacity", num(60.0), slider(0.0, 100.0, 0.0, 100.0, 0)),
                p("shadowColor", "Shadow Color", col(0.0, 0.0, 0.0), ParamUi::Color),
            ],
            render_drop_shadow,
        ),
    ]
}

fn render_glow(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let amount = (cx.params.f("glow") / 100.0).clamp(0.0, 4.0) as f32;
    let width = cx.params.f("glowWidth").clamp(0.0, 100.0) as f32;
    let bright = (cx.params.f("brightness") / 100.0).clamp(0.0, 4.0) as f32;
    let colour = cx.params.color("glowColor");
    let from_alpha = cx.params.b("glowFromAlpha");
    let under = cx.params.b("glowUnderSource");
    let img = &buf.img;
    let src = Plane::from_image(img, move |px| {
        let (c, a) = unpremul(px);
        if from_alpha {
            (px[3] * bright).clamp(0.0, 1.0)
        } else {
            (luma(c) * bright).clamp(0.0, 1.0) * a
        }
    });
    let sigma = f64::from(width) * 0.5;
    let blurred = gauss_plane(&src, sigma, sigma);
    let g = &blurred.data;
    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let glow = g.get(i).copied().unwrap_or(0.0) * amount;
        if glow <= 0.0 {
            return;
        }
        let (c, a) = unpremul(*px);
        let add = [colour[0] * glow, colour[1] * glow, colour[2] * glow];
        let k = if under { 1.0 - a } else { 1.0 };
        let out = [c[0] + add[0] * k, c[1] + add[1] * k, c[2] + add[2] * k];
        let a_out = (a + (glow * k) * colour[3]).clamp(0.0, 1.0);
        *px = premul(out, a_out);
    });
    buf
}

fn render_drop_shadow(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let dist = cx.params.f("distance").clamp(0.0, 400.0);
    let dir = cx.params.f("direction").to_radians();
    let soft = cx.params.f("softness").clamp(0.0, 200.0);
    let opacity = (cx.params.f("opacity") / 100.0).clamp(0.0, 1.0) as f32;
    let colour = cx.params.color("shadowColor");
    let alpha = Plane::alpha(&buf.img);
    let sigma = soft * 0.5;
    let blurred = gauss_plane(&alpha, sigma, sigma);
    let ox = (dist * dir.cos()) as i64;
    let oy = (dist * dir.sin()) as i64;
    let w = buf.img.width as i64;
    let src = &buf.img.data;
    let out: Vec<[f32; 4]> = (0..src.len())
        .into_par_iter()
        .map(|i| {
            let x = (i as i64) % w;
            let y = (i as i64) / w;
            let sa = (blurred.get_clamped(x - ox, y - oy) * opacity).clamp(0.0, 1.0);
            let (c, a) = unpremul(src[i]);
            let shadow = [colour[0] * sa, colour[1] * sa, colour[2] * sa];
            // Source over the shadow.
            let a_out = a + sa * (1.0 - a);
            if a_out <= 0.0 {
                return [0.0; 4];
            }
            let k = a * (1.0 / a_out);
            let ks = sa * (1.0 - a) / a_out;
            premul([c[0] * k + shadow[0] * ks, c[1] * k + shadow[1] * ks, c[2] * k + shadow[2] * ks], a_out)
        })
        .collect();
    buf.img.data = out;
    buf
}

fn render_rays(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let dark = cx.params.e("rayKind") == 1;
    let brightness = (cx.params.f("raysBrightness") / 100.0).clamp(0.0, 4.0) as f32;
    let threshold = (cx.params.f("threshold") / 100.0).clamp(0.0, 1.0) as f32;
    let length = (cx.params.f("length") / 100.0).clamp(0.0, 1.0) as f32;
    let img = &buf.img;
    let (w, h) = (img.width as f32, img.height as f32);
    let cx0 = (cx.params.f("centerX") / 100.0).clamp(0.0, 1.0) as f32 * w;
    let cy0 = (cx.params.f("centerY") / 100.0).clamp(0.0, 1.0) as f32 * h;
    let lum = Plane::from_image(img, |px| {
        let (c, a) = unpremul(px);
        luma(c) * a
    });
    let max_r = (w.max(h)) * length;
    let steps = 24;
    let rays: Vec<f32> = (0..lum.data.len())
        .into_par_iter()
        .map(|i| {
            let x = (i % lum.w as usize) as f32 + 0.5;
            let y = (i / lum.w as usize) as f32 + 0.5;
            let (dx, dy) = (x - cx0, y - cy0);
            let dist = (dx * dx + dy * dy).sqrt();
            if dist < 1.0 || max_r <= 0.0 {
                return 0.0;
            }
            let (ux, uy) = (dx / dist, dy / dist);
            let mut acc = 0.0f32;
            for k in 0..steps {
                let t = dist - (dist.min(max_r)) * (k as f32 / steps as f32);
                let s = lum.sample(f64::from(cx0 + ux * t), f64::from(cy0 + uy * t));
                acc = acc.max(s);
            }
            ((acc - threshold) / (1.0 - threshold).max(0.001)).clamp(0.0, 1.0)
        })
        .collect();
    let data = &mut buf.img.data;
    data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let r = rays.get(i).copied().unwrap_or(0.0) * brightness;
        if r <= 0.0 {
            return;
        }
        let (c, a) = unpremul(*px);
        let out = if dark { [c[0] * (1.0 - r.min(1.0)), c[1] * (1.0 - r.min(1.0)), c[2] * (1.0 - r.min(1.0))] } else { [c[0] + r, c[1] + r, c[2] + r] };
        *px = premul(out, a);
    });
    buf
}

fn render_texture_flux(cx: &EffectCtx, mut buf: Buf) -> Buf {
    let amount = (cx.params.f("amount") / 100.0).clamp(0.0, 1.0) as f32;
    let freq = (cx.params.f("frequency") / 100.0).clamp(0.01, 1.0) as f32;
    let speed = cx.params.f("speed") as f32;
    let detail = cx.params.f("detail").clamp(1.0, 6.0) as u32;
    let seed = (cx.params.f("seed") * 977.0) as u32 ^ cx.seed;
    let t = cx.time as f32 * speed * 0.01;
    let img = &buf.img;
    let (w, h) = (img.width as f32, img.height as f32);
    let src = img.data.clone();
    let step = 12.0 / w.max(h);
    let out: Vec<[f32; 4]> = (0..src.len())
        .into_par_iter()
        .map(|i| {
            let x = (i % img.width as usize) as f32;
            let y = (i / img.width as usize) as f32;
            // Two octaves of value noise give the flowing texture.
            let mut nx = 0.0f32;
            let mut ny = 0.0f32;
            let mut amp = 1.0f32;
            let mut f = freq * 8.0;
            for o in 0..detail {
                nx += (noise(x * step * f + t, y * step * f, seed.wrapping_add(o * 31)) - 0.5) * amp;
                ny += (noise(x * step * f, y * step * f - t, seed.wrapping_add(o * 57 + 7)) - 0.5) * amp;
                amp *= 0.5;
                f *= 2.0;
            }
            let dx = nx * amount * 40.0;
            let dy = ny * amount * 40.0;
            let sx = (x + dx).clamp(0.0, w - 1.0);
            let sy = (y + dy).clamp(0.0, h - 1.0);
            let x0 = sx.floor() as usize;
            let y0 = sy.floor() as usize;
            let x1 = (x0 + 1).min(img.width as usize - 1);
            let y1 = (y0 + 1).min(img.height as usize - 1);
            let (fx, fy) = (sx - x0 as f32, sy - y0 as f32);
            let at = |xx: usize, yy: usize| src[yy * img.width as usize + xx];
            let (p00, p10, p01, p11) = (at(x0, y0), at(x1, y0), at(x0, y1), at(x1, y1));
            let mut o = [0.0f32; 4];
            for k in 0..4 {
                let top = p00[k] + (p10[k] - p00[k]) * fx;
                let bottom = p01[k] + (p11[k] - p01[k]) * fx;
                o[k] = top + (bottom - top) * fy;
            }
            o
        })
        .collect();
    buf.img.data = out;
    buf
}
'''

LIB_ANCHOR = "        v.extend(color3::specs());\n"
MOD_ANCHOR = "mod color3;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/sapphire_fx.rs"
    if not path.exists():
        path.write_text(MODULE, encoding="utf-8")
        print("sapphire_fx.rs written")
    lib = root / "crates/effects/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(MOD_ANCHOR) != 1:
            raise SystemExit(f"mod anchor: {src.count(MOD_ANCHOR)}")
        src = src.replace(MOD_ANCHOR, MOD_ANCHOR + "mod sapphire_fx;\n", 1)
        if src.count(LIB_ANCHOR) != 1:
            raise SystemExit(f"registry anchor: {src.count(LIB_ANCHOR)}")
        src = src.replace(LIB_ANCHOR, LIB_ANCHOR + "        v.extend(sapphire_fx::specs());\n", 1)
        lib.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
        print("registered Glow / Rays / TextureFlux / DropShadow")


if __name__ == "__main__":
    main()
