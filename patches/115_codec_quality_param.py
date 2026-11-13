#!/usr/bin/env python3
"""`codecQuality` on its own key: the 1–100 constant-quality slider, next to `quality`.

`quality` already carries two meanings in one command: the string "best"/"draft" sets the Render
Settings (which is what decides full-resolution vs draft), and a number sets the Output Module's
JPEG/WebM quality. A dialog that wants both — Best render quality *and* a CRF level — cannot use
one key for two values, so the codec's 1–100 quality gets its own name.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CODEC_QUALITY_PARAM_V1"

OLD = """    if let Some(q) = f_p(p, "quality") {
        om.codec.quality = q.clamp(1.0, 100.0) as u8;
    }
"""
NEW = """    if let Some(q) = f_p(p, "quality") {
        om.codec.quality = q.clamp(1.0, 100.0) as u8;
    }
    if let Some(q) = f_p(p, "codecQuality") {
        // EFFECTCRAFT_OURS_CODEC_QUALITY_PARAM_V1
        // `quality` is the render quality when it is a string and the JPEG/WebM quality when it
        // is a number; the codec's own 1-100 constant-quality setting has its own key so a job
        // can ask for Best rendering and a CRF level at the same time.
        om.codec.quality = q.clamp(1.0, 100.0) as u8;
        any = true;
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("codecQuality param already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"codec quality anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("renderQueue.add accepts codecQuality 1-100 (constant-quality slider)")


if __name__ == "__main__":
    main()
