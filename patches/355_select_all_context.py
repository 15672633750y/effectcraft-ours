#!/usr/bin/env python3
"""「全选」按焦点面板分派，像 AE 一样。

- 焦点在「效果控件」→ ours.selectAllEffects（选中该图层上所有效果）
- 其它（时间线/项目等）→ edit.selectAll（全选图层）

`app.ui.focused` 由 dock_ui 每帧维护，所以这里读到的是`当前真正在操作的面板`。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_ALL_CTX_V1"

ANCHOR = '''    // EFFECTCRAFT_OURS_PRESET_SAVE_DIALOG_V1 - save preset opens a naming dialog (no SAF).
'''

INSERT = '''    // EFFECTCRAFT_OURS_SELECT_ALL_CTX_V1 - 全选跟着焦点面板走（效果控件选效果，其余选图层）
    if id == "ours.selectAllCtx" {
        let target = if app.ui.focused == crate::PanelKind::EffectControls {
            "ours.selectAllEffects"
        } else {
            "edit.selectAll"
        };
        return invoke(app, ctx, target, json!({}));
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/menus/invoke.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("context select-all already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, INSERT + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("ours.selectAllCtx dispatches on app.ui.focused")


if __name__ == "__main__":
    main()
