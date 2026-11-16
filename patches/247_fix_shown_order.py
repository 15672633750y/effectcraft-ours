#!/usr/bin/env python3
"""修一个致命顺序错误：`shown` 在拟合之前就算好了，导致后面所有调整都没进画面。

The block that applies the fitted colour, the contrast and the radial compensation ran *after*
`let shown = premul(c, a);`, so the phone kept rendering the old dye maths — that is why the exported
frame stayed dark and blue no matter what the coefficients said. `shown` is now computed afterwards.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHOWN_ORDER_V1"

OLD_HEAD = """                _ => {
                    let shown = premul(c, a);
                    // 外推：负值反向、超过 1 加强，任何数值都看得见变化
                    let k = amount;
"""
NEW_HEAD = """                _ => {
                    // 外推：负值反向、超过 1 加强，任何数值都看得见变化
                    let k = amount;
"""

OLD_TAIL = """                            c = [c[0] * g, c[1] * g, c[2] * g];
                        }
                    }
                    [
"""
NEW_TAIL = """                            c = [c[0] * g, c[1] * g, c[2] * g];
                        }
                    }
                    let shown = premul(c, a);
                    [
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("shown order already fixed")
        return
    for old, new in ((OLD_HEAD, NEW_HEAD), (OLD_TAIL, NEW_TAIL)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("shown now computed after the fitted adjustments")


if __name__ == "__main__":
    main()
