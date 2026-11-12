#!/usr/bin/env python3
"""Fixed-width panels become ratios: the dividers drag again and the layout follows the screen."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RATIO_SPLITS_V1"
REPLACEMENTS = [
    ("FixedFirst(300.0)", "Ratio(0.22)"),
    ("FixedFirst(340.0)", "Ratio(0.25)"),
    ("FixedSecond(300.0)", "Ratio(0.78)"),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("split ratios already installed")
        return
    changed = 0
    for old, new in REPLACEMENTS:
        count = src.count(old)
        changed += count
        src = src.replace(old, new)
    if changed == 0:
        raise SystemExit("no fixed split sizes found")
    src = src.replace(
        "pub fn workspace(name: &str) -> Layout {",
        "// " + MARKER + "\n// Fixed-width panels could not be dragged; ratios both drag and adapt.\npub fn workspace(name: &str) -> Layout {",
        1,
    )
    path.write_text(src, encoding="utf-8")
    print(f"{changed} fixed panel widths became ratios")


if __name__ == "__main__":
    main()
