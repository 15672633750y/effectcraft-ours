#!/usr/bin/env python3
"""多选方块按下后高亮（再按一次熄灭）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILE_ACTIVE_V1"

OLD = '        let hot = resp.hovered();\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, if hot { 40 } else { 18 }));'

NEW = '        let hot = resp.hovered();\n        // EFFECTCRAFT_OURS_TILE_ACTIVE_V1 — 生效中的开关（多选）亮起来\n        let active = *cmd == "ours.multiSelect"\n            && ui.ctx().data(|d| d.get_temp::<bool>(egui::Id::new("ours-multi-mode")).unwrap_or(false));\n        let fill = if active { 70 } else if hot { 40 } else { 18 };\n        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(90, 220, 200, fill));'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tile active state already drawn")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("active tile is highlighted")


if __name__ == "__main__":
    main()
