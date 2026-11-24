#!/usr/bin/env python3
"""「全选」按 AE 的方式：焦点在哪块就全选哪块，而且真的生效。

上一版为了"必有点反应"改成无条件先全选图层，这与 AE 行为不符（用户要求：在效果控件就选效果，
在图层/时间线就选图层）。真正的毛病是**焦点会被浮层抢走**：点「快捷」面板上的按钮时
`app.ui.focused` 可能不再是效果控件，于是分派到了图层。

改法：
1. frame.rs 每帧记录**最后一个真正的内容面板**（Project / EffectControls / Composition / Layer /
   Timeline），浮层不覆盖这个记录 → `ours-last-focus`。
2. `ours.selectAllCtx` 用它分派：
   * 效果控件 → `ours.selectAllEffects`（没有选中图层时给一句提示）
   * 其余 → `edit.selectAll`
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_ALL_AE_V1"

INV_OLD = '''    if id == "ours.selectAllCtx" {
        // EFFECTCRAFT_OURS_SELECT_ALL_QUIET_V1 — 先无条件全选图层（点击必须看得见效果）
        let layers = invoke(app, ctx, "edit.selectAll", json!({}));
        if app.ui.focused == crate::PanelKind::EffectControls {
            // 焦点在效果控件时，再把它这个图层上的效果也全选（失败不影响图层选择）
            let _ = invoke(app, ctx, "ours.selectAllEffects", json!({}));
        }
        return layers;
    }'''

INV_NEW = '''    if id == "ours.selectAllCtx" {
        // EFFECTCRAFT_OURS_SELECT_ALL_AE_V1 — 焦点在哪块就全选哪块（AE 行为）
        let last = ctx
            .data(|d| d.get_temp::<String>(egui::Id::new("ours-last-focus")))
            .unwrap_or_default();
        let on_effects = last == crate::PanelKind::EffectControls.title()
            || app.ui.focused == crate::PanelKind::EffectControls;
        if on_effects {
            let n = app.session.state.selected_layers.len();
            if n == 0 {
                app.ui.status = "先选中一个图层，再全选它的效果".to_string();
                return Ok(json!(0));
            }
            return invoke(app, ctx, "ours.selectAllEffects", json!({}));
        }
        return invoke(app, ctx, "edit.selectAll", json!({}));
    }'''

FRAME_ANCHOR = '''        // EFFECTCRAFT_OURS_MOBILE_AUTOSAVE_V1 — 切后台/失焦立刻自动保存一次，防后台被杀丢活'''

FRAME_INSERT = '''        // EFFECTCRAFT_OURS_SELECT_ALL_AE_V1 — 记住最后一个"内容面板"，浮层抢焦点也不影响全选分派
        {
            use crate::dock::PanelKind as P;
            let f = self.ui.focused;
            if matches!(
                f,
                P::Project | P::EffectControls | P::Composition | P::Layer | P::Timeline
            ) {
                ui.ctx().data_mut(|d| {
                    d.insert_temp(egui::Id::new("ours-last-focus"), f.title().to_string())
                });
            }
        }
        // EFFECTCRAFT_OURS_MOBILE_AUTOSAVE_V1 — 切后台/失焦立刻自动保存一次，防后台被杀丢活'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    inv = root / "crates/ui-egui/src/menus/invoke.rs"
    src = inv.read_text(encoding="utf-8")
    if INV_OLD not in src:
        raise SystemExit("invoke anchor missing")
    inv.write_text(src.replace(INV_OLD, INV_NEW, 1), encoding="utf-8")
    print("select-all dispatches on the last real panel")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("focus memory already present")
        return
    if src.count(FRAME_ANCHOR) != 1:
        raise SystemExit(f"frame anchor: {src.count(FRAME_ANCHOR)}")
    frame.write_text(src.replace(FRAME_ANCHOR, FRAME_INSERT, 1), encoding="utf-8")
    print("frame remembers the last content panel")


if __name__ == "__main__":
    main()
