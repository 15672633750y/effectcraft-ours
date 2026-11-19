#!/usr/bin/env python3
"""底部工具条加第 6 个按钮：**导出**（真的打开导出对话框）。

参考图里各家底部/右上都有"导出/匯出"，我们本来就有导出对话框（ours-export-open），
只是一直挂在顶栏。现在竖屏布局的底部工具条直接给一个。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TRAY_EXPORT_V1"

ITEMS_OLD = '''                    let items: [(&str, &str, u8); 5] = [
                        ("\\u{ff0b}", "导入", 0),
                        ("T", "文字", 1),
                        ("\\u{25c7}", "形状", 2),
                        ("\\u{2605}", "预设", 3),
                        ("\\u{25b6}", "播放", 4),
                    ];'''

ITEMS_NEW = '''                    // EFFECTCRAFT_OURS_TRAY_EXPORT_V1 — 第 6 个：导出（真的打开导出对话框）
                    let items: [(&str, &str, u8); 6] = [
                        ("\\u{ff0b}", "导入", 0),
                        ("T", "文字", 1),
                        ("\\u{25c7}", "形状", 2),
                        ("\\u{2605}", "预设", 3),
                        ("\\u{25b6}", "播放", 4),
                        ("\\u{2191}", "导出", 8),
                    ];'''

MATCH_OLD = '''                Some(7) => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''

MATCH_NEW = '''                Some(7) => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                Some(8) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tray export already present")
        return
    for name, old, new in (("items", ITEMS_OLD, ITEMS_NEW), ("match", MATCH_OLD, MATCH_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("bottom tray gained a real 导出 button")


if __name__ == "__main__":
    main()
