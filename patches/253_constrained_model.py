#!/usr/bin/env python3
"""换成「亮度曲线 + 色度缩放」的有约束模型：单帧误差略大，但换素材不会崩。

The cubic polynomial matched one frame but carried no guarantee elsewhere: on other clips it brightened
by 15+, lost contrast and clipped up to 8% of pixels. This model keeps the same measured look but is
monotone in luminance and only scales chroma, so a different clip cannot be inverted or blown out.

Fitted on the same pair: 17-knot luma curve, chroma gain 0.455 + 0.617·luma.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CONSTRAINED_V1"

NEW_FN = '''/// 亮度曲线（17 段折线，来自实测的前后帧）
const KNOTS: [(f32, f32); 17] = [
    (0.0401, 0.0201), (0.0940, 0.0646), (0.1514, 0.1200), (0.2062, 0.1705),
    (0.2730, 0.2435), (0.3188, 0.2957), (0.3787, 0.3650), (0.4365, 0.4311),
    (0.4967, 0.5002), (0.5582, 0.5596), (0.6165, 0.6401), (0.6753, 0.7015),
    (0.7342, 0.7772), (0.7930, 0.8507), (0.8546, 0.9108), (0.9105, 0.9213),
    (0.9712, 0.9823),
];

fn tone(y: f32) -> f32 {
    let y = y.clamp(0.0, 1.0);
    if y <= KNOTS[0].0 {
        return y * KNOTS[0].1 / KNOTS[0].0.max(1e-4);
    }
    for i in 0..KNOTS.len() - 1 {
        let (x0, y0) = KNOTS[i];
        let (x1, y1) = KNOTS[i + 1];
        if y <= x1 {
            let t = (y - x0) / (x1 - x0).max(1e-6);
            return y0 + (y1 - y0) * t;
        }
    }
    KNOTS[KNOTS.len() - 1].1
}

/// 有约束的调色：只改亮度曲线与色度强度，不做通道交叉，所以换素材也不会翻色/爆掉。
fn fitted(r: f32, g: f32, b: f32) -> [f32; 3] {
    let y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    let k = 0.455 + 0.617 * y;
    let cr = (r - y) * k;
    let cb = (b - y) * k;
    let y2 = tone(y);
    let rr = y2 + cr;
    let bb = y2 + cb;
    let gg = (y2 - 0.2126 * rr - 0.0722 * bb) / 0.7152;
    [rr.clamp(0.0, 1.0), gg.clamp(0.0, 1.0), bb.clamp(0.0, 1.0)]
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("constrained model already installed")
        return
    start = src.index("/// 拟合系数")
    end = src.index("fn render_vintage")
    src = src[:start] + NEW_FN + "\n" + src[end:]
    path.write_text(src, encoding="utf-8")
    print("three-strip now uses the constrained curve + chroma model")


if __name__ == "__main__":
    main()
