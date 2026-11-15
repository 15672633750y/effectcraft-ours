#!/usr/bin/env python3
"""The viewer's comp-chip row only appears when there is more than one comp open.

That row is drawn inside the *panel body* (`panels/viewer.rs`), 24 px tall, one chip per open comp
in the viewer — the rounded “合成 1” chip under the tab strip. With a single comp it is a label
that cannot be dragged and does nothing, and it costs 24 px of canvas.

The tab strip above it (`■ 合成 1  图层  ☰`, which drags and switches panels) is drawn by the
docking library and is **not touched here**. Nothing else about the viewer changes: the row still
appears, exactly as before, once a second comp is opened in the viewer, where it is the switcher.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_COMP_CHIP_MULTI_V1"

OLD = '''    let nav_h = if super::precomp::has_flow(app) { 0.0 } else { 24.0 };
'''
NEW = '''    // EFFECTCRAFT_OURS_COMP_CHIP_MULTI_V1 — 只有一个合成时不画这条 chip 行：
    // 它拖不动、点了没用，还白占 24px；开第二个合成时照旧出现，用来切换。
    let nav_h = if super::precomp::has_flow(app) || app.session.state.open_comps.len() <= 1 {
        0.0
    } else {
        24.0
    };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/viewer.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("comp chip row already conditional")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("the comp chip row hides when only one comp is open")


if __name__ == "__main__":
    main()
