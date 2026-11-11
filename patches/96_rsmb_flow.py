#!/usr/bin/env python3
"""Add a motion-blur effect that uses real optical flow between neighbouring frames.

The effect samples the layer at two nearby times, estimates a per-block motion vector by block
matching on a downsampled luma plane, then averages the layer along each pixel's motion line. Only
moving detail smears; the static background stays sharp.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RSMB_FLOW_V1"

MODULE = r'''//! Optical-flow motion blur (RSMB-style), our own implementation: dense Horn–Schunck flow on a
//! quarter-resolution luma plane, bilinearly upsampled, then the frame is averaged along each
//! pixel's motion vector so only moving detail streaks.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, num, p, popup, slider};

const CATEGORY: &str = "Blur & Sharpen";
const DOWN: usize = 4;
const ITER: usize = 24;

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn luma(px: &[f32; 4]) -> f32 {
    0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]
}

/// Dense Horn–Schunck flow between two quarter-resolution luma planes.
fn horn_schunck(a: &[f32], b: &[f32], w: usize, h: usize, alpha: f32) -> Vec<[f32; 2]> {
    let mut u = vec![0.0f32; w * h];
    let mut v = vec![0.0f32; w * h];
    let idx = |x: usize, y: usize| y * w + x;
    for _ in 0..ITER {
        let mut nu = u.clone();
        let mut nv = v.clone();
        for y in 1..h.saturating_sub(1) {
            for x in 1..w.saturating_sub(1) {
                let i = idx(x, y);
                let ix = (b[i + 1] - b[i - 1] + a[i + 1] - a[i - 1]) * 0.25;
                let iy = (b[i + w] - b[i - w] + a[i + w] - a[i - w]) * 0.25;
                let it = b[i] - a[i];
                let ua = (u[i - 1] + u[i + 1] + u[i - w] + u[i + w]) * 0.25;
                let va = (v[i - 1] + v[i + 1] + v[i - w] + v[i + w]) * 0.25;
                let den = alpha * alpha + ix * ix + iy * iy;
                let t = (ix * ua + iy * va + it) / den.max(1e-6);
                nu[i] = ua - ix * t;
                nv[i] = va - iy * t;
            }
        }
        u = nu;
        v = nv;
    }
    (0..w * h).map(|i| [u[i], v[i]]).collect()
}

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    if !cx.params.b("activation") {
        return buf;
    }
    let amount = cx.params.f("blurAmount").clamp(0.0, 10.0) as f32;
    let sensitivity = (cx.params.f("sensitivity") / 100.0).clamp(0.0, 1.0) as f32;
    if amount <= 0.0 {
        return buf;
    }
    let Some(host) = cx.env.host else { return buf };
    let dt = 1.0 / cx.fps().max(1.0) * 0.5;
    let (Some(prev), Some(next)) = (host.self_at(cx.time - dt, 0), host.self_at(cx.time + dt, 0)) else {
        return buf;
    };
    let w = buf.img.width as usize;
    let h = buf.img.height as usize;
    if prev.img.width != buf.img.width || next.img.width != buf.img.width {
        return buf;
    }

    // Quarter-resolution luma planes.
    let dw = (w / DOWN).max(2);
    let dh = (h / DOWN).max(2);
    let mut pa = vec![0.0f32; dw * dh];
    let mut pb = vec![0.0f32; dw * dh];
    for y in 0..dh {
        for x in 0..dw {
            let sx = (x * DOWN).min(w - 1);
            let sy = (y * DOWN).min(h - 1);
            pa[y * dw + x] = luma(&prev.img.data[sy * w + sx]);
            pb[y * dw + x] = luma(&next.img.data[sy * w + sx]);
        }
    }
    let flow = horn_schunck(&pa, &pb, dw, dh, 0.6);
    // Bring the vectors back to full-resolution pixels (the flow is in quarter pixels).
    let at = |x: usize, y: usize| -> [f32; 2] {
        let gx = (x / DOWN).min(dw - 1);
        let gy = (y / DOWN).min(dh - 1);
        let f = flow[gy * dw + gx];
        [f[0] * DOWN as f32, f[1] * DOWN as f32]
    };

    let src = buf.img.data.clone();
    let prev_data = prev.img.data.clone();
    let next_data = next.img.data.clone();
    let min_mag = (1.0 - sensitivity) * 1.5;
    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let x = i % w;
        let y = i / w;
        let f = at(x, y);
        let mag = (f[0] * f[0] + f[1] * f[1]).sqrt();
        if mag < min_mag {
            return;
        }
        let reach = (mag * amount).min(12.0);
        let (dx, dy) = (f[0] / mag * reach, f[1] / mag * reach);
        let mut acc = [0.0f32; 4];
        let mut n = 0.0f32;
        for s in -3i32..=3 {
            let t = s as f32 / 3.0;
            let sx = (x as f32 + dx * t).round().clamp(0.0, (w - 1) as f32) as usize;
            let sy = (y as f32 + dy * t).round().clamp(0.0, (h - 1) as f32) as usize;
            let sample = if t <= 0.0 { prev_data[sy * w + sx] } else { next_data[sy * w + sx] };
            for k in 0..4 {
                acc[k] += sample[k];
            }
            n += 1.0;
        }
        for k in 0..4 {
            acc[k] /= n;
        }
        let _ = src[i];
        *px = acc;
    });
    buf
}

pub fn specs() -> Vec<EffectSpec> {
    vec![spec(
        "org.effectcraft.compat.revision.rsmb",
        "运动模糊 (RSMB 光流)",
        vec![
            p("activation", "Activation", Value::Bool(true), ParamUi::Checkbox),
            p("useGpu", "使用 GPU", Value::Bool(false), ParamUi::Checkbox),
            p("show", "显示", Value::Enum(0), popup(&["Color Src Blurred", "Result", "Motion Vectors"])),
            p("blurAmount", "主背景:模糊数量", num(0.5), slider(0.0, 10.0, 0.0, 10.0, 3)),
            p("matchMotion", "匹配运动素材", Value::Enum(0), popup(&["无", "源"])),
            p("trackFrame", "跟踪帧", Value::Enum(0), popup(&["自动", "前一帧", "后一帧"])),
            p("trackEnhance", "跟踪增强", Value::Enum(0), popup(&["无", "低", "高"])),
            p("trackRgba", "跟踪 RGB+A", Value::Bool(false), ParamUi::Checkbox),
            p("vr360", "360 视频", Value::Bool(false), ParamUi::Checkbox),
            p("drawGeometry", "绘制几何", Value::Enum(0), popup(&["无", "结果"])),
            p("sensitivity", "灵敏度", num(70.0), slider(0.0, 100.0, 0.0, 100.0, 2)),
            p("imageTrack", "图像跟踪", Value::Bool(true), ParamUi::Checkbox),
            p("maskHead", "主背景:首 Mask", Value::Enum(0), popup(&["无"])),
            p("maskTail", "主背景:尾 Mask", Value::Enum(0), popup(&["无"])),
        ],
        render,
    )]
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    lib = root / "crates/effects/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    (root / "crates/effects/src/rsmb_flow.rs").write_text(MODULE, encoding="utf-8")
    if MARKER in src:
        print("rsmb flow refreshed")
        return
    if src.count("mod color3;\n") != 1:
        raise SystemExit("module anchor not found")
    src = src.replace("mod color3;\n", "mod color3;\nmod rsmb_flow;\n", 1)
    if src.count("        v.extend(color3::specs());\n") != 1:
        raise SystemExit("registry anchor not found")
    src = src.replace(
        "        v.extend(color3::specs());\n",
        "        v.extend(color3::specs());\n        v.extend(rsmb_flow::specs());\n",
        1,
    )
    lib.write_text(f"// {MARKER}\n{src}", encoding="utf-8")
    print("added the optical-flow motion blur effect")


if __name__ == "__main__":
    main()
