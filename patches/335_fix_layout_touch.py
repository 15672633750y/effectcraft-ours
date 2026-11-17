#!/usr/bin/env python3
"""布局真正的重排 + 入口位置（APP-交接 2.1 / 2.3）。

1) 「布局」入口不再自己画在预览区里，只把**画布矩形**记进 ctx data
   （`ours-canvas-rect`），按钮由 frame.rs 的 `draw_layout_switcher` 统一画。
   这样没有打开合成时按钮照样在，样式也和「曲线 / 插件」完全同款。

2) 点击布局不重排：移动端没有这些 dock 命名工作区 → `dock::ours_layout()` 直接返回四套
   布局树，点击时直接换 `app.ui.dock`。比例按 APP-交接 2.3：
   - 经典：上游默认工作区（项目 + 合成 + 属性 + 时间线）；万一它是空树，退回一个
     最小可用布局，绝不给空界面
   - 简易：没有项目面板，时间线压到 35%
   - 专业：项目 | 合成 | 属性 三栏 + 下方时间线 45%
   - 极简：只有合成预览（项目面板与时间线都消失）

（PNG 拖动贴边已由用户取消，本补丁不碰 phase_drag。）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_REAL_V3"

DOCK_ANCHOR = "#[cfg(test)]\n"
DOCK_INSERT = '''/// EFFECTCRAFT_OURS_LAYOUT_REAL_V3 — 「布局」切换器用的四套布局树。
/// 只负责“摆放”，全部复用现有面板与渲染代码，不复制任何绘制逻辑：
/// 经典 = 上游默认工作区；简易 = 上预览 + 下时间线（时间线 35%，无项目面板）；
/// 专业 = 项目 | 预览 | 属性 三栏 + 下方时间线 45%；极简 = 只有预览。
pub fn ours_layout(name: &str) -> Layout {
    use PanelKind::*;
    use SplitSize::*;
    let simple = || Layout { root: Some(vsplit(Ratio(0.65), tabs(&[Composition], 0), tabs(&[Timeline], 0))), floating: Vec::new() };
    match name {
        "simple" => simple(),
        "pro" => Layout {
            root: Some(vsplit(
                Ratio(0.55),
                hsplit(
                    FixedFirst(190.0),
                    tabs(&[Project], 0),
                    hsplit(Ratio(0.70), tabs(&[Composition], 0), tabs(&[EffectControls], 0)),
                ),
                tabs(&[Timeline], 0),
            )),
            floating: Vec::new(),
        },
        "minimal" => Layout { root: Some(tabs(&[Composition], 0)), floating: Vec::new() },
        _ => {
            // 经典：上游的 Default 工作区。它要是不存在（以后改了名）就给一个最小可用布局，
            // 绝不把用户丢到空界面。
            let classic = workspace("Default");
            if classic.root.is_some() { classic } else { simple() }
        }
    }
}

'''

VIEWER_ANCHOR = (
    "    let t = app.tokens;\n"
    "    let ctx = ui.ctx().clone();\n"
    "    let Some(cid) = app.session.active_comp_id() else {\n"
    "        empty_state(app, ui, rect);\n"
    "        return;\n"
    "    };\n"
)
VIEWER_NEW = (
    "    let t = app.tokens;\n"
    "    let ctx = ui.ctx().clone();\n"
    "    // EFFECTCRAFT_OURS_CANVAS_RECT_V1 — 记下画布矩形，「布局」按钮由 frame.rs 贴在它的\n"
    "    // 右上角。先按整个预览面板记一次（没有打开合成时也照样在），下面算完再收窄到画布。\n"
    "    ctx.data_mut(|d| d.insert_temp(egui::Id::new(\"ours-canvas-rect\"), rect));\n"
    "    let Some(cid) = app.session.active_comp_id() else {\n"
    "        empty_state(app, ui, rect);\n"
    "        return;\n"
    "    };\n"
)

TAIL_ANCHOR = "    phase_tail(app, ui, &ectx, &mut v);\n}\n"
TAIL_NEW = "    ui.data_mut(|d| d.insert_temp(egui::Id::new(\"ours-canvas-rect\"), v.area));\n    phase_tail(app, ui, &ectx, &mut v);\n}\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    # 1) dock 里加四套布局
    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(DOCK_ANCHOR) != 1:
            raise SystemExit(f"dock anchor: {src.count(DOCK_ANCHOR)}")
        dock.write_text(src.replace(DOCK_ANCHOR, DOCK_INSERT + DOCK_ANCHOR, 1), encoding="utf-8")
        print("dock: four layouts added")

    # 2) 预览区把画布矩形记下来（入口本身由 frame.rs 画）
    viewer = root / "crates/ui-egui/src/panels/viewer.rs"
    src = viewer.read_text(encoding="utf-8")
    if "EFFECTCRAFT_OURS_CANVAS_RECT_V1" not in src:
        if src.count(VIEWER_ANCHOR) != 1:
            raise SystemExit(f"viewer show-head anchor: {src.count(VIEWER_ANCHOR)}")
        src = src.replace(VIEWER_ANCHOR, VIEWER_NEW, 1)
        if src.count(TAIL_ANCHOR) != 1:
            raise SystemExit(f"viewer tail anchor: {src.count(TAIL_ANCHOR)}")
        src = src.replace(TAIL_ANCHOR, TAIL_NEW, 1)
        viewer.write_text(src, encoding="utf-8")
        print("viewer: canvas rect recorded for the layout entry")


if __name__ == "__main__":
    main()
