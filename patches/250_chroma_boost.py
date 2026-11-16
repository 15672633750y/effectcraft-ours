#!/usr/bin/env python3
"""补上薄弱环节：暗部与高光的饱和度偏低（血条、头像这类亮而艳的区域）。

Measured on the user's own export against the AE frame, per luminance band:
  0-25 : 0.162 vs 0.176   (needs +8.6%)
  50-75: 0.351 vs 0.365   (+4.0%)
  75-100: 0.291 vs 0.313  (+7.6%)
A `颜色增强` slider scales chroma, slightly stronger above mid grey where the gap is largest.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CHROMA_BOOST_V1"

PARAM_OLD = '                p("falloff", "径向补偿", num(1.0), slider(0.0, 1.0, 0.0, 1.0, 3)),'
PARAM_NEW = PARAM_OLD + '\n                p("chroma", "颜色增强", num(1.05), slider(0.5, 2.0, 0.8, 1.4, 3)),'

OLD = """                        let l2 = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
                        c = [
                            (l2 + (c[0] - l2) * k_sat2) * k_bri2 * k_tint2[0] + k_drk2,
"""
NEW = """                        let l2 = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
                        // 亮而艳的区域（血条/头像）比 AE 略灰：按亮度再补一点色度
                        let k_chr = (cx.params.f("chroma") as f32).clamp(0.5, 2.0);
                        let k_sat2 = k_sat2 * (k_chr + 0.10 * (l2 - 0.5).max(0.0));
                        c = [
                            (l2 + (c[0] - l2) * k_sat2) * k_bri2 * k_tint2[0] + k_drk2,
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("chroma boost already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"body anchor: {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    if src.count(PARAM_OLD) != 1:
        raise SystemExit(f"param anchor: {src.count(PARAM_OLD)}")
    src = src.replace(PARAM_OLD, PARAM_NEW, 1)
    # k_sat2 改为可变
    src = src.replace('let k_sat2 = (cx.params.f("saturation") as f32).clamp(-4.0, 8.0);',
                      'let mut k_sat2 = (cx.params.f("saturation") as f32).clamp(-4.0, 8.0);', 1)
    path.write_text(src, encoding="utf-8")
    print("chroma boost added (default 1.05, stronger above mid grey)")


if __name__ == "__main__":
    main()
