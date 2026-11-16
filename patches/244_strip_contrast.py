#!/usr/bin/env python3
"""三条彩加「对比」滑块并让拟合结果可继续微调（默认值 = 现在的拟合输出）。

残差分析：暗部误差 3.2 已经很准，误差集中在 50–100 亮度带（6.4 / 8.8），来自 AE 那条链的高光压缩与锐化。
加一个默认 1.0 的对比滑块，让高光可以单独往上/往下压，而不动颜色。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STRIP_CONTRAST_V1"

PARAM_OLD = '                p("amount", "Amount", num(1.0), slider(-100.0, 100.0, -2.0, 2.0, 3)),'
PARAM_NEW = PARAM_OLD + '\n                p("contrast", "对比", num(1.0), slider(0.0, 2.0, 0.5, 1.5, 3)),'

MIX_OLD = """                        c = f;"""
MIX_NEW = """                        // 对比：以 0.5 为轴做 S 曲线，1.0 = 不变
                        let k_ct = cx.params.f("contrast").clamp(0.0, 2.0) as f32;
                        let curve = |v: f32| -> f32 {
                            if (k_ct - 1.0).abs() < 1e-4 {
                                v
                            } else {
                                (0.5 + (v - 0.5) * k_ct).clamp(0.0, 1.0)
                            }
                        };
                        c = [curve(f[0]), curve(f[1]), curve(f[2])];"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("contrast slider already present")
        return
    for old, new in ((PARAM_OLD, PARAM_NEW), (MIX_OLD, MIX_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("three-strip has a contrast control on top of the fit")


if __name__ == "__main__":
    main()
