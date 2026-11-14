#!/usr/bin/env python3
"""Export resizing: Lanczos 3 for the High setting, the way AfterCodecs' high-quality scaling looks.

Bicubic is fine at 1:1 but soft when the output is much smaller than the render (4K comp exported
at 1080p). Lanczos 3 keeps the detail bicubic loses, with the support widened by the scale factor
so it filters rather than aliases. Filtering runs on the premultiplied frame, so edges stay clean.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LANCZOS_V1"

FUNC = r'''
/// Lanczos 3 kernel.
fn lanczos_kernel(x: f64) -> f64 {
    let ax = x.abs();
    if ax < 1e-9 {
        return 1.0;
    }
    if ax >= 3.0 {
        return 0.0;
    }
    let px = std::f64::consts::PI * x;
    (px.sin() / px) * ((px / 3.0).sin() / (px / 3.0))
}

/// High-quality resample: separable Lanczos 3, support widened for downscaling.
fn lanczos(src: &Image, w: u32, h: u32) -> Image {
    use rayon::prelude::*;
    let (sw, sh) = (src.width.max(1) as usize, src.height.max(1) as usize);
    let (dw, dh) = (w.max(1) as usize, h.max(1) as usize);
    let sx = sw as f64 / dw as f64;
    let sy = sh as f64 / dh as f64;
    let support = |s: f64| if s > 1.0 { 3.0 * s } else { 3.0 };
    let (sup_x, sup_y) = (support(sx), support(sy));
    let (blur_x, blur_y) = (if sx > 1.0 { sx } else { 1.0 }, if sy > 1.0 { sy } else { 1.0 });

    let mut tmp = vec![[0f32; 4]; dw * sh];
    tmp.par_chunks_mut(dw).enumerate().for_each(|(y, row)| {
        for (x, out) in row.iter_mut().enumerate() {
            let center = (x as f64 + 0.5) * sx;
            let lo = ((center - sup_x).floor() as i64).max(0);
            let hi = ((center + sup_x).ceil() as i64).min(sw as i64 - 1);
            let mut acc = [0f64; 4];
            let mut wsum = 0f64;
            for i in lo..=hi {
                let wt = lanczos_kernel((i as f64 + 0.5 - center) / blur_x);
                if wt == 0.0 {
                    continue;
                }
                let p = src.data[y * sw + i as usize];
                for c in 0..4 {
                    acc[c] += f64::from(p[c]) * wt;
                }
                wsum += wt;
            }
            let inv = if wsum.abs() > 1e-12 { 1.0 / wsum } else { 0.0 };
            let mut px = [0f32; 4];
            for c in 0..4 {
                px[c] = (acc[c] * inv) as f32;
            }
            px[3] = px[3].min(1.0);
            *out = px;
        }
    });

    let mut out = Image::new(w.max(1), h.max(1));
    out.data.par_chunks_mut(dw).enumerate().for_each(|(y, row)| {
        let center = (y as f64 + 0.5) * sy;
        let lo = ((center - sup_y).floor() as i64).max(0);
        let hi = ((center + sup_y).ceil() as i64).min(sh as i64 - 1);
        for (x, px) in row.iter_mut().enumerate() {
            let mut acc = [0f64; 4];
            let mut wsum = 0f64;
            for i in lo..=hi {
                let wt = lanczos_kernel((i as f64 + 0.5 - center) / blur_y);
                if wt == 0.0 {
                    continue;
                }
                let p = tmp[i as usize * dw + x];
                for c in 0..4 {
                    acc[c] += f64::from(p[c]) * wt;
                }
                wsum += wt;
            }
            let inv = if wsum.abs() > 1e-12 { 1.0 / wsum } else { 0.0 };
            let mut o = [0f32; 4];
            for c in 0..4 {
                o[c] = (acc[c] * inv) as f32;
            }
            o[3] = o[3].min(1.0);
            *px = o;
        }
    });
    out
}
'''

SWAP_OLD = "            ResizeQuality::High => bicubic(&img, w, h),\n"
SWAP_NEW = "            // EFFECTCRAFT_OURS_LANCZOS_V1 — 高质量缩放用 Lanczos 3（比双三次更锐）\n            ResizeQuality::High => lanczos(&img, w, h),\n"

ANCHOR = "fn bicubic(src: &Image, w: u32, h: u32) -> Image {\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/export/src/pipeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("lanczos already installed")
        return
    if src.count(SWAP_OLD) != 1:
        raise SystemExit(f"resize anchor: {src.count(SWAP_OLD)}")
    src = src.replace(SWAP_OLD, SWAP_NEW, 1)
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"bicubic anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, FUNC + "\n" + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("export High resize uses Lanczos 3")


if __name__ == "__main__":
    main()
