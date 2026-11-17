#!/usr/bin/env python3
"""汉化第二十批：状态栏/反馈长句 + GPU 提示（HANDOFF 第 6 节点名的「命令反馈长句、GPU/渲染提示」）。

状态栏消息本来就会过 `i18n::status()`（`137_status_zh.py` 改的 `draw_toast`），所以普通句子只补表就行；
`format!` 拼出来的四句改成 `tr_args`，否则永远匹配不上表。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH20_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH20_V1 — 状态栏反馈长句与 GPU 提示
    ("Select a layer to sketch its motion", "请选择一个图层来记录它的运动"),
    ("Motion Sketch: drag in the Composition panel to record", "运动草图：在合成面板里拖动即可记录"),
    ("no file dialog available: type the path", "没有可用的文件对话框：请直接输入路径"),
    ("no file dialog available: set the path with prop.set", "没有可用的文件对话框：请用 prop.set 设置路径"),
    ("Object Matte: click an object on a footage, solid or composition layer", "对象蒙版：在素材、纯色或合成图层上点选一个对象"),
    ("New 3D Primitive closed: the composition changed", "「新建 3D 对象」已关闭：合成已经变了"),
    ("Interpret Footage: select a footage item", "解释素材：请先选择一个素材项"),
    ("Make a composition first: a template is saved from the open project.", "请先建一个合成：模板是从当前打开的工程里保存的。"),
    ("Graphics device lost. The project is still open; presentation requires restarting the application.", "图形设备丢失。工程仍然是打开的；要恢复画面需要重启应用。"),
    ("Shared GPU preview disabled; CPU compositing remains available.", "已停用共享 GPU 预演；仍可用 CPU 合成。"),
    ("Preparing the GPU compositor… (compositing on the CPU until it is ready)", "正在准备 GPU 合成器…（就绪之前先用 CPU 合成）"),
    ("GPU compositor unavailable: the window has no wgpu device", "GPU 合成不可用：窗口没有 wgpu 设备"),
    ("the compositor's worker thread ended without a result", "合成器的工作线程没有返回结果就结束了"),
    ("backend panicked", "渲染后端崩溃"),
    ("synthetic host device failure", "测试用的宿主设备失败"),
    ("presentation requires restarting", "需要重启才能恢复显示"),
    ("can't open {}: {}", "无法打开 {}：{}"),
    ("This shortcut belongs to {}: focus one of them", "这个快捷键属于 {}：请先让其中之一获得焦点"),
    ("Motion Sketch: {} Position keyframes", "运动草图：已记录 {} 个位置关键帧"),
    ("Keyframe at {}", "关键帧位于 {}"),
"""

EDITS: list[tuple[str, str, str, int]] = [
    (
        "crates/ui-egui/src/app/window.rs",
        '                    self.ui.status = format!("can\'t open {}: {e}", p.title());\n',
        '                    self.ui.status = crate::i18n::tr_args("can\'t open {}: {}", &[&p.title(), &e]);\n',
        1,
    ),
    (
        "crates/ui-egui/src/menus/shortcuts.rs",
        '                app.ui.status = format!("This shortcut belongs to {}: focus one of them", panels.join(" and "));\n',
        '                app.ui.status = crate::i18n::tr_args("This shortcut belongs to {}: focus one of them", &[&panels.join(" and ")]);\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/anim_tools.rs",
        '            Ok(r) => app.ui.status = format!("Motion Sketch: {} Position keyframes", r["keys"]),\n',
        '            Ok(r) => app.ui.status = crate::i18n::tr_args("Motion Sketch: {} Position keyframes", &[&r["keys"]]),\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/timeline.rs",
        '                app.ui.status = format!("Keyframe at {}", super::timecode(&app.session, &comp, at));\n',
        '                app.ui.status = crate::i18n::tr_args("Keyframe at {}", &[&super::timecode(&app.session, &comp, at)]);\n',
        1,
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    ui = root / "crates/ui-egui/src/i18n/ui.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(ANCHOR) != 1:
            raise SystemExit(f"ui anchor: {src.count(ANCHOR)}")
        src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH20_V1", 1)
        ui.write_text(src, encoding="utf-8")
        print("batch 20 rows added")
    for rel, old, new, want in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        got = text.count(old)
        if got != want:
            raise SystemExit(f"{rel}: anchor {got} != {want}")
        path.write_text(text.replace(old, new, want), encoding="utf-8")
    print("batch 20 sites wired")


if __name__ == "__main__":
    main()
