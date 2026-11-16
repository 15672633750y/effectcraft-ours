#!/usr/bin/env python3
"""快捷键面板：可折叠成标题条、拖动只认标题条、面板不再穿透到画布。

The panel dragged from anywhere and every press went through to the canvas underneath. Now only the
title bar drags, the body swallows clicks, and a `-` button collapses the panel to just the bar (still
draggable).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_GRIP_V1"

EDITS = [('    let size = egui::vec2(196.0, 184.0);\n', '    let size = egui::vec2(196.0, 184.0);\n    // EFFECTCRAFT_OURS_PANEL_COLLAPSE_V1 — 折叠时只留标题条\n    let col_id = egui::Id::unique("ours-shortcut-collapsed");\n    let mut collapsed: bool = ui.ctx().data(|d| d.get_temp::<bool>(col_id).unwrap_or(false));\n    let size = if collapsed { egui::vec2(196.0, 40.0) } else { size };\n'), ('    let mut latched: bool = ui.ctx().data(|d| d.get_temp::<bool>(latch_id)).unwrap_or(false);\n    let (pressed, down, released, ppos) = ui.input(|i| {\n        (i.pointer.primary_pressed(), i.pointer.primary_down(), i.pointer.primary_released(), i.pointer.interact_pos())\n    });\n    if pressed && let Some(p) = ppos && title.contains(p) {\n        latched = true;\n    }\n    if latched && down {\n        let d = ui.input(|i| i.pointer.delta());\n        if d.length() > 0.0 {\n            off += d;\n            let nx = base.x + d.x;\n            let ny = base.y + d.y;\n            off.x = (nx - (full.center().x - size.x * 0.5)).clamp(full.min.x + 8.0 - (full.center().x - size.x * 0.5), full.max.x - size.x - 8.0 - (full.center().x - size.x * 0.5));\n            off.y = (ny - (full.max.y - 300.0)).clamp(full.min.y + 8.0 - (full.max.y - 300.0), full.max.y - size.y - 8.0 - (full.max.y - 300.0));\n        }\n    }\n    if released && latched {\n        latched = false;\n    }\n', '    // EFFECTCRAFT_OURS_PANEL_GRIP_V1 — 只有标题条能拖；面板本体吃掉点击，避免穿透到画布\n    let grip = ui.interact(title, egui::Id::new("ours-shortcut-grip"), egui::Sense::click_and_drag());\n    if grip.dragged() {\n        off += grip.drag_delta();\n    }\n    off.x = off.x.clamp(full.min.x + 8.0 - (full.center().x - size.x * 0.5), full.max.x - size.x - 8.0 - (full.center().x - size.x * 0.5));\n    off.y = off.y.clamp(full.min.y + 8.0 - (full.max.y - 300.0), full.max.y - size.y - 8.0 - (full.max.y - 300.0));\n    let _block = ui.interact(r, egui::Id::new("ours-shortcut-block"), egui::Sense::click());\n'), ('    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));\n', '    let cy = r.min.y + 20.0;\n    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));\n    {\n        let btn = egui::Rect::from_min_size(egui::pos2(r.min.x + 8.0, cy - 10.0), egui::vec2(22.0, 20.0));\n        p.rect_filled(btn, 6.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 26));\n        p.text(btn.center(), egui::Align2::CENTER_CENTER, if collapsed { "+" } else { "-" }, Tokens::ui(12.0), egui::Color32::from_rgb(235, 237, 242));\n        if ui.interact(btn, egui::Id::new("ours-shortcut-collapse"), egui::Sense::click()).clicked() {\n            collapsed = !collapsed;\n            ui.ctx().data_mut(|d| d.insert_temp(col_id, collapsed));\n        }\n    }\n    if collapsed {\n        return;\n    }\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panel grip/collapse already present")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("panel: title-bar drag, click blocking, collapse")


if __name__ == "__main__":
    main()
