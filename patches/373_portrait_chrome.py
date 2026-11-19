#!/usr/bin/env python3
"""竖屏布局的精简顶栏：隐藏桌面式菜单栏、工具栏压到 34px。

手机剪辑软件没有"文件 编辑 合成 图层 …"那一长排菜单；留着它，切到 CapCut/剪映也还像桌面软件。
所以竖屏布局下这一排不画，工具栏也矮一点，配合底部大图标工具条形成竖屏形态。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PORTRAIT_CHROME_V1"

OLD = '''        let mut top = full.min.y;
        if self.ui.show_menu_bar {
            let mb = egui::Rect::from_min_size(full.min, egui::vec2(full.width(), 24.0));
            let mut child = ui.new_child(egui::UiBuilder::new().max_rect(mb));
            child.painter().rect_filled(mb, 0.0, t.header_bg);
            menus::menu_bar(self, &mut child);
            top = mb.max.y;
        }
        let header_h = 40.0;'''

NEW = '''        let mut top = full.min.y;
        // EFFECTCRAFT_OURS_PORTRAIT_CHROME_V1 — 竖屏布局没有桌面菜单栏，工具栏也更矮
        let ours_portrait = matches!(
            self.ui.workspace.as_str(),
            "capcut" | "blurrr" | "kuaishou" | "jianying"
        );
        if self.ui.show_menu_bar && !ours_portrait {
            let mb = egui::Rect::from_min_size(full.min, egui::vec2(full.width(), 24.0));
            let mut child = ui.new_child(egui::UiBuilder::new().max_rect(mb));
            child.painter().rect_filled(mb, 0.0, t.header_bg);
            menus::menu_bar(self, &mut child);
            top = mb.max.y;
        }
        let header_h = if ours_portrait { 34.0 } else { 40.0 };'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("portrait chrome already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("portrait layouts hide the desktop menu bar and slim the toolbar")


if __name__ == "__main__":
    main()
