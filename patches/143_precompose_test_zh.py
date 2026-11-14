#!/usr/bin/env python3
"""The pre-compose naming test follows the localized default names.

`20_chinese_default_names.py` names new pre-comps 预合成 N (as the Simplified Chinese After Effects
does), so the engine's own test — which looked for "Pre-comp" — has to look for that name.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRECOMPOSE_TEST_ZH_V1"

EDITS = [
    ('.starts_with("Pre-comp")', '.starts_with("预合成")'),
    ('assert_eq!(names, ["Pre-comp 1", "Pre-comp 2"]);', 'assert_eq!(names, ["预合成 1", "预合成 2"]);'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/tests/menu_cmds.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("pre-compose test already localized")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
    print("pre-compose test expects 预合成")


if __name__ == "__main__":
    main()
