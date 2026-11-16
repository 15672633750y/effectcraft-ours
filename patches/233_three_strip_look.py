#!/usr/bin/env python3
"""三条彩按「染料片」的减色响应算，默认值就有明显的老胶片色调。

Evidence: the preset stores *default* values for both S_VintageColor3Strip and S_Vignette (see the AE
screenshots), yet the graded frame is strongly magenta/warm — so the effect itself, at defaults, must
shift colour far more than a 2 px strip offset does. Three-strip film is subtractive: each dye layer
has its own response and bleeds into its neighbours, which is what gives the warm cast. This models
that instead of a bare sideways shift.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_THREE_STRIP_LOOK_V1"

OLD = "            let mut c = [r[0], base[1], b[2]];\n"
NEW = """            // 三条彩：每条染料片的响应不同（红片偏亮、蓝片偏暗），再互相串一点色
            let dye = |v: f32, gain: f32, gamma: f32| -> f32 { (v.max(0.0).powf(gamma) * gain).clamp(0.0, 4.0) };
            let rr = dye(r[0], 1.06, 0.86);
            let gg = dye(base[1], 1.0, 0.95);
            let bb = dye(b[2], 0.93, 1.14);
            let mut c = [
                rr * 0.94 + gg * 0.04 + bb * 0.02,
                gg * 0.93 + rr * 0.05 + bb * 0.02,
                bb * 0.92 + gg * 0.06 + rr * 0.02,
            ];
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("three-strip dye response already in place")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("three-strip dye response added")


if __name__ == "__main__":
    main()
