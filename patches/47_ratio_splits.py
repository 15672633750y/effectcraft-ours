#!/usr/bin/env python3
"""Fixed-width panels become ratios: the dividers drag again and the layout follows the screen."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RATIO_SPLITS_V1"
REPLACEMENTS = [
    ("FixedFirst(300.0)", "FixedFirst(190.0)"),
    ("FixedFirst(340.0)", "FixedFirst(200.0)"),
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
    print(f"{changed} panels set: left column fixed and narrow, right column proportional")

    # Existing installs keep their saved layout; offer the new one by bumping the snapshot
    # version, which makes the app fall back to the defaults below.
    state = root / "crates/ui-egui/src/workspace_state.rs"
    src = state.read_text(encoding="utf-8")
    if "const VERSION: u32 = 2;" in src:
        state.write_text(src.replace("const VERSION: u32 = 2;", "const VERSION: u32 = 3;", 1), encoding="utf-8")
        print("workspace snapshot version bumped, saved layouts are rebuilt")


if __name__ == "__main__":
    main()
