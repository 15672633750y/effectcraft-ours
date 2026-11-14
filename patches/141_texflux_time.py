#!/usr/bin/env python3
"""Declare S_TextureFlux as time dependent.

Its texture flows with layer time (the `speed` parameter), so the render cache has to key on the
time: without the declaration the effect would be cached from its first frame and never animate.
The effects crate's own test (`time_dependence_is_declared`) caught it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TEXFLUX_TIME_V1"

ANCHOR = 'pub const TIME_DEPENDENT: &[&str] = &[\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/lib.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("S_TextureFlux already declared time dependent")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + '    // ' + MARKER + '\n    "S_TextureFlux",\n', 1)
    path.write_text(src, encoding="utf-8")
    print("TIME_DEPENDENT lists S_TextureFlux")


if __name__ == "__main__":
    main()
