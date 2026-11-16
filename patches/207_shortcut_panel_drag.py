#!/usr/bin/env python3
"""「快捷」面板可以拖动：按住标题条拖到任意位置，位置记住。

The panel was a painted rectangle with no input. It now reads the pointer itself (the same latch
trick the ball needed): press on its title strip, move, release — the offset is kept in egui's temp
data so the panel stays where it was put.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_DRAG_V1"

OLD = '''    let size = egui::vec2(196.0, 132.0);
    let r = egui::Rect::from_min_size(egui::pos2(full.center().x - size.x * 0.5, full.max.y - 300.0), size);
'''
NEW = '''    let size = egui::vec2(196.0, 132.0);
    // EFFECTCRAFT_OURS_PANEL_DRAG_V1 — 可拖动：按住标题条拖，位置记住
    let off_id = egui::Id::unique("ours-shortcut-panel-pos");
    let latch_id = egui::Id::unique("ours-shortcut-panel-latch");
    let mut off: egui::Vec2 = ui.ctx().data(|d| d.get_temp::<egui::Vec2>(off_id)).unwrap_or(egui::vec2(0.0, 0.0));
    let base = egui::pos2(full.center().x - size.x * 0.5, full.max.y - 300.0) + off;
    let r = egui::Rect::from_min_size(base, size);
    let title = egui::Rect::from_min_size(r.min, egui::vec2(size.x, 34.0));
    let mut latched: bool = ui.ctx().data(|d| d.get_temp::<bool>(latch_id)).unwrap_or(false);
    let (pressed, down, released, ppos) = ui.input(|i| {
        (i.pointer.primary_pressed(), i.pointer.primary_down(), i.pointer.primary_released(), i.pointer.interact_pos())
    });
    if pressed && let Some(p) = ppos && title.contains(p) {
        latched = true;
    }
    if latched && down {
        let d = ui.input(|i| i.pointer.delta());
        if d.length() > 0.0 {
            off += d;
            let nx = base.x + d.x;
            let ny = base.y + d.y;
            off.x = (nx - (full.center().x - size.x * 0.5)).clamp(full.min.x + 8.0 - (full.center().x - size.x * 0.5), full.max.x - size.x - 8.0 - (full.center().x - size.x * 0.5));
            off.y = (ny - (full.max.y - 300.0)).clamp(full.min.y + 8.0 - (full.max.y - 300.0), full.max.y - size.y - 8.0 - (full.max.y - 300.0));
        }
    }
    if released && latched {
        latched = false;
    }
    ui.ctx().data_mut(|d| {
        d.insert_temp(off_id, off);
        d.insert_temp(latch_id, latched);
    });
    let r = egui::Rect::from_min_size(egui::pos2(full.center().x - size.x * 0.5, full.max.y - 300.0) + off, size);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panel already draggable")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("panel can be dragged by its title")


if __name__ == "__main__":
    main()
