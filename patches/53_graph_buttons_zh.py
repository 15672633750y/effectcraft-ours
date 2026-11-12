#!/usr/bin/env python3
"""Graph editor toolbar labels in Chinese: Value / Speed / Selected / Auto-zoom / Fit."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GRAPH_BUTTONS_V1"
EDITS = [
    ('label: "Value"', 'label: "数值"'),
    ('label: "Speed"', 'label: "速度"'),
    ('label: "Selected"', 'label: "仅选中"'),
    ('label: "Auto-zoom"', 'label: "自动缩放"'),
    ('label: "Fit Selection"', 'label: "适合选中"'),
    ('label: "Fit"', 'label: "适合"'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/graph.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("graph buttons already translated")
        return
    changed = 0
    for old, new in EDITS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
    if changed < 4:
        raise SystemExit(f"only {changed} graph labels matched")
    src = src.replace("fn text_button(", "// " + MARKER + "\nfn text_button(", 1)
    path.write_text(src, encoding="utf-8")
    print(f"{changed} graph toolbar labels translated")


if __name__ == "__main__":
    main()
