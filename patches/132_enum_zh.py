#!/usr/bin/env python3
"""Enum values in Chinese at the two widgets every combo box goes through.

Effect parameters pick from lists like `Result | Source`, `Luma | Alpha`, blend modes, light
types … 500 distinct labels in the registry, all English. Translating each draw site would miss
some, so the translation sits inside `widgets::dropdown` (the closed box) and
`widgets::popup_menu` (the open list): every label goes through the table, and the index that comes
back is still the original one.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ENUM_ZH_V1"

DROPDOWN_OLD = '''    let room = rect.width() - 7.0 - 18.0;
    let fits = |s: &str| ui.painter().layout_no_wrap(s.to_string(), Tokens::ui(11.5), t.text).size().x <= room;
    let shown = if fits(text) {
        text.to_string()
'''
DROPDOWN_NEW = '''    let room = rect.width() - 7.0 - 18.0;
    let fits = |s: &str| ui.painter().layout_no_wrap(s.to_string(), Tokens::ui(11.5), t.text).size().x <= room;
    // EFFECTCRAFT_OURS_ENUM_ZH_V1 — an enum value ("Result", "Luma", "Screen" …) shows in Chinese.
    let text = crate::i18n::tr(text);
    let shown = if fits(text) {
        text.to_string()
'''

POPUP_OLD = '''        for (i, o) in options.iter().enumerate() {
            if o == "-" {
                ui.separator();
            } else {
                let r = ui.selectable_label(current == Some(i), o);
'''
POPUP_NEW = '''        for (i, o) in options.iter().enumerate() {
            if o == "-" {
                ui.separator();
            } else {
                let shown = crate::i18n::tr(o);
                let r = ui.selectable_label(current == Some(i), shown);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/widgets.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("enum widgets already translated")
        return
    for old, new in ((DROPDOWN_OLD, DROPDOWN_NEW), (POPUP_OLD, POPUP_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    src = "// " + MARKER + "\n" + src
    path.write_text(src, encoding="utf-8")
    print("dropdown and popup labels go through the table")


if __name__ == "__main__":
    main()
