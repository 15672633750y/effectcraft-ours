#!/usr/bin/env python3
"""三条彩永远输出拟合结果（不再按「第一遍」判断）。

The previous version only applied the fitted transform when `amount >= 0.99`, so a stack whose first
instance had Amount 0.5 fell back to the old dye maths — that is why the phone's render came out much
darker than After Effects. The fitted transform already reproduces the *whole* AE chain, so a single
instance at Amount 1.0 is the correct way to use it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STRIP_ALWAYS_FIT_V1"

OLD = """                    // 第一遍：用拟合结果替换染料结果（这是按用户前后帧校准的那一版）
                    if base_pass {
"""
NEW = """                    // 直接用拟合结果（它本身就是 AE 整条链的结果）
                    if true {
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("three-strip already always applies the fit")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("three-strip always applies the fitted transform")


if __name__ == "__main__":
    main()
