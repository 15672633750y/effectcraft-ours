#!/usr/bin/env python3
"""把「颜色增强」默认值定在 1.08：按用户真机导出（Frame3）与 AE 的差值反推。

On the real device the render is 5–9% less saturated than the AE frame in the dark and bright bands;
the measured gaps are 0.162→0.176 (+8.6%), 0.291→0.313 (+7.6%), so the default is 1.08 and the extra
above mid grey stays at 0.10.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CHROMA_DEFAULT_V1"

OLD = 'p("chroma", "颜色增强", num(1.05), slider(0.5, 2.0, 0.8, 1.4, 3)),'
NEW = 'p("chroma", "颜色增强", num(1.08), slider(0.5, 2.0, 0.8, 1.4, 3)),'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("chroma default already 1.08")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("chroma default raised to 1.08")


if __name__ == "__main__":
    main()
