#!/usr/bin/env python3
"""工具条背景跟着主题走。

1015/1016 让 capcut/快影/AM 切到亮色以后，我画的三条工具条（底部/右侧/顶部）还是硬编码的深色
`rgba(12,12,14,2xx)`，在白底界面上就是一块黑疙瘩。改成用 tokens 的面板色 + 边框色。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CHROME_THEME_V1"

OLD_A = '''                    ui.painter().rect_filled(
                        bar,
                        14.0,
                        egui::Color32::from_rgba_unmultiplied(12, 12, 14, 205),
                    );'''
NEW_A = '''                    ui.painter().rect_filled(bar, 14.0, self.tokens.panel_bg);
                    ui.painter().rect_stroke(
                        bar,
                        14.0,
                        egui::Stroke::new(1.0, self.tokens.separator),
                        egui::StrokeKind::Inside,
                    );'''

OLD_B = '''                    ui.painter().rect_filled(
                        rail,
                        16.0,
                        egui::Color32::from_rgba_unmultiplied(12, 12, 14, 205),
                    );'''
NEW_B = '''                    ui.painter().rect_filled(rail, 16.0, self.tokens.panel_bg);
                    ui.painter().rect_stroke(
                        rail,
                        16.0,
                        egui::Stroke::new(1.0, self.tokens.separator),
                        egui::StrokeKind::Inside,
                    );'''

OLD_C = '''                    ui.painter().rect_filled(
                        strip,
                        12.0,
                        egui::Color32::from_rgba_unmultiplied(12, 12, 14, 190),
                    );'''
NEW_C = '''                    ui.painter().rect_filled(strip, 12.0, self.tokens.panel_bg);
                    ui.painter().rect_stroke(
                        strip,
                        12.0,
                        egui::Stroke::new(1.0, self.tokens.separator),
                        egui::StrokeKind::Inside,
                    );'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("chrome theming already present")
        return
    for name, old, new in (("bar", OLD_A, NEW_A), ("rail", OLD_B, NEW_B), ("strip", OLD_C, NEW_C)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    frame.write_text(src, encoding="utf-8")
    print("tool bars use panel_bg/separator instead of hard-coded dark")


if __name__ == "__main__":
    main()
