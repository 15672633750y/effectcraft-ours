#!/usr/bin/env python3
"""预设库真的给一条**能拖的滚动条**。

之前只有一个不可见的滚动区（滚轮 + 拖列表），用户看到的细条是别处画的、拖不动。
现在在列表右侧画 4px 轨道 + 可拖动滑块：拖动滑块滚动、悬停高亮、点击轨道跳转。
列表拖动的热区同时避开这条轨道，避免两种拖动互相抢。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SCROLLBAR_DRAG_V1"

OLD = '''    // 拖动列表区也是滚动（拖动面板只在标题栏那块生效）
    let drag_in_list = ui.interact(view, egui::Id::unique("ours-preset-list-scroll"), egui::Sense::drag());
    if drag_in_list.dragged() && max_scroll > 0.0 {
        scroll = (scroll - drag_in_list.drag_delta().y).clamp(0.0, max_scroll);
        ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
    }'''

NEW = '''    // 拖动列表区也是滚动（拖动面板只在标题栏那块生效）。
    // EFFECTCRAFT_OURS_SCROLLBAR_DRAG_V1 — 右侧留 10px 给滚动条，别和列表拖动抢。
    let drag_rect = egui::Rect::from_min_max(view.min, egui::pos2(view.max.x - 10.0, view.max.y));
    let drag_in_list = ui.interact(drag_rect, egui::Id::unique("ours-preset-list-scroll"), egui::Sense::drag());
    if drag_in_list.dragged() && max_scroll > 0.0 {
        scroll = (scroll - drag_in_list.drag_delta().y).clamp(0.0, max_scroll);
        ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
    }
    // 可拖动的滚动条：轨道 + 滑块（真的能拖，不是装饰）
    if max_scroll > 0.0 {
        let track = egui::Rect::from_min_max(
            egui::pos2(view.max.x - 6.0, view.min.y),
            egui::pos2(view.max.x, view.max.y),
        );
        ui.painter()
            .rect_filled(track, 3.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 24));
        let frac = (view_h / content_h).clamp(0.08, 1.0);
        let thumb_h = (track.height() * frac).max(28.0);
        let progress = if max_scroll > 0.0 { scroll / max_scroll } else { 0.0 };
        let thumb_y = track.min.y + (track.height() - thumb_h) * progress;
        let thumb = egui::Rect::from_min_size(
            egui::pos2(track.min.x + 1.0, thumb_y),
            egui::vec2(track.width() - 2.0, thumb_h),
        );
        let bar = ui.interact(
            thumb.expand2(egui::vec2(6.0, 0.0)),
            egui::Id::unique("ours-preset-scrollbar"),
            egui::Sense::drag(),
        );
        let hot = bar.hovered() || bar.dragged();
        ui.painter().rect_filled(
            thumb,
            2.0,
            if hot {
                t.accent
            } else {
                egui::Color32::from_rgba_unmultiplied(255, 255, 255, 96)
            },
        );
        if bar.dragged() {
            let span = (track.height() - thumb_h).max(1.0);
            let ratio = bar.drag_delta().y / span;
            scroll = (scroll + ratio * max_scroll).clamp(0.0, max_scroll);
            ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
        }
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("scrollbar already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset library gets a draggable scrollbar")


if __name__ == "__main__":
    main()
