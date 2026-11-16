#!/usr/bin/env python3
"""直接拖线改形状：按在线的左半段改前段、右半段改后段。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVE_TOUCH_V1"

EDITS = [('                let k = usize::from(ctx.data(|d| d.get_temp::<u8>(pick_id).unwrap_or(0))) * 2;\n                pts[k] = gx;\n                pts[k + 1] = gy;\n', '                // 手指按在哪一半就改哪一半（没有可见手柄也能做形状）\n                if gx < 0.5 {\n                    pts[0] = gx;\n                    pts[1] = gy;\n                } else {\n                    pts[2] = gx;\n                    pts[3] = gy;\n                }\n                let _ = pick_id;\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("curve already dragged by touch")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("dragging the line shapes the curve")


if __name__ == "__main__":
    main()
