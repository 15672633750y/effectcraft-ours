#!/usr/bin/env python3
"""预设库窗口右上角加「×」，点它关闭（之前只能靠再点「预设」）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_CLOSE_BTN_V1"

OLD = 'p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "预设库", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));\n'

NEW = 'p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "预设库", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));\n    {\n        let btn = egui::Rect::from_min_size(egui::pos2(r.max.x - 34.0, r.min.y + 8.0), egui::vec2(24.0, 24.0));\n        p.rect_filled(btn, 6.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 30));\n        p.text(btn.center(), egui::Align2::CENTER_CENTER, "×", Tokens::ui(13.0), egui::Color32::from_rgb(240, 242, 246));\n        if ui.interact(btn, egui::Id::new("ours-preset-close"), egui::Sense::click()).clicked() {\n            ui.ctx().data_mut(|d| d.insert_temp(open_id, false));\n        }\n    }\n'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset window already has a close button")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset window got a close button")


if __name__ == "__main__":
    main()
