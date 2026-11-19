#!/usr/bin/env python3
"""竖屏布局加「设置」入口：手机上原本根本进不去设置。

设置面板是 `Dialog::Settings`，只能从桌面菜单栏（文件/编辑 → 设置）打开；
竖屏品牌布局把菜单栏隐藏了，于是手机上完全没有入口。

现在自绘顶栏右侧多一格 ⚙：点它 `app.dialog = Some(crate::Dialog::Settings)`。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SETTINGS_BUTTON_V1"

OLD = '''    let cells: [(&str, &str, bool); 4] = [
        ("undo", "\\u{27f2}", undo_ready),
        ("redo", "\\u{27f3}", redo_ready),
        ("play", if playing { "\\u{23f8}" } else { "\\u{25b6}" }, true),
        ("full", "\\u{26f6}", true),
    ];'''

NEW = '''    // EFFECTCRAFT_OURS_SETTINGS_BUTTON_V1 — 手机上没有菜单栏，设置必须有个入口
    let cells: [(&str, &str, bool); 5] = [
        ("undo", "\\u{27f2}", undo_ready),
        ("redo", "\\u{27f3}", redo_ready),
        ("play", if playing { "\\u{23f8}" } else { "\\u{25b6}" }, true),
        ("full", "\\u{26f6}", true),
        ("settings", "\\u{2699}", true),
    ];'''

HANDLE_OLD = '''                _ => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }'''

HANDLE_NEW = '''                "full" => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {
                    // 设置（手机上是唯一入口）
                    app.dialog = Some(crate::Dialog::Settings);
                }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("settings button already present")
        return
    for name, old, new in (("cells", OLD, NEW), ("handle", HANDLE_OLD, HANDLE_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("portrait header gained a settings button")


if __name__ == "__main__":
    main()
