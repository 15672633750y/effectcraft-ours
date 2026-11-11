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

MODULE = r'''//! Optical-flow motion blur (RSMB-style), our own implementation.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, num, p, popup, slider};

const CATEGORY: &str = "Blur & Sharpen";
const BLOCK: usize = 16;

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
}

fn luma(px: &[f32; 4]) -> f32 {
    0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]
}

/// Per-block motion between two frames, in pixels, by SAD block matching.
fn block_flow(a: &Buf, b: &Buf, blocks_x: usize, blocks_y: usize, search: i32) -> Vec<[f32; 2]> {
    let (w, h) = (a.img.width.max(1), a.img.height.max(1));
    let mut out = vec![[0.0f32; 2]; blocks_x * blocks_y];
    let step = BLOCK as i32;
    for by in 0..blocks_y {
        for bx in 0..blocks_x {
            let cx = (bx as i32 * step + step / 2).min(w as i32 - 1);
            let cy = (by as i32 * step + step / 2).min(h as i32 - 1);
            let mut best = (f32::MAX, 0i32, 0i32);
            for dy in -search..=search {
                for dx in -search..=search {
                    let mut sad = 0.0f32;
                    let mut n = 0.0f32;
                    for sy in (0..step).step_by(4) {
                        for sx in (0..step).step_by(4) {
                            let ax = (cx + sx).clamp(0, w as i32 - 1) as usize;
                            let ay = (cy + sy).clamp(0, h as i32 - 1) as usize;
                            let bxx = (cx + sx + dx).clamp(0, w as i32 - 1) as usize;
                            let byy = (cy + sy + dy).clamp(0, h as i32 - 1) as usize;
                            sad += (luma(&a.img.data[ay * w as usize + ax]) - luma(&b.img.data[byy * w as usize + bxx])).abs();
                            n += 1.0;
                        }
                    }
                    let score = if n > 0.0 { sad / n } else { f32::MAX };
                    if score < best.0 {
                        best = (score, dx, dy);
                    }
                }
            }
            out[by * blocks_x + bx] = [best.1 as f32, best.2 as f32];
        }
    }
    out
}

/// Average each block's vector with its neighbours so the field is continuous instead of noisy.
fn smooth(flow: Vec<[f32; 2]>, bx: usize, by: usize) -> Vec<[f32; 2]> {
    let mut out = flow.clone();
    for y in 0..by {
        for x in 0..bx {
            let mut sum = [0.0f32; 2];
            let mut n = 0.0f32;
            for dy in -1i32..=1 {
                for dx in -1i32..=1 {
                    let nx = x as i32 + dx;
                    let ny = y as i32 + dy;
                    if nx < 0 || ny < 0 || nx >= bx as i32 || ny >= by as i32 {
                        continue;
                    }
                    let v = flow[ny as usize * bx + nx as usize];
                    sum[0] += v[0];
                    sum[1] += v[1];
                    n += 1.0;
                }
            }
            if n > 0.0 {
                out[y * bx + x] = [sum[0] / n, sum[1] / n];
            }
        }
    }
    out
}

fn render(cx: &EffectCtx, mut buf: Buf) -> Buf {
    if !cx.params.b("activation") {
        return buf;
    }
    let amount = cx.params.f("blurAmount").clamp(0.0, 10.0) as f32;
    let sensitivity = (cx.params.f("sensitivity") / 100.0).clamp(0.0, 1.0) as f32;
    let Some(host) = cx.env.host else { return buf };
    let dt = 1.0 / cx.fps().max(1.0) * 0.5;
    let (Some(prev), Some(next)) = (host.self_at(cx.time - dt, 0), host.self_at(cx.time + dt, 0)) else {
        return buf;
    };
    if prev.img.width != buf.img.width || next.img.width != buf.img.width {
        return buf;
    }

    let w = buf.img.width as usize;
    let h = buf.img.height as usize;
    let bx = (w + BLOCK - 1) / BLOCK;
    let by = (h + BLOCK - 1) / BLOCK;
    let flow_prev = smooth(block_flow(&buf, &prev, bx, by, 2), bx, by);
    let flow_next = smooth(block_flow(&buf, &next, bx, by, 2), bx, by);

    // The layer at full resolution, kept for sampling along the motion line.
    let src_prev = prev.img.data.clone();
    let src_next = next.img.data.clone();
    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {
        let x = i % w;
        let y = i / w;
        let gx = (x / BLOCK).min(bx - 1);
        let gy = (y / BLOCK).min(by - 1);
        let g = gy * bx + gx;
        let v = [
            (flow_prev[g][0] + flow_next[g][0]) * 0.5,
            (flow_prev[g][1] + flow_next[g][1]) * 0.5,
        ];
        let mag = (v[0] * v[0] + v[1] * v[1]).sqrt();
        if amount <= 0.0 || mag < (1.0 - sensitivity) * 1.2 {
            return;
        }
        // Shutter: how far along the motion line we integrate.
        let reach = (mag * amount * 2.0).clamp(0.0, 16.0);
        let mut acc = [0.0f32; 4];
        let mut n = 0.0f32;
        for s in 0i32..=6 {
            let t = s as f32 / 6.0;
            let dx = (v[0] / mag * reach * t).round() as i32;
            let dy = (v[1] / mag * reach * t).round() as i32;
            let sx = (x as i32 + dx).clamp(0, w as i32 - 1) as usize;
            let sy = (y as i32 + dy).clamp(0, h as i32 - 1) as usize;
            let sample = src_prev[sy * w + sx];
            for k in 0..4 {
                acc[k] += sample[k];
            }
            n += 1.0;
        }
        if n > 0.0 {
            for k in 0..4 {
                acc[k] /= n;
            }
            *px = acc;
        }
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
