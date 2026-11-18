#!/usr/bin/env python3
"""快捷面板加「全选」(Ctrl+A)：点一下选中当前合成里的全部图层。

排在 276（多选）之后，因为它的锚点就是 tiles 数组的当前结尾。
再加一项后 tiles 是 10 项 → 4 行，面板高度 280 → 320。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_ALL_TILE_V1"

TILES_OLD = '''        ("多选", "M", "ours.multiSelect", serde_json::json!({})),
    ];'''
TILES_NEW = '''        ("多选", "M", "ours.multiSelect", serde_json::json!({})),
        ("全选", "Ctrl+A", "edit.selectAll", serde_json::json!({})),
    ];'''

SIZE_OLD = '    let size = egui::vec2(196.0, 280.0);'
SIZE_NEW = '    let size = egui::vec2(196.0, 320.0);'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("select-all tile already present")
        return
    for old, new in ((TILES_OLD, TILES_NEW), (SIZE_OLD, SIZE_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("全选 tile added (Ctrl+A)")


if __name__ == "__main__":
    main()
