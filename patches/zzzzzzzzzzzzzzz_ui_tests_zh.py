#!/usr/bin/env python3
"""Two UI tests that assert the English interface follow the Chinese one.

`shape_group_inner_contents_is_elided` compares the Timeline's rendered rows (now Chinese through
the property-name table) and `composition_settings_register_every_control…` expects the default
composition name ("Comp 3" → "合成 3"). The expected list is rebuilt from the name table itself, so
it stays right when a name is added. Runs last: it reads the table `70_property_names_zh` writes.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_UI_TESTS_ZH_V1"

TIMELINE_TEST = "fn shape_group_inner_contents_is_elided()"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    prop = (root / "crates/ui-egui/src/i18n/prop.rs").read_text(encoding="utf-8")
    table = dict(re.findall(r'"([^"]+)" => "([^"]+)"', prop))

    timeline = root / "crates/ui-egui/src/panels/timeline/tests.rs"
    src = timeline.read_text(encoding="utf-8")
    if MARKER not in src:
        start = src.index(TIMELINE_TEST)
        end = src.index("]);", start)
        block = src[start:end]

        def entry(m: re.Match) -> str:
            body = m.group(1)
            lead = len(body) - len(body.lstrip(" "))
            rest = body[lead:]
            arrow = ">" if rest.startswith(">") else ""
            rest = rest[len(arrow):]
            return '"' + " " * lead + arrow + table.get(rest, rest) + '"'

        new_block = re.sub(r'"([^"]*)"', entry, block)
        src = src[:start] + new_block + src[end:]
        timeline.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
        print("timeline label test expects Chinese rows")

    dialogs = root / "crates/ui-egui/src/panels/dialogs.rs"
    src = dialogs.read_text(encoding="utf-8")
    if '(1000, 500, 18.0, "Comp 3")' in src:
        dialogs.write_text(src.replace('(1000, 500, 18.0, "Comp 3")', '(1000, 500, 18.0, "合成 3")', 1), encoding="utf-8")
        print("comp settings test expects 合成 3")


if __name__ == "__main__":
    main()
