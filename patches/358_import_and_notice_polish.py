#!/usr/bin/env python3
"""两处打磨：

1. `.aep` 导入完成后的提示不再只给一个数字，而是按类别列出（`effects: 3, masks: 1`）。
2. 画布上「Missing footage …」那条橙色横幅可以点 ✕ 关掉，本次会话内不再重复出现
   （缺素材是 AEP 跨机器导入的常态，常驻太吵）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NOTICE_POLISH_V1"

# ① 引擎：toast 带类别明细
AEP_OLD = '''        format!("Imported {name} ({losses} unsupported item{} not imported)", if losses == 1 { "" } else { "s" })'''
AEP_NEW = '''        format!("Imported {name} ({losses} unsupported: {})", res.report.summary())'''

# ② 画布横幅：可关闭
VIEW_OLD = '''    for (notices, (layer, why)) in footage_problems(app, ectx, comp, time).into_iter().enumerate() {
        let (m, _) = l2c(ectx, layer);'''
VIEW_NEW = '''    // EFFECTCRAFT_OURS_NOTICE_POLISH_V1 — 横幅可关闭：点过 ✕ 的图层本次会话内不再提示。
    let notice_ctx = v.ctx.clone();
    let dismissed: Vec<u64> = notice_ctx
        .data(|d| d.get_temp::<Vec<u64>>(egui::Id::new("viewer-notice-dismissed")))
        .unwrap_or_default();
    for (notices, (layer, why)) in footage_problems(app, ectx, comp, time).into_iter().enumerate() {
        if dismissed.contains(&layer.id.0) {
            continue;
        }
        let (m, _) = l2c(ectx, layer);'''

VIEW_DRAW_OLD = '''        app.auto.add(&format!("viewer.footageProblem.{}", layer.id.0), r, &text);
    }'''
VIEW_DRAW_NEW = '''        // 右上角的 ✕：点它就不再显示这条提示。
        let close = Rect::from_min_size(pos2(r.max.x - 18.0, r.min.y + 3.0), vec2(15.0, 15.0));
        painter.text(close.center(), Align2::CENTER_CENTER, "\\u{00d7}", Tokens::ui(13.0), Color32::WHITE);
        app.auto.add(&format!("viewer.footageProblem.{}", layer.id.0), r, &text);
        let clicked = notice_ctx.input(|i| {
            i.pointer.primary_clicked() && i.pointer.interact_pos().is_some_and(|p| close.contains(p))
        });
        if clicked {
            let mut next = dismissed.clone();
            if !next.contains(&layer.id.0) {
                next.push(layer.id.0);
            }
            notice_ctx.data_mut(|d| d.insert_temp(egui::Id::new("viewer-notice-dismissed"), next));
        }
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    aep = root / "crates/engine/src/cmd/aep.rs"
    src = aep.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(AEP_OLD) != 1:
            raise SystemExit(f"aep toast anchor: {src.count(AEP_OLD)}")
        aep.write_text(src.replace(AEP_OLD, AEP_NEW, 1), encoding="utf-8")
        print("aep toast now lists loss categories")

    viewer = root / "crates/ui-egui/src/panels/viewer.rs"
    src = viewer.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(VIEW_OLD) != 1:
            raise SystemExit(f"viewer banner anchor: {src.count(VIEW_OLD)}")
        src = src.replace(VIEW_OLD, VIEW_NEW, 1)
        if src.count(VIEW_DRAW_OLD) != 1:
            raise SystemExit(f"viewer draw anchor: {src.count(VIEW_DRAW_OLD)}")
        src = src.replace(VIEW_DRAW_OLD, VIEW_DRAW_NEW, 1)
        viewer.write_text(src, encoding="utf-8")
        print("footage banner is dismissible")


if __name__ == "__main__":
    main()
