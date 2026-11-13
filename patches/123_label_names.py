#!/usr/bin/env python3
"""Label names in Chinese: Red, Yellow, Aqua … were the last English list in Settings ▸ Labels.

The names are stored data (a label can be renamed), so the engine keeps them verbatim and only the
drawing goes through the interface language: `i18n::label_name` looks the stored English name up
and falls back to it, which is what a renamed label should do.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LABEL_NAMES_ZH_V1"

HELPER = '''
/// A label's name in the interface language. The stored names are English by default (Red,
/// Yellow, …) and a renamed label falls back to what it was renamed to.
pub fn label_name(name: &str) -> String {
    tr(name).to_string()
}
'''

CALL = "crate::i18n::label_name(&app.session.prefs.label_name("

SITES = [
    ("crates/ui-egui/src/panels/effect_controls/panel.rs", [
        ("&app.session.prefs.label_name(lab),", "&" + CALL + "lab)),"),
        ("&app.session.prefs.label_name(l), l == cur, &t", "&" + CALL + "l)), l == cur, &t"),
    ]),
    ("crates/ui-egui/src/panels/markers_ui.rs", [
        ("selected_text(app.session.prefs.label_name(cur))", "selected_text(" + CALL + "cur)))"),
        ("&app.session.prefs.label_name(l), d.label == i, &app.tokens", "&" + CALL + "l)), d.label == i, &app.tokens"),
    ]),
    ("crates/ui-egui/src/panels/project.rs", [
        ("&app.session.prefs.label_name(l), l == it.label, &t", "&" + CALL + "l)), l == it.label, &t"),
        ("&[&it.name, &app.session.prefs.label_name(it.label)]", "&[&it.name, &" + CALL + "it.label))]"),
        ("|l| app.session.prefs.label_name(l), &t", "|l| " + CALL + "l)), &t"),
    ]),
    ("crates/ui-egui/src/panels/timeline.rs", [
        ("|l| app.session.prefs.label_name(l), &t", "|l| " + CALL + "l)), &t"),
        ("&app.session.prefs.label_name(lab));", "&" + CALL + "lab)));"),
        ("&app.session.prefs.label_name(l), k.label as usize == i, &t", "&" + CALL + "l)), k.label as usize == i, &t"),
    ]),
]

ROWS = """
    ("Red", "红"),
    ("Yellow", "黄"),
    ("Aqua", "青"),
    ("Pink", "粉"),
    ("Lavender", "淡紫"),
    ("Peach", "桃"),
    ("Sea Foam", "海沫"),
    ("Blue", "蓝"),
    ("Purple", "紫"),
    ("Green", "绿"),
    ("Orange", "橙"),
    ("Fuchsia", "洋红"),
    ("Brown", "棕"),
    ("Cyan", "青蓝"),
    ("Sandstone", "砂岩"),
    ("Dark Green", "墨绿"),
"""

TABLE_ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    i18n = root / "crates/ui-egui/src/i18n.rs"
    src = i18n.read_text(encoding="utf-8")
    if MARKER not in src:
        anchor = "pub(crate) use ui::{set_current, tr, tr_args};\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"i18n anchor: expected 1, found {src.count(anchor)}")
        src = src.replace(anchor, anchor + "// " + MARKER + HELPER, 1)
        i18n.write_text(src, encoding="utf-8")
        print("i18n::label_name added")

    table = root / "crates/ui-egui/src/i18n/ui.rs"
    t = table.read_text(encoding="utf-8")
    if '("Dark Green", "墨绿")' not in t:
        if t.count(TABLE_ANCHOR) != 1:
            raise SystemExit(f"table anchor: expected 1, found {t.count(TABLE_ANCHOR)}")
        table.write_text(t.replace(TABLE_ANCHOR, TABLE_ANCHOR + ROWS, 1), encoding="utf-8")
        print("label names translated")

    for rel, subs in SITES:
        path = root / rel
        s = path.read_text(encoding="utf-8")
        changed = False
        for old, new in subs:
            if new in s or old not in s:
                continue
            s = s.replace(old, new, 1)
            changed = True
        if changed:
            path.write_text(s, encoding="utf-8")
            print(f"{rel}: label names go through the table")


if __name__ == "__main__":
    main()
