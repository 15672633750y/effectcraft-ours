#!/usr/bin/env python3
"""文件 ▸ 导入 also lists 导入插件与工程…, where people look for it.

The window itself existed behind the Project panel's ⋯ menu; this adds a frontend command under the
File ▸ Import submenu and the one line in the UI that opens the window, so it is reachable from the
menu bar too.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_IMPORT_MENU_V1"

FE_ANCHOR = '        fe!("app.find", "Find", ["File"], Some("Cmd+F"), "{query?: string, status?: all|available|missing}", always),\n'
FE_NEW = FE_ANCHOR + '        // EFFECTCRAFT_OURS_IMPORT_MENU_V1 — 文件 ▸ 导入 里也放一个入口\n        fe!("ours.importWindow", "导入插件与工程…", ["File", "Import"], None, "{}", always),\n'

UI_ANCHOR = '        "mediaBrowser.copySourcePath" => {\n'
UI_NEW = '''        // EFFECTCRAFT_OURS_IMPORT_MENU_V1 — 打开导入窗口（插件与工程）
        "ours.importWindow" => {
            ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-import-open"), true));
            json!({"opened": true})
        }
''' + UI_ANCHOR


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    eng = root / "crates/engine/src/cmd/frontend.rs"
    src = eng.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FE_ANCHOR) != 1:
            raise SystemExit(f"command anchor: {src.count(FE_ANCHOR)}")
        eng.write_text(src.replace(FE_ANCHOR, FE_NEW, 1), encoding="utf-8")
        print("frontend command registered")
    ui = root / "crates/ui-egui/src/menus/frontend.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER in src:
        print("import menu entry already installed")
        return
    if src.count(UI_ANCHOR) != 1:
        raise SystemExit(f"ui anchor: {src.count(UI_ANCHOR)}")
    ui.write_text(src.replace(UI_ANCHOR, UI_NEW, 1), encoding="utf-8")
    print("文件 ▸ 导入 now opens the import window")


if __name__ == "__main__":
    main()
