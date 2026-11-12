#!/usr/bin/env python3
"""Chinese for the undo/redo entries (the edit labels are English in the engine)."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_UNDO_LABELS_V1"
OLD = '            s.history.undo.iter().rev().enumerate().map(|(i, (l, _))| dyn_entry(format!("Undo {l}"), "edit.history", json!({"steps": i + 1}))).collect(),'
NEW = '            s.history.undo.iter().rev().enumerate().map(|(i, (l, _))| dyn_entry(format!("撤销 {}", zh_edit_label(l)), "edit.history", json!({"steps": i + 1}))).collect(),'

HELPER = '''
// {marker}
/// The engine labels edits in English; the menu reads better in Chinese.
fn zh_edit_label(label: &str) -> &str {
    match label {
        "Add Footage to Comp" => "将素材添加到合成",
        "Ripple Insert Edit" => "波纹插入编辑",
        "Overlay Edit" => "覆盖编辑",
        "New Adjustment Layer" => "新建调整图层",
        "New Solid" => "新建纯色",
        "New Comp" => "新建合成",
        "Set Value" => "修改数值",
        "Add Keyframe" => "添加关键帧",
        "Delete Keyframe" => "删除关键帧",
        "Move Layer" => "移动图层",
        "Delete Layer" => "删除图层",
        "Duplicate Layer" => "复制图层",
        "Rename" => "重命名",
        "Import" => "导入",
        "Apply Effect" => "应用效果",
        "Move Keyframe" => "移动关键帧",
        "Trim Layer" => "裁剪图层",
        "Change Property" => "修改属性",
        "Reset Property" => "重置属性",
        "Add/Remove Keyframe" => "添加/移除关键帧",
        "Toggle Animation" => "切换动画",
        "Convert Audio to Keyframes" => "音频转关键帧",
        "Convert Expression to Keyframes" => "表达式转关键帧",
        "New Comp from Selection" => "从所选新建合成",
        "Replace Footage" => "替换素材",
        "Replace with Precomposition" => "替换为预合成",
        "Record Puppet Pins" => "记录木偶销钉",
        "Nulls Follow Points" => "空对象跟随点",
        "Points Follow Nulls" => "点跟随空对象",
        "Follow-Through" => "跟随惯性",
        "Trace Path" => "跟踪路径",
        "Create VR Environment" => "创建 VR 环境",
        "Extract Cubemap" => "提取立方体贴图",
        "RPF Camera Import" => "导入 RPF 摄像机",
        "VR View Orientation" => "VR 视图方向",
        other => other,
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/menus.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("undo labels already translated")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"undo anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.rstrip() + "\n" + HELPER.replace("{marker}", MARKER)
    path.write_text(src + "\n", encoding="utf-8")
    print("undo entries are Chinese now")


if __name__ == "__main__":
    main()
