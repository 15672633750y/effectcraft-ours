#!/usr/bin/env python3
"""多选方块改成「键盘灯」：底色不变、四周发光、文字正常显示（之前白填充把字盖住了）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILE_LED_V1"

OLD = '        let fill = if active { 235 } else if hot { 40 } else { 18 };\n        // EFFECTCRAFT_OURS_TILE_GLOW_V1 — 生效时白色高亮 + 一层外发光\n        if active {\n            p.rect_filled(tr.expand(2.0), 10.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 46));\n            p.rect_stroke(tr.expand(2.0), 10.0, egui::Stroke::new(1.5, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 120)), egui::StrokeKind::Inside);\n        }\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, fill));'

NEW = '        let fill = if hot { 40 } else { 18 };\n        // EFFECTCRAFT_OURS_TILE_LED_V1 — 像键盘灯：底色不变，四周发光，文字照原样\n        if active {\n            for (i, a) in [(3.0f32, 26u8), (2.0, 46), (1.0, 78)] {\n                p.rect_stroke(tr.expand(i), 9.0, egui::Stroke::new(1.5, egui::Color32::from_rgba_unmultiplied(255, 255, 255, a)), egui::StrokeKind::Inside);\n            }\n            p.rect_stroke(tr, 8.0, egui::Stroke::new(1.6, egui::Color32::from_rgb(255, 255, 255)), egui::StrokeKind::Inside);\n        }\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, fill));'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tile LED already drawn")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("active tile is an LED ring now")


if __name__ == "__main__":
    main()
