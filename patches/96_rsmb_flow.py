#!/usr/bin/env python3
"""Motion blur by accumulating the layer over the shutter interval (the way RSMB/Bread actually look)."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RSMB_ACCUM_V1"

MODULE = r'''//! Motion blur by shutter accumulation: sample the layer at several times inside the shutter
//! window and average them. Static content is identical in every sample and stays sharp; anything
//! that moves leaves a continuous streak.

use effectcraft_keyframe::Value;
use effectcraft_project::ParamUi;
use rayon::prelude::*;

use crate::util::{premul, unpremul};
use crate::{Buf, EffectCtx, EffectSpec, num, p, popup, slider};

const CATEGORY: &str = "Blur & Sharpen";

fn spec(id: &'static str, name: &'static str, params: Vec<crate::ParamSpec>, render: crate::RenderFn) -> EffectSpec {
    EffectSpec { id, name, category: CATEGORY, params, render, gpu: false, float: true }
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

    // 敏感度 decides how many frames are averaged; 模糊程度 decides how wide the shutter is.
    let samples = (3.0 + sensitivity * 21.0).round() as usize;
    let fps = cx.fps().max(1.0);
    let window = (amount * 0.5 / fps).max(1.0 / fps * 0.05);

    let mut acc: Option<Vec<[f32; 4]>> = None;
    let mut used = 0usize;
    for k in 0..samples {
        let t = if samples <= 1 {
            cx.time
        } else {
            cx.time - window * 0.5 + window * (k as f64) / ((samples - 1) as f64)
        };
        let Some(frame) = host.self_at(t, 0) else { continue };
        if frame.img.width != buf.img.width || frame.img.height != buf.img.height {
            continue;
        }
        match acc.as_mut() {
            None => acc = Some(frame.img.data.clone()),
            Some(a) => {
                for (dst, src) in a.iter_mut().zip(frame.img.data.iter()) {
                    for c in 0..4 {
                        dst[c] += src[c];
                    }
                }
            }
        }
        used += 1;
    }
    let Some(sum) = acc else { return buf };
    if used == 0 {
        return buf;
    }
    let inv = 1.0 / used as f32;
    buf.img.data.par_iter_mut().zip(sum.par_iter()).for_each(|(px, s)| {
        let mut out = [0.0f32; 4];
        for c in 0..4 {
            out[c] = s[c] * inv;
        }
        let _ = unpremul(*px);
        *px = premul([out[0], out[1], out[2]], out[3].clamp(0.0, 1.0));
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
        print("rsmb accumulation refreshed")
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
    print("motion blur is now shutter accumulation")


if __name__ == "__main__":
    main()
