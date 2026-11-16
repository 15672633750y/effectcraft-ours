#!/usr/bin/env python3
"""汉化第十批：把剩下的「裸画」文字改成查表（约 10 处）+ 6 行带占位符的翻译。

`ui.heading("Rendering script")`、`ui.small_button("Revert")` 这类调用直接把英文字面量交给 egui，
从不查 `i18n` 表，所以表里有中文也显示英文。这一批只把「画出来的字」换成 `tr()` / `tr_args()`；
英文界面下两者原样返回，行为不变。自动化/无障碍标签不动。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH10_V1"

UI_ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

UI_ROWS = """    ("{} / {} frames", "{} / {} 帧"),
    ("{} of {} commands", "共 {} 个命令，列出 {} 个"),
    ("Delete the preset “{}”?", "删除预设「{}」？"),
    ("Delete the template “{}”?", "删除模板「{}」？"),
    ("Analyzing {} / {} frames  ({} fps)", "正在分析 {} / {} 帧（{} fps）"),
    ("Tracking {} / {} frames  ({} fps)", "正在跟踪 {} / {} 帧（{} fps）"),
"""

EDITS: list[tuple[str, str, str, int]] = [
    # 脚本渲染遮罩（渲染脚本时盖在画布上的那层）
    (
        "crates/ui-egui/src/app/frame.rs",
        '                ui.heading("Rendering script");\n'
        '                ui.label("The script will continue when rendering finishes. Editing is paused to preserve its undo group.");\n'
        '                if let Some(progress) = self.session.render_progress() {\n'
        '                    ui.label(format!("{} / {} frames", progress.done, progress.total));\n'
        '                }\n'
        '                let stop = ui.button("Stop Render");\n',
        '                ui.heading(crate::i18n::tr("Rendering script"));\n'
        '                ui.label(crate::i18n::tr("The script will continue when rendering finishes. Editing is paused to preserve its undo group."));\n'
        '                if let Some(progress) = self.session.render_progress() {\n'
        '                    ui.label(crate::i18n::tr_args("{} / {} frames", &[&progress.done, &progress.total]));\n'
        '                }\n'
        '                let stop = ui.button(crate::i18n::tr("Stop Render"));\n',
        1,
    ),
    # 基本图形面板：Revert / Push
    (
        "crates/ui-egui/src/panels/essential.rs",
        '                let r = ui.small_button("Revert");\n',
        '                let r = ui.small_button(crate::i18n::tr("Revert"));\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/essential.rs",
        '                let r = ui.small_button("Push");\n',
        '                let r = ui.small_button(crate::i18n::tr("Push"));\n',
        1,
    ),
    # 快捷键编辑器：Remove 按钮 + 「列出 N / 共 M 个命令」
    (
        "crates/ui-egui/src/panels/shortcut_editor.rs",
        '                        let r = ui.small_button("Remove");\n',
        '                        let r = ui.small_button(crate::i18n::tr("Remove"));\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/shortcut_editor.rs",
        '                ui.label(RichText::new(format!("{} of {} commands", rows.len(), table.bindables.len())).color(t.text_faint));\n',
        '                ui.label(RichText::new(crate::i18n::tr_args("{} of {} commands", &[&rows.len(), &table.bindables.len()])).color(t.text_faint));\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/shortcut_editor.rs",
        '            ui.label(RichText::new(format!("Delete the preset “{name}”?")).color(t.tab_text_active));\n',
        '            ui.label(RichText::new(crate::i18n::tr_args("Delete the preset “{}”?", &[&name])).color(t.tab_text_active));\n',
        1,
    ),
    # 模板删除确认
    (
        "crates/ui-egui/src/panels/templates.rs",
        '        ui.label(egui::RichText::new(format!("Delete the template “{name}”?")).color(t.tab_text_active));\n',
        '        ui.label(egui::RichText::new(crate::i18n::tr_args("Delete the template “{}”?", &[&name])).color(t.tab_text_active));\n',
        1,
    ),
    # 跟踪/分析进度行（{:.0} 先格式化，再交给 tr_args）
    (
        "crates/ui-egui/src/panels/tracker.rs",
        '            format!("Analyzing {} / {} frames  ({:.0} fps)", pr.done, pr.total, pr.fps),\n',
        '            crate::i18n::tr_args("Analyzing {} / {} frames  ({} fps)", &[&pr.done, &pr.total, &format!("{:.0}", pr.fps)]),\n',
        1,
    ),
    (
        "crates/ui-egui/src/panels/tracker.rs",
        '            format!("Tracking {} / {} frames  ({:.0} fps)", pr.done, pr.total, pr.fps),\n',
        '            crate::i18n::tr_args("Tracking {} / {} frames  ({} fps)", &[&pr.done, &pr.total, &format!("{:.0}", pr.fps)]),\n',
        1,
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    ui = root / "crates/ui-egui/src/i18n/ui.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(UI_ANCHOR) != 1:
            raise SystemExit(f"ui anchor: {src.count(UI_ANCHOR)}")
        src = src.replace(UI_ANCHOR, UI_ROWS + UI_ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH10_V1", 1)
        ui.write_text(src, encoding="utf-8")
        print("batch 10 rows added")
    for rel, old, new, want in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        got = text.count(old)
        if got != want:
            raise SystemExit(f"{rel}: anchor count {got} != {want}")
        path.write_text(text.replace(old, new, want), encoding="utf-8")
    print("batch 10 sites wired")


if __name__ == "__main__":
    main()
