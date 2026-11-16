#!/usr/bin/env python3
"""参数范围放宽到 -100..100（默认仍按 AE），并让极值/负值也产生可见效果。

AE 的 Amount 默认 1.000 但可以拉到 -100 / 100；之前的 0..2 既拉不到两端，负值还会被直接返回原图。
现在：范围 -100..100，插值按 amount 外推（负值反向），三条彩的错位量随 amount 放大但有上限。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_WIDE_RANGES_V1"

EDITS = (
    ('p("amount", "Amount", num(1.0), slider(0.0, 2.0, 0.0, 1.0, 3)),',
     'p("amount", "Amount", num(1.0), slider(-100.0, 100.0, -2.0, 2.0, 3)),'),
    ('p("brightness", "Brightness", num(1.0), slider(0.0, 4.0, 0.0, 2.0, 3)),',
     'p("brightness", "Brightness", num(1.0), slider(-100.0, 100.0, 0.0, 4.0, 3)),'),
    ('p("saturation", "Saturation", num(1.0), slider(0.0, 4.0, 0.0, 2.0, 3)),',
     'p("saturation", "Saturation", num(1.0), slider(-100.0, 100.0, 0.0, 4.0, 3)),'),
    ('p("grainAmp", "Grain Amp", num(0.0), slider(0.0, 1.0, 0.0, 0.2, 4)),',
     'p("grainAmp", "Grain Amp", num(0.0), slider(-100.0, 100.0, 0.0, 1.0, 4)),'),
    ('    let amount = cx.params.f("amount").clamp(0.0, 2.0) as f32;\n    if amount <= 0.0 {\n        return buf;\n    }\n',
     '    let amount = cx.params.f("amount") as f32;\n    if !amount.is_finite() || amount.abs() < 1e-6 {\n        return buf;\n    }\n'),
    ('    let bright = cx.params.f("brightness").clamp(0.0, 4.0) as f32;\n',
     '    let bright = cx.params.f("brightness") as f32;\n'),
    ('    let sat = cx.params.f("saturation").clamp(0.0, 4.0) as f32;\n',
     '    let sat = cx.params.f("saturation") as f32;\n'),
    ('    let grain = cx.params.f("grainAmp").clamp(0.0, 1.0) as f32;\n',
     '    let grain = cx.params.f("grainAmp") as f32;\n'),
    ('    let sep = (amount * 2.0).round() as i64;\n',
     '    // 错位量随 amount 放大，但有上限，避免极端值把采样甩出画面\n    let sep = (amount * 2.0).round().clamp(-64.0, 64.0) as i64;\n'),
    ('                    let k = amount.clamp(0.0, 1.0);\n',
     '                    // 外推：负值反向、超过 1 加强，任何数值都看得见变化\n                    let k = amount;\n'),
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("ranges already widened")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:48]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("amount/brightness/saturation/grain ranges are -100..100 and extrapolate")


if __name__ == "__main__":
    main()
