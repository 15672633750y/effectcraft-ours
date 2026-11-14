#!/usr/bin/env python3
"""Timeline property rows in Chinese, and the two UI tests that assert the old English names.

`prop_name` painted `prop.name` straight to the painter, so every row in the Timeline (Size,
Position, Anchor Point …) stayed English however complete the table was. Only the drawing changes:
the stored name is what expressions address.

The tests follow: `shape_group_inner_contents_is_elided` compares the rendered rows (now Chinese)
and `composition_settings_register_every_control…` expects the default name 合成 3. Runs last: it
reads the name table `70_property_names_zh` writes.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TL_PROP_ZH_V1"
TIMELINE_TEST = "fn shape_group_inner_contents_is_elided()"

PROP_OLD = '    let pname = if prop.has_expression() { format!("{base}  =") } else { base };\n'
PROP_NEW = '''    // EFFECTCRAFT_OURS_TL_PROP_ZH_V1 — 只翻显示；存储名（表达式用的）保持英文
    let shown = crate::i18n::prop::name(&base, "").to_string();
    let pname = if prop.has_expression() { format!("{shown}  =") } else { shown };
'''

# The rows the Timeline renders for a default shape layer (English, before the table).
ROWS = [
    "形状图层 1",
    "  >Contents",
    "    >Rectangle 1",
    "      >Rectangle Path 1",
    "        Size",
    "        Position",
    "        Roundness",
    "        Per-Corner Roundness",
    "        Top Left Roundness",
    "        Top Right Roundness",
    "        Bottom Right Roundness",
    "        Bottom Left Roundness",
    "      >Fill 1",
    "        Composite",
    "        Fill Rule",
    "        Color",
    "        Opacity",
    "      >Transform",
    "        Anchor Point",
    "        Position",
    "        Scale",
    "        Skew",
    "        Skew Axis",
    "        Rotation",
    "        Opacity",
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    prop = (root / "crates/ui-egui/src/i18n/prop.rs").read_text(encoding="utf-8")
    table = dict(re.findall(r'"([^"]+)" => "([^"]+)"', prop))

    timeline = root / "crates/ui-egui/src/panels/timeline.rs"
    src = timeline.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(PROP_OLD) != 1:
            raise SystemExit(f"prop_name anchor: {src.count(PROP_OLD)}")
        timeline.write_text(src.replace(PROP_OLD, PROP_NEW, 1), encoding="utf-8")
        print("timeline property rows go through the table")

    def shown(row: str) -> str:
        lead = len(row) - len(row.lstrip(" "))
        rest = row[lead:]
        arrow = ">" if rest.startswith(">") else ""
        rest = rest[len(arrow):]
        return " " * lead + arrow + table.get(rest, rest)

    tests = root / "crates/ui-egui/src/panels/timeline/tests.rs"
    src = tests.read_text(encoding="utf-8")
    start = src.index(TIMELINE_TEST)
    open_at = src.index("labels(&app),", start)
    begin = src.index("[", open_at)
    end = src.index("]", begin)
    body = "[\n" + "".join(f'            "{shown(r)}",\n' for r in ROWS) + "        "
    src = src[:begin] + body + src[end:]
    tests.write_text(src, encoding="utf-8")
    print("timeline label test rebuilt from the table")

    dialogs = root / "crates/ui-egui/src/panels/dialogs.rs"
    src = dialogs.read_text(encoding="utf-8")
    if '(1000, 500, 18.0, "Comp 3")' in src:
        dialogs.write_text(src.replace('(1000, 500, 18.0, "Comp 3")', '(1000, 500, 18.0, "合成 3")', 1), encoding="utf-8")
        print("comp settings test expects 合成 3")


if __name__ == "__main__":
    main()
