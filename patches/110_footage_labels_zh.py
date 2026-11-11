#!/usr/bin/env python3
"""Chinese labels for the two edit-mode buttons at the bottom right."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FOOTAGE_LABELS_V1"
EDITS = [
    ('"footage.rippleInsertEdit", "Ripple Insert Edit"', '"footage.rippleInsertEdit", "波纹插入编辑"'),
    ('"footage.overlayEdit", "Overlay Edit"', '"footage.overlayEdit", "覆盖编辑"'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/footage_panel.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("footage labels already localized")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"{old}: expected 1 match, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(f"// {MARKER}\n{src}", encoding="utf-8")
    print("edit-mode buttons are Chinese now")


if __name__ == "__main__":
    main()
