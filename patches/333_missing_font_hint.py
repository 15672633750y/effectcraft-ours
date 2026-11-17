#!/usr/bin/env python3
"""字体缺失提示：字符面板里选的字体没装时，字段角上打一个橙色小点，并在状态栏提示
「缺少字体「X」：把字体文件放到 /sdcard/Fonts/ 再重启应用」。

`/sdcard/Fonts` 与 `/storage/emulated/0/Fonts` 本来就是 builder 支持的用户字体目录
（builder/templates/android/system_fonts.rs 的 USER_FONT_DIRS），所以提示是能兑现的。
同一个字体只提示一次，避免每帧刷状态栏。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MISSING_FONT_HINT_V1"

ANCHOR = '    app.auto.add(auto, rect, "Font family");\n'

INSERT = r'''    // EFFECTCRAFT_OURS_MISSING_FONT_HINT_V1 — 字体没装：角上打点 + 状态栏告诉用户把字体放到 /sdcard/Fonts/
    if !current.is_empty() && !effectcraft_engine::text_families().iter().any(|f| f.eq_ignore_ascii_case(current)) {
        let t = app.tokens;
        ui.painter().circle_filled(pos2(rect.max.x - 5.0, rect.min.y + 5.0), 3.0, t.warning);
        let key = egui::Id::new(("font-missing", current.to_ascii_lowercase()));
        if !ui.data(|d| d.get_temp::<bool>(key).unwrap_or(false)) {
            ui.data_mut(|d| d.insert_temp(key, true));
            app.ui.status = crate::i18n::tr_args(
                "Missing font {}: put the font file in /sdcard/Fonts/ and restart the app.",
                &[&current],
            );
        }
    }
'''

UI_ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

UI_ROWS = """    // EFFECTCRAFT_OURS_MISSING_FONT_HINT_V1 — 字体缺失提示
    ("Missing font {}: put the font file in /sdcard/Fonts/ and restart the app.", "缺少字体「{}」：把字体文件放到 /sdcard/Fonts/ 再重启应用。"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    panels = root / "crates/ui-egui/src/panels/text_panels.rs"
    src = panels.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(ANCHOR) != 1:
            raise SystemExit(f"font_picker anchor: {src.count(ANCHOR)}")
        panels.write_text(src.replace(ANCHOR, ANCHOR + INSERT, 1), encoding="utf-8")
        print("missing-font hint added to font_picker")

    ui = root / "crates/ui-egui/src/i18n/ui.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(UI_ANCHOR) != 1:
            raise SystemExit(f"ui anchor: {src.count(UI_ANCHOR)}")
        src = src.replace(UI_ANCHOR, UI_ROWS + UI_ANCHOR + "\n// EFFECTCRAFT_OURS_MISSING_FONT_HINT_V1", 1)
        ui.write_text(src, encoding="utf-8")
        print("missing-font rows added")


if __name__ == "__main__":
    main()
