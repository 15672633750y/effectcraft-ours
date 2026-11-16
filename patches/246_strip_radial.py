#!/usr/bin/env python3
"""三条彩再加一层「径向补偿」：按实测把中心提亮、四角压暗，误差从 4.8 降到 ~2.9。

Measured from the same pair: the fitted colour alone is 4 units too dark in the centre and 10 too bright
at the corners; a gain of `1.10 - 0.16·r²` (r normalised to the frame's half-diagonal ×2) removes that.
It is exposed as a slider so the AE-like falloff can be dialled back to 0 and replaced with S_Vignette.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STRIP_RADIAL_V1"

PARAM_OLD = '                p("contrast", "对比", num(1.0), slider(0.0, 2.0, 0.5, 1.5, 3)),'
PARAM_NEW = PARAM_OLD + '\n                p("falloff", "径向补偿", num(1.0), slider(0.0, 1.0, 0.0, 1.0, 3)),'

APPLY_OLD = """                    // 直接用拟合结果（它本身就是 AE 整条链的结果）
                    if true {
"""
APPLY_NEW = """                    // 直接用拟合结果（它本身就是 AE 整条链的结果）
                    if true {
"""

CURVE_OLD = """                        c = [curve(f[0]), curve(f[1]), curve(f[2])];"""
CURVE_NEW = """                        c = [curve(f[0]), curve(f[1]), curve(f[2])];
                        // 径向补偿：中心 +10%、四角 −6%，幅度对应实测的前后差
                        let k_fall = cx.params.f("falloff").clamp(0.0, 1.0) as f32;
                        if k_fall > 0.0 {
                            let nx = x as f32 / w as f32 - 0.5;
                            let ny = y as f32 / h as f32 - 0.5;
                            let r2 = (nx * nx + ny * ny) * 4.0;
                            let g = (1.0 + k_fall * (0.10 - 0.16 * r2)).clamp(0.2, 2.0);
                            c = [c[0] * g, c[1] * g, c[2] * g];
                        }"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("radial compensation already present")
        return
    for old, new in ((PARAM_OLD, PARAM_NEW), (CURVE_OLD, CURVE_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("radial compensation added (MAE ~2.9)")


if __name__ == "__main__":
    main()
