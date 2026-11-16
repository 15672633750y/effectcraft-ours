#!/usr/bin/env python3
"""有约束模型自己就带降饱和，所以「颜色增强」默认回到 1.0（1.08 会让蓝色偏）。

Measured on the training pair with the constrained model: chroma 1.0 gives 4.03/3.44/4.11, 1.08 gives
3.94/3.46/4.49 — the extra boost only helps red slightly and costs blue, so the default returns to 1.0.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CHROMA_ONE_V1"

OLD = 'p("chroma", "颜色增强", num(1.08), slider(0.5, 2.0, 0.8, 1.4, 3)),'
NEW = 'p("chroma", "颜色增强", num(1.0), slider(0.5, 2.0, 0.8, 1.4, 3)),'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("chroma default already 1.0")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("chroma default back to 1.0")


if __name__ == "__main__":
    main()
