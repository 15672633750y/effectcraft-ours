#!/usr/bin/env python3
"""Blur Mask 真正参与：遮罩视图（Show = Luma/Matte）按它做模糊。

AE 的 Blur Mask 默认 12.00，作用是让遮罩视图边缘柔和。之前它被声明但从未读取，拖动没有任何变化。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BLUR_MASK_V1"

OLD = """            match show {
                1 => premul([mask, mask, mask], a),
                2 => premul([mask, mask, mask], 1.0),
"""
NEW = """            // Blur Mask：遮罩视图按它做盒式模糊（AE 默认 12.00）
            if blur_mask > 0.0 && show != 0 {
                let rad = (blur_mask / 20.0).round().clamp(0.0, 6.0) as i64;
                if rad > 0 {
                    let mut acc = 0.0f32;
                    let mut n = 0.0f32;
                    for oy in -rad..=rad {
                        for ox in -rad..=rad {
                            let (c2, _) = unpremul(at(x + ox, y + oy));
                            acc += luma(c2);
                            n += 1.0;
                        }
                    }
                    if n > 0.0 {
                        mask = acc / n;
                    }
                }
            }
            match show {
                1 => premul([mask, mask, mask], a),
                2 => premul([mask, mask, mask], 1.0),
"""

READ_OLD = '    let mask_use = cx.params.e("maskUse");\n'
READ_NEW = '    let mask_use = cx.params.e("maskUse");\n    let blur_mask = cx.params.f("blurMask").clamp(0.0, 100.0) as f32;\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("Blur Mask already applied")
        return
    for old, new in ((READ_OLD, READ_NEW), (OLD, NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("Blur Mask now blurs the mask view")


if __name__ == "__main__":
    main()
