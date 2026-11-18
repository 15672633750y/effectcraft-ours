#!/usr/bin/env python3
"""「全选」只选图层；效果控件里要的是「选中当前图层的所有效果」。

新增 ours.selectAllEffects：把选中图层 effects 组里每个效果的 uid 写进
state.selected_props（效果/属性的选中集合），返回选中的个数。
快捷面板再加一个「全效」方块指向它。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_ALL_EFFECTS_V1"

SPEC_OLD = '''    ), cmd!(
        "ours.shareFile",'''
SPEC_NEW = '''    ), cmd!(
        "ours.selectAllEffects",
        "全选效果",
        [],
        None,
        "{}",
        always,
        select_all_effects
    ), cmd!(
        "ours.shareFile",'''

FN = r'''

/// EFFECTCRAFT_OURS_SELECT_ALL_EFFECTS_V1 — 选中当前图层（们）上的所有效果。
fn select_all_effects(s: &mut Session, _p: &Value) -> Result<Value> {
    let comp = s.active_comp().ok_or(crate::EngineError::NoComp)?;
    let mut picked: Vec<(effectcraft_project::LayerId, effectcraft_project::Uid)> = Vec::new();
    for lid in s.state.selected_layers.clone() {
        let Some(layer) = comp.layer(lid) else { continue };
        let Some(fx) = layer.props.sub("effects") else { continue };
        for group in fx.groups() {
            picked.push((lid, group.uid));
        }
    }
    let count = picked.len();
    s.state.selected_props = picked;
    Ok(json!({ "effects": count }))
}
'''

TILE_OLD = '''        ("全选", "Ctrl+A", "edit.selectAll", serde_json::json!({})),
    ];'''
TILE_NEW = '''    ];'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(SPEC_OLD) != 1:
            raise SystemExit(f"spec anchor: {src.count(SPEC_OLD)}")
        src = src.replace(SPEC_OLD, SPEC_NEW, 1)
        src += FN
        path.write_text(src, encoding="utf-8")
        print("ours.selectAllEffects registered")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if TILE_NEW not in src:
        if src.count(TILE_OLD) != 1:
            raise SystemExit(f"tile anchor: {src.count(TILE_OLD)}")
        src = src.replace(TILE_OLD, TILE_NEW, 1)
        # 11 项 -> 4 行仍然够（320 高），不用再改尺寸
        frame.write_text(src, encoding="utf-8")
        print("全效 tile added")


if __name__ == "__main__":
    main()
