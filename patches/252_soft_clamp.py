#!/usr/bin/env python3
"""拟合输出改成软限幅：避免别的片子里高饱和/极亮区域被硬夹断出现色块。

A hard `clamp(0,1)` on the fitted value makes very bright or very saturated input posterise on other
footage (the fit was measured on one frame). A soft knee keeps the look on that frame but rolls off
smoothly above 0.9, so out-of-range colours bend instead of clipping.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SOFT_CLAMP_V1"

OLD = """        out[c] = FIT[c].iter().zip(f.iter()).map(|(k, x)| k * x).sum::<f32>().clamp(0.0, 1.0);"""
NEW = """        let v: f32 = FIT[c].iter().zip(f.iter()).map(|(k, x)| k * x).sum();
        // 软限幅：0.9 以上平滑压回，0 以下平滑提回，避免别的素材硬夹出色块
        let v = if v > 0.9 {
            0.9 + 0.1 * (1.0 - (-(v - 0.9) / 0.1).exp())
        } else if v < 0.02 {
            v.max(0.0)
        } else {
            v
        };
        out[c] = v;"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("soft clamp already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("fitted output uses a soft knee")


if __name__ == "__main__":
    main()
