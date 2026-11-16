#!/usr/bin/env python3
"""多选方块生效时改成白色 + 外发光（原来青绿偏暗）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILE_GLOW_V1"

OLD = '        let fill = if active { 70 } else if hot { 40 } else { 18 };\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(90, 220, 200, fill));'

NEW = '        let fill = if active { 235 } else if hot { 40 } else { 18 };\n        // EFFECTCRAFT_OURS_TILE_GLOW_V1 — 生效时白色高亮 + 一层外发光\n        if active {\n            p.rect_filled(tr.expand(2.0), 10.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 46));\n            p.rect_stroke(tr.expand(2.0), 10.0, egui::Stroke::new(1.5, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 120)), egui::StrokeKind::Inside);\n        }\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, fill));'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("active tile already glows white")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("active tile is white with a glow")


if __name__ == "__main__":
    main()
