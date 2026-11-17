#!/usr/bin/env python3
"""汉化第十九批：最后几处 `format!` 拼出来的界面文字（填充/描边工具提示、时间码基准、插值对话框计数）。

这些字是拼出来的，永远匹配不上翻译表，所以要改成 `tr_args`：表里的模板按 `{}` 占位，
英文界面下 `tr_args` 原样返回，行为不变。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH19_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH19_V1 — 最后几处拼字符串
    ("{} Options", "{}选项"),
    ("{}:", "{}："),
    ("{}: {}", "{}：{}"),
    ("Base {}{}", "基准 {}{}"),
    ("drop", "丢帧"),
    ("is {}  {}", "是 {}  {}"),
    ("{} keyframes selected", "已选 {} 个关键帧"),
    ("{} copy", "{} 副本"),
    ("{} copy {i}", "{} 副本 {i}"),
"""

EDITS: list[tuple[str, str, str, int]] = [
    # 填充/描边工具：标签、提示、下拉标题
    (
        "crates/ui-egui/src/header.rs",
        '        let options = format!("{title} Options");\n',
        '        let options = crate::i18n::tr_args("{} Options", &[&crate::i18n::tr(title)]);\n',
        1,
    ),
    (
        "crates/ui-egui/src/header.rs",
        '        let g = p.layout_no_wrap(format!("{title}:"), Tokens::ui(12.0), t.text_dim);\n',
        '        let g = p.layout_no_wrap(crate::i18n::tr_args("{}:", &[&crate::i18n::tr(title)]), Tokens::ui(12.0), t.text_dim);\n',
        1,
    ),
    (
        "crates/ui-egui/src/header.rs",
        '        let sresp = ui.interact(sr, egui::Id::unique(("tool-paint-swatch", key)), Sense::click()).on_hover_text(format!("{title}: {}", tp.kind.label()));\n',
        '        let sresp = ui.interact(sr, egui::Id::unique(("tool-paint-swatch", key)), Sense::click()).on_hover_text(crate::i18n::tr_args("{}: {}", &[&crate::i18n::tr(title), &crate::i18n::tr(tp.kind.label())]));\n',
        1,
    ),
    # 时间码输入框下面的「基准 24 丢帧 / 是 …」
    (
        "crates/ui-egui/src/panels/comp_settings.rs",
        '    let base = format!("Base {}{}", rate.timecode_base(), if df { "drop" } else { "" });\n'
        '    ui.label(egui::RichText::new(format!("is {shown}  {base}")).color(Color32::GRAY));\n',
        '    let base = crate::i18n::tr_args("Base {}{}", &[&rate.timecode_base(), &(if df { crate::i18n::tr("drop") } else { "" })]);\n'
        '    ui.label(egui::RichText::new(crate::i18n::tr_args("is {}  {}", &[&shown, &base])).color(Color32::GRAY));\n',
        1,
    ),
    # 关键帧插值对话框：「已选 N 个关键帧」
    (
        "crates/ui-egui/src/panels/key_dialogs.rs",
        '        ui.label(egui::RichText::new(format!("{} keyframe{} selected", d.count, if d.count == 1 { "" } else { "s" })).color(t.text_dim));\n',
        '        ui.label(egui::RichText::new(crate::i18n::tr_args("{} keyframes selected", &[&d.count])).color(t.text_dim));\n',
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
        src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH19_V1", 1)
        ui.write_text(src, encoding="utf-8")
        print("batch 19 rows added")
    for rel, old, new, want in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        got = text.count(old)
        if got != want:
            raise SystemExit(f"{rel}: anchor count {got} != {want}")
        path.write_text(text.replace(old, new, want), encoding="utf-8")
    print("batch 19 sites wired")


if __name__ == "__main__":
    main()
