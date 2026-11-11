#!/usr/bin/env python3
"""The brand mark sits under the File menu, where a thumb lands. Require a double tap.

Only the hit test changes: the mark keeps its place, its icon and its tooltip, so the
original layout is untouched.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ABOUT_DOUBLE_TAP_V1"
OLD = 'if bresp.on_hover_text(tr("About EffectCraft")).clicked() {'
NEW = 'if bresp.on_hover_text(tr("About EffectCraft (double-tap)")).double_clicked() {'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    source = path.read_text(encoding="utf-8")
    if MARKER in source:
        print("About double-tap is already installed.")
        return
    if source.count(OLD) != 1:
        raise SystemExit(f"about handler: expected exactly one match, found {source.count(OLD)}")
    source = source.replace(OLD, f"// {MARKER}\n    {NEW}", 1)
    path.write_text(source, encoding="utf-8")
    print("About now opens on a double tap.")


if __name__ == "__main__":
    main()
