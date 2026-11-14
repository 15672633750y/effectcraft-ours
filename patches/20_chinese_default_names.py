#!/usr/bin/env python3
"""Default names in Chinese, the way the localized After Effects names them.

The only `String::from("Comp 1")` in widgets.rs belongs to a text-editing test (it just needs a
six-character string), so it is left alone: editing it turned that test's fixture Chinese and its
6-character assertion failed.


A new composition starts as 合成 1 and a pre-composition as 预合成 1; the engine still
appends the next free number, so nothing about uniqueness changes.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CHINESE_DEFAULT_NAMES_V1"
EDITS = [
    ("crates/ui-egui/src/panels/comp_settings.rs",
     'name: "Comp 1".into(),', 'name: "合成 1".into(),'),
    ("crates/engine/src/cmd/comp.rs",
     '.unwrap_or("Comp 1")', '.unwrap_or("合成 1")'),
    ("crates/engine/src/cmd/layer/timing.rs",
     'format!("Pre-comp {n}")', 'format!("预合成 {n}")'),
    ("crates/engine/src/cmd/layer/timing.rs",
     '"Pre-comp".to_string()', '"预合成".to_string()'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    for rel, old, new in EDITS:
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        source = path.read_text(encoding="utf-8")
        if MARKER in source:
            continue
        count = source.count(old)
        if count != 1:
            raise SystemExit(f"{rel}: expected one {old!r}, found {count}")
        source = source.replace(old, f"/* {MARKER} */ {new}" if False else new, 1)
        path.write_text(source, encoding="utf-8")
        print(f"{rel}: {old} -> {new}")


if __name__ == "__main__":
    main()
