#!/usr/bin/env python3
"""汉化第十六批：还剩的几个窗口/对话框标题 + 纯色设置的尺寸说明（约 15 条）。

对话框标题本身已经过 `tr()`（`dialogs::modal` 里就是这么画的），所以缺的只是表里的中文行；
`format!` 拼出来的句子永远匹配不上表，改成 `tr_args` 拼。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH16_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH16_V1 — 窗口/对话框标题与组合句
    ("Unsaved Changes", "未保存的更改"),
    ("Revert Project", "恢复工程"),
    ("Keyframe Velocity", "关键帧速度"),
    ("Keyframe Velocity: {}", "关键帧速度：{}"),
    ("Export Adobe After Effects Project", "导出 Adobe After Effects 工程"),
    ("Output Module Templates", "输出模块模板"),
    ("Render Settings Templates", "渲染设置模板"),
    ("Video Preview — {}", "视频预览 — {}"),
    ("Width: {}% of comp", "宽度：占合成的 {}%"),
    ("Height: {}% of comp", "高度：占合成的 {}%"),
    ("Frame Aspect Ratio: {}", "帧宽高比：{}"),
    ("No shortcut", "没有快捷键"),
"""

EDITS: list[tuple[str, str, str, int]] = [
    # 关键帧速度对话框的标题（带图层名/属性名时走 tr_args）
    (
        "crates/ui-egui/src/panels/key_dialogs.rs",
        '    let title = if d.name.is_empty() { "Keyframe Velocity".to_string() } else { format!("Keyframe Velocity: {}", d.name) };\n',
        '    let title = if d.name.is_empty() { crate::i18n::tr("Keyframe Velocity").to_string() } else { crate::i18n::tr_args("Keyframe Velocity: {}", &[&d.name]) };\n',
        1,
    ),
    # 纯色设置里的「占合成的百分比」三行说明
    (
        "crates/ui-egui/src/panels/dialogs.rs",
        '        ui.label(\n'
        '            egui::RichText::new(format!(\n'
        '                "Width: {:.1}% of comp\\nHeight: {:.1}% of comp\\nFrame Aspect Ratio: {}",\n'
        '                pct(size[0], comp_size.0),\n'
        '                pct(size[1], comp_size.1),\n'
        '                super::comp_settings::aspect_label(size[0] as f64 * par, size[1] as f64)\n'
        '            ))\n'
        '            .color(Color32::GRAY),\n'
        '        );\n',
        '        let size_note = [\n'
        '            crate::i18n::tr_args("Width: {}% of comp", &[&format!("{:.1}", pct(size[0], comp_size.0))]),\n'
        '            crate::i18n::tr_args("Height: {}% of comp", &[&format!("{:.1}", pct(size[1], comp_size.1))]),\n'
        '            crate::i18n::tr_args("Frame Aspect Ratio: {}", &[&super::comp_settings::aspect_label(size[0] as f64 * par, size[1] as f64)]),\n'
        '        ]\n'
        '        .join("\\n");\n'
        '        ui.label(egui::RichText::new(size_note).color(Color32::GRAY));\n',
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
        src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH16_V1", 1)
        ui.write_text(src, encoding="utf-8")
        print("batch 16 rows added")
    for rel, old, new, want in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        got = text.count(old)
        if got != want:
            raise SystemExit(f"{rel}: anchor count {got} != {want}")
        path.write_text(text.replace(old, new, want), encoding="utf-8")
    print("batch 16 sites wired")


if __name__ == "__main__":
    main()
