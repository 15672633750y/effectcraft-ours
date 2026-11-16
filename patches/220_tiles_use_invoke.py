#!/usr/bin/env python3
"""面板方块改走 `menus::invoke`（与菜单同一入口），不在绘制途中直接执行命令。

Calling `session.execute` while the frame is being drawn can mutate the document under the panels
that are still painting — the usual cause of an occasional crash. Every menu entry goes through
`menus::invoke`, which defers to the same safe path; the tiles do the same now.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILES_VIA_INVOKE_V1"

OLD = '''    if let Some(cmd) = run {
        match app.session.execute(cmd, payload) {
            Ok(_) => {}
            Err(e) => {
                app.ui.status = format!("{e}");
            }
        }
    }
'''
NEW = '''    if let Some(cmd) = run {
        // EFFECTCRAFT_OURS_TILES_VIA_INVOKE_V1 — 走菜单同一个入口，避免在绘制途中改文档
        match crate::menus::invoke(app, ui.ctx(), cmd, payload) {
            Ok(_) => {}
            Err(e) => {
                app.ui.status = format!("{e}");
            }
        }
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tiles already use invoke")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("tiles run through menus::invoke")


if __name__ == "__main__":
    main()
