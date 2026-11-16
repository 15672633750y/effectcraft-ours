#!/usr/bin/env python3
"""亮度护栏：拟合后亮度不得超过实测曲线 +0.08，避免别的素材被推爆。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LUMA_GUARD_V1"

OLD = '                    let shown = premul(c, a);'

NEW = '                    // 护栏：拟合可能把别的素材推亮，亮度最多到实测曲线 +0.08\n                    {\n                        let ly = 0.2126 * base[0] + 0.7152 * base[1] + 0.0722 * base[2];\n                        let lim = tone(ly.clamp(0.0, 1.0)) + 0.08;\n                        let lo = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];\n                        if lo > lim && lo > 1e-4 {\n                            let k = lim / lo;\n                            c = [c[0] * k, c[1] * k, c[2] * k];\n                        }\n                    }\n                    let shown = premul(c, a);'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("luma guard already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("luma guard added")


if __name__ == "__main__":
    main()
