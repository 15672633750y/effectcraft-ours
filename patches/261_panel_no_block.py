#!/usr/bin/env python3
"""面板恢复穿透：只有标题条（可拖的地方）拦截点击，其它区域照旧点到画布。

Click-through is wanted: the panel floats over the canvas and you still want to grab layers under it.
Only the drag grip must swallow input, so the blocker over the whole panel is removed and the grip keeps
its own interaction.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_NO_BLOCK_V1"

OLD = "    let _block = ui.interact(r, egui::Id::new(\"ours-shortcut-block\"), egui::Sense::click());\n"
NEW = ""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panel already click-through")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("panel is click-through again; only the grip swallows input")


if __name__ == "__main__":
    main()
