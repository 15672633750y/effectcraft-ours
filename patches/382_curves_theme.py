#!/usr/bin/env python3
"""曲线编辑器面板也跟着主题走（亮色布局下不要一块黑底）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVES_THEME_V1"

OLD = '''    let p = ui.painter().with_clip_rect(full);
    p.rect_filled(r, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 240));
    p.rect_stroke(r, 14.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 90)), egui::StrokeKind::Inside);'''

NEW = '''    let p = ui.painter().with_clip_rect(full);
    // EFFECTCRAFT_OURS_CURVES_THEME_V1 — 跟着主题：亮色布局下用浅色卡片
    let light_theme = app.tokens.kind.is_light();
    let (card, edge) = if light_theme {
        (
            egui::Color32::from_rgba_unmultiplied(255, 255, 255, 242),
            egui::Color32::from_rgba_unmultiplied(0, 0, 0, 45),
        )
    } else {
        (
            egui::Color32::from_rgba_unmultiplied(12, 12, 14, 240),
            egui::Color32::from_rgba_unmultiplied(255, 255, 255, 90),
        )
    };
    p.rect_filled(r, 14.0, card);
    p.rect_stroke(r, 14.0, egui::Stroke::new(1.0, edge), egui::StrokeKind::Inside);'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("curves theming already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("curves editor follows the theme")


if __name__ == "__main__":
    main()
