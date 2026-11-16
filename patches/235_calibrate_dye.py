#!/usr/bin/env python3
"""按真实前后帧（原图.png / 调色.png）拟合出的系数校准三条彩的染料响应。

Measured from the user's exports (1920x1080, same frame, effects on/off):
  ch0 out = 1.0919*in - 10.20   rms 9.4
  ch1 out = 1.0642*in - 11.99   rms 8.4
  ch2 out = 1.0228*in -  3.39   rms 13.5
The preset stacks two three-strip passes, so each pass takes the square root of the gain:
1.045 / 1.032 / 1.011. The previous coefficients (1.06 / 1.00 / 0.93) pushed blue far too dark.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DYE_CALIBRATED_V1"

OLD = """            let rr = dye(r[0], 1.06, 0.86);
            let gg = dye(base[1], 1.0, 0.95);
            let bb = dye(b[2], 0.93, 1.14);
"""
NEW = """            // 系数来自真实前后帧拟合（两遍叠加后 1.092 / 1.064 / 1.023）
            let rr = dye(r[0], 1.045, 1.0);
            let gg = dye(base[1], 1.032, 1.0);
            let bb = dye(b[2], 1.011, 1.0);
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("dye response already calibrated")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("dye response calibrated to the measured frames")


if __name__ == "__main__":
    main()
