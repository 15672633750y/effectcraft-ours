#!/usr/bin/env python3
"""「快捷键」面板是全局视觉基准：所有浮层从这一个模块取值。

基准值（照 `203_shortcut_panel_draw.py` 的实测）：圆角 14、内边距 16、
行高 44、按钮高 40、标题 14px semibold、半透明底 rgba(12,12,14,130) + 1px 白 90 边。

新增 `crates/ui-egui/src/panel_style.rs` 并在 `lib.rs` 里 `pub mod panel_style;`，
其它补丁用 `crate::panel_style::...` 引用；改一处，全部浮层一起变。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANEL_STYLE_V1"

MODULE = r'''//! EFFECTCRAFT_OURS_PANEL_STYLE_V1 — 「快捷键」面板是全局视觉基准。
//!
//! 所有浮层（预设库 / 导入 / 云端工程 / 插件 / 我的资料）都从这里取尺寸与材质，
//! 不要再在各处写死圆角、背景、行高。基准值照 203_shortcut_panel_draw.py 的实测。

use egui::Color32;

/// 圆角（快捷键面板就是 14）。
pub const RADIUS: f32 = 14.0;
/// 内边距。
pub const PADDING: f32 = 16.0;
/// 列表行高。
pub const ROW_H: f32 = 44.0;
/// 行间距。
pub const ROW_GAP: f32 = 6.0;
/// 按钮高度。
pub const BUTTON_H: f32 = 40.0;
/// 标题字号。
pub const TITLE_SIZE: f32 = 14.0;

/// 半透明底板：和快捷键面板同一组数值。
pub fn bg() -> Color32 {
    Color32::from_rgba_unmultiplied(12, 12, 14, 130)
}

/// 1px 亮边。
pub fn border() -> Color32 {
    Color32::from_rgba_unmultiplied(255, 255, 255, 90)
}

/// 浮层的 `egui::Frame`：底板 + 圆角 + 内边距 + 亮边（保留窗口阴影）。
pub fn frame(style: &egui::Style) -> egui::Frame {
    egui::Frame::window(style)
        .fill(bg())
        .corner_radius(RADIUS)
        .inner_margin(egui::Margin::same(PADDING as i8))
        .stroke(egui::Stroke::new(1.0, border()))
}

/// 主题色的低不透明度叠加（hover / 选中 / 图标底）。
pub fn tint(color: Color32, alpha: u8) -> Color32 {
    Color32::from_rgba_unmultiplied(color.r(), color.g(), color.b(), alpha)
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    module = root / "crates/ui-egui/src/panel_style.rs"
    if not module.exists():
        module.write_text(MODULE, encoding="utf-8")
        print("panel_style.rs created")
    lib = root / "crates/ui-egui/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    if MARKER not in src:
        anchor = "pub mod frames;\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"lib anchor: {src.count(anchor)}")
        src = src.replace(anchor, anchor + "// EFFECTCRAFT_OURS_PANEL_STYLE_V1 — 浮层视觉基准（详见 panel_style.rs）\npub mod panel_style;\n", 1)
        lib.write_text(src, encoding="utf-8")
        print("lib.rs exports panel_style")


if __name__ == "__main__":
    main()
