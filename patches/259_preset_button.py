#!/usr/bin/env python3
"""在快捷键面板的标题条右侧加「预设」按钮，点开预设库窗口。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_BUTTON_V1"

OLD = """    // EFFECTCRAFT_OURS_SHORTCUT_TILES_V1 — 功能方块：上面大字，下面键位
"""
NEW = """    // EFFECTCRAFT_OURS_PRESET_BUTTON_V1 — 标题条右侧「预设」按钮
    {
        let btn = egui::Rect::from_min_size(egui::pos2(r.max.x - 56.0, r.min.y + 8.0), egui::vec2(48.0, 20.0));
        p.rect_filled(btn, 6.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 26));
        p.text(btn.center(), egui::Align2::CENTER_CENTER, "预设", Tokens::ui(11.0), egui::Color32::from_rgb(235, 237, 242));
        let resp = ui.interact(btn, egui::Id::new("ours-preset-btn"), egui::Sense::click());
        if resp.clicked() {
            let id = egui::Id::unique("ours-preset-open");
            let cur: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
            ui.ctx().data_mut(|d| d.insert_temp(id, !cur));
        }
    }
    // EFFECTCRAFT_OURS_SHORTCUT_TILES_V1 — 功能方块：上面大字，下面键位
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset button already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset button added to the shortcut panel")


if __name__ == "__main__":
    main()
