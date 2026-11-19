#!/usr/bin/env python3
"""浮层材质跟着主题走：亮色布局下不再是一块半透明黑卡。

`panel_style::bg()` 是给深色主题定的 `rgba(12,12,14,130)`；1015/1016 把 capcut/快影/AM 切成亮色后，
预设库、导入面板、快捷键面板这些浮层都变成了白底上的黑卡。这里加一个带主题的版本，
并在三处调用点换成它。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_THEME_V1"

STYLE_OLD = '''/// 浮层的 `egui::Frame`：底板 + 圆角 + 内边距 + 亮边（保留窗口阴影）。
pub fn frame(style: &egui::Style) -> egui::Frame {'''

STYLE_NEW = '''/// 亮色主题下的浮层底板：浅色卡片 + 深色细边，避免白底上出现半透明黑块。
pub fn bg_light() -> Color32 {
    Color32::from_rgba_unmultiplied(255, 255, 255, 236)
}

/// 亮色主题下的边框。
pub fn border_light() -> Color32 {
    Color32::from_rgba_unmultiplied(0, 0, 0, 40)
}

/// 跟着主题走的浮层：深色用原来的半透明黑，亮色用浅色卡片。
pub fn frame_themed(style: &egui::Style, light: bool) -> egui::Frame {
    if light {
        egui::Frame::window(style)
            .fill(bg_light())
            .corner_radius(RADIUS)
            .inner_margin(egui::Margin::same(PADDING as i8))
            .stroke(egui::Stroke::new(1.0, border_light()))
    } else {
        frame(style)
    }
}

/// 浮层的 `egui::Frame`：底板 + 圆角 + 内边距 + 亮边（保留窗口阴影）。
pub fn frame(style: &egui::Style) -> egui::Frame {'''

CALL_OLD_A = "    let frame = crate::panel_style::frame(&style);"
CALL_NEW_A = "    let frame = crate::panel_style::frame_themed(&style, t.kind.is_light());"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    style = root / "crates/ui-egui/src/panel_style.rs"
    src = style.read_text(encoding="utf-8")
    if MARKER in src:
        print("panels already themed")
        return
    if src.count(STYLE_OLD) != 1:
        raise SystemExit(f"style anchor: {src.count(STYLE_OLD)}")
    style.write_text(src.replace(STYLE_OLD, STYLE_NEW, 1), encoding="utf-8")

    changed = 0
    for rel in ("crates/ui-egui/src/header.rs", "crates/ui-egui/src/panels/project.rs"):
        p = root / rel
        s = p.read_text(encoding="utf-8")
        n = s.count(CALL_OLD_A)
        if n:
            p.write_text(s.replace(CALL_OLD_A, CALL_NEW_A), encoding="utf-8")
            changed += n
    print(f"panel_style: themed frame added, {changed} call sites switched")


if __name__ == "__main__":
    main()
