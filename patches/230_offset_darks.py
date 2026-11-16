#!/usr/bin/env python3
"""Offset Darks 的量纲：AE 里是 -1..1 的归一化值（默认 0.000），不是百分比。

Screenshots of the AE effect list show `Offset Darks 0.000` next to `Brightness 1.000` and
`Saturation 1.000` — all normalised values. Our render divided it by 100, so a preset's 0.2 lifted the
blacks by 0.002 (invisible) and the slider's range implied a percentage. Both now match AE.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_OFFSET_DARKS_V1"

RANGE_OLD = 'p("offsetDarks", "Offset Darks", num(0.0), slider(-50.0, 50.0, -50.0, 50.0, 3)),'
RANGE_NEW = 'p("offsetDarks", "Offset Darks", num(0.0), slider(-1.0, 1.0, -1.0, 1.0, 3)),'
USE_OLD = "    let darks = (cx.params.f(\"offsetDarks\") / 100.0) as f32;\n"
USE_NEW = "    // AE 的 Offset Darks 是 -1..1 的归一化量，不再除以 100\n    let darks = cx.params.f(\"offsetDarks\") as f32;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("offset darks already normalised")
        return
    for old, new in ((RANGE_OLD, RANGE_NEW), (USE_OLD, USE_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("offset darks matches AE units")


if __name__ == "__main__":
    main()
