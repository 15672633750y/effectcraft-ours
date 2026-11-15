#!/usr/bin/env python3
"""The viewer no longer draws its own comp-chip row at all.

That row is drawn inside the *panel body* (`panels/viewer.rs`), 24 px tall, one chip per open comp
in the viewer — the rounded “合成 1” chip under the tab strip. Switching compositions is done with
the tab strip above it (which drags and switches panels too), so the chip row is removed outright:
it cost 24 px of canvas and could not be dragged.

The tab strip above it (`■ 合成 1  图层  ☰`) is drawn by the docking library and is **not touched
here**.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_COMP_CHIP_MULTI_V1"

OLD = '''    let nav_h = if super::precomp::has_flow(app) { 0.0 } else { 24.0 };
'''
NEW = '''    // EFFECTCRAFT_OURS_COMP_CHIP_MULTI_V1 — 不画这一行 chip：
    // 切合成用上面的标签条（能拖、能切面板），这行只是白占 24px。全部隐藏。
    let nav_h = 0.0f32;
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
