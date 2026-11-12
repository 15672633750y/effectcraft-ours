#!/usr/bin/env python3
"""The 3D switch only shows on layers that are already 3D, so unused columns free the space."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HIDE_UNUSED_SWITCH_V1"
OLD = '        (Icon::Cube, layer.is_3d(), "threeD", switch_applies(layer, "threeD", &app.session.project)),'
NEW = '        // ' + MARKER + '\n        (Icon::Cube, layer.is_3d(), "threeD", layer.is_3d() && switch_applies(layer, "threeD", &app.session.project)),'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("3D switch already conditional")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("the 3D switch shows only on 3D layers")


if __name__ == "__main__":
    main()
