#!/usr/bin/env python3
"""「布局」按钮改成 Middle 层的独立 Area：被浮层盖住、贴预览面板右下角。

- 337 已经把原来那处 catch_unwind 调用去掉（只剩 curves_editor）。
- 这里在 frame.rs 末尾用 Order::Middle 的 Area 重画，并保留同样的 panic 保护。
- 入口优先用 Area 给的矩形，按钮落到右下角。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1"

FRAME_ANCHOR = "        crate::account_ui::panel(self, ui, full);\n"

FRAME_INSERT = """        crate::account_ui::panel(self, ui, full);
        // EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1 — 「布局」放在 Middle 层、贴预览面板右下角：
        // Foreground 的预设库/导入/云端面板会盖住它（以前它最后绘制，永远最上层）。
        // 先保证「不消失」：用屏幕右侧固定锚点，不依赖 dock_rects（那条路取不到就不画）。
        // 预览面板右下角是下一轮的优化项。
        let screen = ui.ctx().content_rect();
        {
            let pos = egui::pos2(screen.max.x - 70.0, screen.min.y + 220.0);
            egui::Area::new(egui::Id::unique("ours-layout-btn"))
                .order(egui::Order::Middle)
                .fixed_pos(pos)
                .show(ui.ctx(), |ui| {
                    ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-layout-area-rect"), ui.max_rect()));
                    let crashed = ui
                        .data(|d| d.get_temp::<bool>(egui::Id::new("ours-layout-crashed")).unwrap_or(false));
                    if crashed {
                        return;
                    }
                    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| self.draw_layout_switcher(ui, full)))
                        .is_err()
                    {
                        ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-layout-crashed"), true));
                        ui.data_mut(|d| d.remove::<f64>(egui::Id::new("layout-open-at")));
                        self.ours_layout_error("switcher", "panic inside draw_layout_switcher");
                    }
                });
        }
"""

AREA_OLD = """let canvas: Option<egui::Rect> = ui.data(|d| d.get_temp(egui::Id::new("ours-canvas-rect")));"""
AREA_NEW = """// EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1 — Area 给的矩形优先（Middle 层那块），否则退回画布。
        let area_rect: Option<egui::Rect> = ui.data(|d| d.get_temp(egui::Id::new("ours-layout-area-rect")));
        let canvas: Option<egui::Rect> = area_rect.or_else(|| ui.data(|d| d.get_temp(egui::Id::new("ours-canvas-rect"))));"""

POS_OLD = """let r = Rect::from_min_size(egui::pos2(area.max.x - 8.0 - 44.0, area.min.y + 8.0), Vec2::new(44.0, 26.0));"""
POS_NEW = """// 右下角（原来是画布右上角）
        let r = Rect::from_min_size(egui::pos2(area.max.x - 8.0 - 44.0, area.max.y - 8.0 - 26.0), Vec2::new(44.0, 26.0));"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FRAME_ANCHOR) != 1:
            raise SystemExit(f"frame anchor: {src.count(FRAME_ANCHOR)}")
        src = src.replace(FRAME_ANCHOR, FRAME_INSERT, 1)
    for old, new in ((AREA_OLD, AREA_NEW), (POS_OLD, POS_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"entry anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    frame.write_text(src, encoding="utf-8")
    print("布局 button: Middle-layer Area at the preview panel's bottom-right")


if __name__ == "__main__":
    main()
