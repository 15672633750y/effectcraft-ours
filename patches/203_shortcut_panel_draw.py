#!/usr/bin/env python3
"""「快捷」面板：透明的轻量小面板（先空着，只显示标题），由工具栏按钮开关。

Drawn at the end of the frame like the toast, in the same low-alpha glass style, and it takes no
input, so it never blocks the timeline behind it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_PANEL_V1"

CALL_OLD = "        shortcut_ball(ui, full);\n"
CALL_NEW = CALL_OLD + "        shortcut_panel(ui, full);\n"

FUNC = r'''

/// EFFECTCRAFT_OURS_SHORTCUT_PANEL_V1 — 空面板：透明、小巧、不挡点击。
fn shortcut_panel(ui: &mut egui::Ui, full: egui::Rect) {
    let id = egui::Id::unique("ours-shortcut-open");
    let open: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
    if !open {
        return;
    }
    let size = egui::vec2(196.0, 132.0);
    let r = egui::Rect::from_min_size(egui::pos2(full.center().x - size.x * 0.5, full.max.y - 300.0), size);
    let p = ui.painter().with_clip_rect(full);
    p.rect_filled(r, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 130));
    p.rect_stroke(r, 14.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 90)), egui::StrokeKind::Inside);
    p.text(r.center_top() + egui::vec2(0.0, 26.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(14.0), egui::Color32::from_rgb(242, 243, 247));
    p.text(r.center() + egui::vec2(0.0, 10.0), egui::Align2::CENTER_CENTER, "（功能加入中）", Tokens::ui(12.0), egui::Color32::from_gray(180));
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("shortcut panel already installed")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src += FUNC
    path.write_text(src, encoding="utf-8")
    print("shortcut panel draws when the button is on")


if __name__ == "__main__":
    main()
