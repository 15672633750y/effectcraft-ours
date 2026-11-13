#!/usr/bin/env python3
"""Columns the composition never uses are dropped up front, so the remaining ones move left."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DROP_COLUMNS_V1"
ANCHOR = "    let vis = Vis::of(&app.ui.timeline);\n"
CODE = '''    // " + MARKER + "
    // Only the columns this composition can actually use take space: the rest move away.
    let mut vis = Vis::of(&app.ui.timeline);
    if !comp.layers.iter().any(|l| l.parent.is_some()) {
        vis.parent = false;
    }
    if comp.layers.iter().all(|l| l.blend_mode.label() == "Normal" && !l.preserve_transparency) {
        vis.modes = false;
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("unused columns already dropped")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, CODE, 1), encoding="utf-8")
    print("parent and blend columns drop when unused")


if __name__ == "__main__":
    main()
