#!/usr/bin/env python3
"""快捷键面板用主题色（之前写死深色，浅色主题下会一块亮一块暗）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_THEME_V1"

EDITS = [('    let size = egui::vec2(196.0, 280.0);\n', '    let size = egui::vec2(196.0, 280.0);\n    let t = app.tokens;\n'), ('    p.rect_filled(r, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 130));\n', '    p.rect_filled(r, 14.0, t.panel_bg.gamma_multiply(0.92));\n'), ('    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));\n', '    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(13.0), t.text);\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panel already themed")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("shortcut panel follows the theme")


if __name__ == "__main__":
    main()
