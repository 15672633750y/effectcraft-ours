#!/usr/bin/env python3
"""把两个 ffx 效果里「只声明没读取」的参数接进像素计算，并隐藏纯参考线参数。

Found by comparing the declared parameter ids with their uses:

* Vintage: `grainBlur` (average the grain over a box), `keyLayerDensity` (grain frequency),
  `maskUse` (which channel the mask view shows: luma / alpha / none)
* Vignette: `blurAmount` + `blurInside` (blur inside or outside the mask), `effect`
  (Vignette / Ellipse / Rectangle — the rectangle forces the squareness to 1)
* Vignette: `showRadius` / `showRotate` / `showCenter` drew guides in After Effects only; they are
  removed so nobody drags a slider that cannot change the picture.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FFX_PARAMS_LIVE_V1"

VINTAGE_READ_OLD = '''    let grain = cx.params.f("grainAmp").clamp(0.0, 1.0) as f32;
'''
VINTAGE_READ_NEW = '''    let grain = cx.params.f("grainAmp").clamp(0.0, 1.0) as f32;
    // EFFECTCRAFT_OURS_FFX_PARAMS_LIVE_V1 — 这两个参数原来没被读取，拖了没反应
    let grain_density = cx.params.f("keyLayerDensity").clamp(0.0, 1.0) as f32;
    let grain_blur = cx.params.f("grainBlur").clamp(0.0, 20.0) as f32;
    let mask_use = cx.params.e("maskUse");
'''

GRAIN_OLD = '''            if grain > 0.0 {
                let g = (hash(seed ^ (x as u32).wrapping_mul(374761393) ^ (y as u32).wrapping_mul(668265263)) - 0.5) * 2.0;
                let g = g * grain * 0.25;
                c = [c[0] + g, c[1] + g, c[2] + g];
            }
'''
GRAIN_NEW = '''            if grain > 0.0 {
                // 密度：把坐标乘上一个系数改变颗粒频率；模糊：在 3x3 到 41x41 的盒子里取平均
                let dens = (0.05 + grain_density * 3.95).max(0.05);
                let gx = (x as f32 * dens) as u32;
                let gy = (y as f32 * dens) as u32;
                let rad = grain_blur.round() as i64;
                let mut acc;
                if rad <= 0 {
                    acc = hash(seed ^ gx.wrapping_mul(374761393) ^ gy.wrapping_mul(668265263)) - 0.5;
                } else {
                    let rad = rad.min(20);
                    acc = 0.0;
                    let mut n = 0.0f32;
                    for oy in -rad..=rad {
                        for ox in -rad..=rad {
                            let hx = (gx as i64 + ox).max(0) as u32;
                            let hy = (gy as i64 + oy).max(0) as u32;
                            acc += hash(seed ^ hx.wrapping_mul(374761393) ^ hy.wrapping_mul(668265263)) - 0.5;
                            n += 1.0;
                        }
                    }
                    acc /= n.max(1.0);
                }
                let g = acc * 2.0 * grain * 0.25;
                c = [c[0] + g, c[1] + g, c[2] + g];
            }
'''

MASK_OLD = '''            let mut mask = luma(c).clamp(0.0, 1.0);
            if invert {
                mask = 1.0 - mask;
            }
'''
MASK_NEW = '''            // maskUse：0 = 亮度、1 = Alpha、2 = 不遮罩
            let mut mask = match mask_use {
                1 => a.clamp(0.0, 1.0),
                2 => 1.0,
                _ => luma(c).clamp(0.0, 1.0),
            };
            if invert {
                mask = 1.0 - mask;
            }
'''

VIG_READ_OLD = '''    let combine = cx.params.e("combine");
'''
VIG_READ_NEW = '''    let combine = cx.params.e("combine");
    // EFFECTCRAFT_OURS_FFX_PARAMS_LIVE_V1 — 形状 / 模糊两个参数原来没被读取
    let shape = cx.params.e("effect");
    let blur_amount = cx.params.f("blurAmount").clamp(0.0, 100.0) as f32;
    let blur_inside = cx.params.b("blurInside");
'''

SHAPE_OLD = '''        let square = dx.abs().max(dy.abs());
        let d = circle + (square - circle) * squareness;
'''
SHAPE_NEW = '''        let square = dx.abs().max(dy.abs());
        // effect：0 暗角椭圆、1 椭圆、2 矩形（矩形 = 完全方化）
        let sq = if shape == 2 { 1.0 } else { squareness };
        let d = circle + (square - circle) * sq;
'''

# 参考线参数：从面板上撤掉

VIG_LOOP_OLD = "    buf.img.data.par_iter_mut().enumerate().for_each(|(i, px)| {\n"
VIG_LOOP_NEW = "    let mut weights = vec![0.0f32; buf.img.data.len()];\n    buf.img.data.par_iter_mut().zip(weights.par_iter_mut()).enumerate().for_each(|(i, (px, wt))| {\n"

VIG_TAIL_OLD = "        *px = premul(mixed, a);\n    });\n    buf\n}"
VIG_TAIL_NEW = """        *px = premul(mixed, a);
        *wt = wgt;
    });
    // EFFECTCRAFT_OURS_FFX_PARAMS_LIVE_V1 — Blur Amount / Blur Inside
    if blur_amount >= 1.0 {
        let radius = blur_amount.min(60.0) as i64;
        let width = buf.img.width as i64;
        let height = buf.img.height as i64;
        let src = buf.img.data.clone();
        let at = |x: i64, y: i64| -> [f32; 4] {
            let xx = x.clamp(0, width - 1) as usize;
            let yy = y.clamp(0, height - 1) as usize;
            src[yy * width as usize + xx]
        };
        let step = (radius / 6).max(1);
        for y in 0..height {
            for x in 0..width {
                let i = (y * width + x) as usize;
                let inside = weights[i] >= 0.5;
                if inside != blur_inside {
                    continue;
                }
                let mut acc = [0.0f32; 4];
                let mut n = 0.0f32;
                let mut oy = -radius;
                while oy <= radius {
                    let mut ox = -radius;
                    while ox <= radius {
                        let c = at(x + ox, y + oy);
                        acc[0] += c[0];
                        acc[1] += c[1];
                        acc[2] += c[2];
                        acc[3] += c[3];
                        n += 1.0;
                        ox += step;
                    }
                    oy += step;
                }
                if n > 0.0 {
                    buf.img.data[i] = [acc[0] / n, acc[1] / n, acc[2] / n, acc[3] / n];
                }
            }
        }
    }
    buf
}"""

GUIDE_OLD = '''                p("showRadius", "Show Radius", Value::Bool(true), ParamUi::Checkbox),
                p("showRotate", "Show Rotate", Value::Bool(true), ParamUi::Checkbox),
                p("showCenter", "Show Center", Value::Bool(true), ParamUi::Checkbox),
'''
GUIDE_NEW = ''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("params already live")
        return
    for old, new in (
        (VINTAGE_READ_OLD, VINTAGE_READ_NEW),
        (GRAIN_OLD, GRAIN_NEW),
        (MASK_OLD, MASK_NEW),
        (VIG_READ_OLD, VIG_READ_NEW),
        (SHAPE_OLD, SHAPE_NEW),
        (VIG_LOOP_OLD, VIG_LOOP_NEW),
        (VIG_TAIL_OLD, VIG_TAIL_NEW),
        (GUIDE_OLD, GUIDE_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("vintage grain/mask and vignette shape/blur are live")


if __name__ == "__main__":
    main()
