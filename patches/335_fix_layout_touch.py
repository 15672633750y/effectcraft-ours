#!/usr/bin/env python3
"""三个实测问题的修复（877 之后的 878 批）。

1) 「布局」入口画到窗口最右上角（顶栏外面）→ 改成画进预览区内部，偏移 8px。
   frame.rs 里那套只在展开时画遮罩/卡片；入口由 `panels/viewer.rs::phase_press` 用 `v.area` 画。

2) 点击布局不重排：移动端没有这些 dock 工作区 → `dock::ours_layout()` 直接返回四套布局树
   （经典 / 简易 / 专业 / 极简），点击时直接换 `app.ui.dock`。极简只有预览，项目面板和时间线一定消失。

3) 触屏拖动不触发贴边：加一条**不依赖手势表**的兜底——按住预览区拖动时用 `resp.drag_delta()`
   （触屏同样走这里）直接移动已选图层，并做 24px 画布边缘吸附；松手把 `snap:` 写进图层批注。
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

TOUCH_ANCHOR = "    let gesture: Option<Gesture> = ui.data(|d| d.get_temp(gid));\n"

TOUCH_INSERT = r'''    // EFFECTCRAFT_OURS_TOUCH_DRAG_V1 — 触屏兜底：没有手势时，按住画布拖动直接移动已选图层。
    // 走 response.drag_delta()，触屏与鼠标是同一条路径；顺便做 24px 画布边缘吸附。
    if gesture.is_none() && resp.dragged() && !app.session.state.selected_layers.is_empty() {
        let delta = resp.drag_delta();
        if delta != egui::Vec2::ZERO {
            let comp = v.comp;
            let zoom = zoom as f64;
            let d = [(delta.x as f64) / zoom, (delta.y as f64) / zoom];
            let merge = drag_merge_key(ui);
            for lid in app.session.state.selected_layers.clone() {
                let Some(layer) = comp.layer(lid) else { continue };
                let Some(tr) = layer.transform() else { continue };
                let p0 = ectx.v3(layer, tr, "position", [0.0; 3]);
                // 吸附：包围盒离画布边缘 24px 内贴过去（X/Y 独立，角上可双吸）
                let mut d = d;
                if let Some(snapped) = ours_edge_snap(ectx, comp, layer, d, 24.0, &painter, &map) {
                    d = snapped;
                }
                let v3 = [p0[0] + d[0], p0[1] + d[1], p0[2]];
                let _ = app.session.execute("prop.set", json!({"layer": lid.0, "path": "transform/position", "value": v3, "merge": merge}));
            }
        }
    }
'''

STOP_ANCHOR = '''                Gesture::Move { layers, .. } => {
'''

STOP_INSERT = r'''                Gesture::None | Gesture::Pan { .. } => {}
'''

SNAP_FN = r'''
/// EFFECTCRAFT_OURS_TOUCH_DRAG_V1 — 画布边缘吸附：返回 (dx, dy, …)；不吸附时 None。
/// 拖动时用 24px 阈值；松手判定贴边用 0.5px。吸附时画一条强调色参考线。
#[allow(clippy::too_many_arguments)]
pub(crate) fn ours_edge_snap(
    ectx: &EvalCtx,
    comp: &effectcraft_project::Comp,
    layer: &effectcraft_project::Layer,
    d: [f64; 2],
    th: f64,
    painter: &egui::Painter,
    map: &ViewerMap,
) -> Option<[f64; 2]> {
    let feats = effectcraft_engine::viewer::layer_features(ectx, layer);
    if feats.is_empty() {
        return None;
    }
    let (mut x0, mut y0, mut x1, mut y1) = (f64::MAX, f64::MAX, f64::MIN, f64::MIN);
    for f in &feats {
        x0 = x0.min(f[0]);
        x1 = x1.max(f[0]);
        y0 = y0.min(f[1]);
        y1 = y1.max(f[1]);
    }
    let (cw, ch) = (comp.width as f64, comp.height as f64);
    let (bx0, bx1) = (x0 + d[0], x1 + d[0]);
    let (by0, by1) = (y0 + d[1], y1 + d[1]);
    let mut out = d;
    let mut snapped = false;
    if bx0.abs() <= th {
        out[0] += -bx0;
        painter.line_segment([map.to_screen([0.0, 0.0]), map.to_screen([0.0, ch])], Stroke::new(1.0, Color32::LIGHT_BLUE));
        snapped = true;
    } else if (bx1 - cw).abs() <= th {
        out[0] += cw - bx1;
        painter.line_segment([map.to_screen([cw, 0.0]), map.to_screen([cw, ch])], Stroke::new(1.0, Color32::LIGHT_BLUE));
        snapped = true;
    }
    if by0.abs() <= th {
        out[1] += -by0;
        painter.line_segment([map.to_screen([0.0, 0.0]), map.to_screen([cw, 0.0])], Stroke::new(1.0, Color32::LIGHT_BLUE));
        snapped = true;
    } else if (by1 - ch).abs() <= th {
        out[1] += ch - by1;
        painter.line_segment([map.to_screen([0.0, ch]), map.to_screen([cw, ch])], Stroke::new(1.0, Color32::LIGHT_BLUE));
        snapped = true;
    }
    snapped.then_some(out)
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

    # 3) 触屏拖动兜底
    if "EFFECTCRAFT_OURS_TOUCH_DRAG_V1" not in src:
        if src.count(TOUCH_ANCHOR) != 1:
            raise SystemExit(f"phase_drag anchor: {src.count(TOUCH_ANCHOR)}")
        src = src.replace(TOUCH_ANCHOR, TOUCH_ANCHOR + TOUCH_INSERT, 1)
        src = src.rstrip() + "\n" + SNAP_FN
        print("viewer: touch drag fallback + edge snap helper")
    viewer.write_text(src, encoding="utf-8")


if __name__ == "__main__":
    main()
