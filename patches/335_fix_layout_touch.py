#!/usr/bin/env python3
"""三个实测问题的修复（877 之后的 878 批）。

1) 「布局」入口画到窗口最右上角（顶栏外面）→ 改成画进预览区内部，偏移 8px。
   frame.rs 里那套只在展开时画遮罩/卡片；入口由 `panels/viewer.rs::phase_press` 用 `v.area` 画。

2) 点击布局不重排：移动端没有这些 dock 工作区 → `dock::ours_layout()` 直接返回四套布局树
   （经典 / 简易 / 专业 / 极简），点击时直接换 `app.ui.dock`。极简只有预览，项目面板和时间线一定消失。

（原先的第 3 项「PNG 拖动贴边」已由用户取消，不再改 `phase_drag`。）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FIX_LAYOUT_TOUCH_V1"

DOCK_ANCHOR = "#[cfg(test)]\n"
DOCK_INSERT = '''/// EFFECTCRAFT_OURS_LAYOUT_REAL_V1 — 「布局」切换器用的四套布局（不依赖 dock 的命名工作区，
/// 所以手机上切了一定重排）：经典 = 默认；简易 = 上下两块（预览 + 时间线）；
/// 专业 = 项目/效果控件 + 预览 + 时间线；极简 = 只有预览（项目面板与时间线消失）。
pub fn ours_layout(name: &str) -> Layout {
    use PanelKind::*;
    use SplitSize::*;
    match name {
        "simple" => Layout { root: Some(vsplit(Ratio(0.56), tabs(&[Composition], 0), tabs(&[Timeline], 0))), floating: Vec::new() },
        "pro" => Layout {
            root: Some(vsplit(
                Ratio(0.58),
                hsplit(FixedFirst(220.0), tabs(&[Project, EffectControls], 0), tabs(&[Composition], 0)),
                tabs(&[Timeline], 0),
            )),
            floating: Vec::new(),
        },
        "minimal" => Layout { root: Some(tabs(&[Composition], 0)), floating: Vec::new() },
        _ => workspace("Default"),
    }
}

'''

ENTRY_INSERT = r'''    // EFFECTCRAFT_OURS_CANVAS_LAYOUT_ENTRY_V1 — 画布（预览区）内部右上角 8px 处的「布局」按钮，
    // 外观与工具栏的「曲线 / 插件」一致（同 26px 高、4px 圆角、switch_well 底、12pt 字）。
    // 展开时不画：否则打开它的那次点击会被遮罩判成“点空白”而立刻关掉。
    if ui.data(|d| d.get_temp::<f64>(egui::Id::new("layout-open-at"))).is_none() {
        let t = app.tokens;
        let galley = painter.layout_no_wrap("布局".to_string(), Tokens::ui(12.0), t.text);
        let btn_w = (galley.size().x + 22.0).max(44.0);
        let r = Rect::from_min_size(pos2(v.area.max.x - 8.0 - btn_w, v.area.min.y + 8.0), vec2(btn_w, 26.0));
        let resp = ui.interact(r, egui::Id::unique("layout-entry-canvas"), Sense::click());
        painter.rect_filled(r, 4.0, if resp.hovered() { t.hover } else { t.switch_well });
        painter.text(r.center(), egui::Align2::CENTER_CENTER, "布局", Tokens::ui(12.0), t.text);
        app.auto.add("layout.switcher", r, "布局");
        if resp.clicked() {
            ui.data_mut(|d| d.insert_temp(egui::Id::new("layout-open-at"), app.now));
            ui.ctx().request_repaint();
        }
    }
'''

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    # 1) dock 里加四套布局
    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if "pub fn ours_layout(" not in src:
        if src.count(DOCK_ANCHOR) != 1:
            raise SystemExit(f"dock anchor: {src.count(DOCK_ANCHOR)}")
        dock.write_text(src.replace(DOCK_ANCHOR, DOCK_INSERT + DOCK_ANCHOR, 1), encoding="utf-8")
        print("dock: four layouts added")

    # 2) 预览区里画入口
    viewer = root / "crates/ui-egui/src/panels/viewer.rs"
    src = viewer.read_text(encoding="utf-8")
    if "EFFECTCRAFT_OURS_CANVAS_LAYOUT_ENTRY_V1" not in src:
        anchor = "    v.mods = mods;\n    v.space_pan = space_pan;\n    v.text_owns = text_owns;\n}\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"phase_press anchor: {src.count(anchor)}")
        src = src.replace(anchor, ENTRY_INSERT + anchor, 1)
        print("viewer: layout entry inside the canvas")

    viewer.write_text(src, encoding="utf-8")


if __name__ == "__main__":
    main()
