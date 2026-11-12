#!/usr/bin/env python3
"""Double-clicking footage or a solid adds it to the active composition instead of only opening it."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DOUBLECLICK_MEDIA_V1"
OLD = """        // Footage (not data) and solids open in the Footage panel.
        ItemKind::Footage(f) if f.kind != effectcraft_engine::project::FootageKind::Data => actions.push(("footage.open".into(), json!({"item": id.0}))),
        ItemKind::Solid(_) => actions.push(("footage.open".into(), json!({"item": id.0}))),
"""
NEW = """        // With a composition open, a double click puts the footage on top of it; without one it
        // still opens the Footage panel.
        ItemKind::Footage(f) if f.kind != effectcraft_engine::project::FootageKind::Data => {
            if app.session.active_comp_id().is_some() {
                actions.push(("layer.addItem".into(), json!({"item": id.0, "index": 0})));
            } else {
                actions.push(("footage.open".into(), json!({"item": id.0})));
            }
        }
        ItemKind::Solid(_) => {
            if app.session.active_comp_id().is_some() {
                actions.push(("layer.addItem".into(), json!({"item": id.0, "index": 0})));
            } else {
                actions.push(("footage.open".into(), json!({"item": id.0})));
            }
        }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/project.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("double-click add already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"open_item anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace("fn open_item(", "// " + MARKER + "\nfn open_item(", 1)
    path.write_text(src, encoding="utf-8")
    print("double-clicking footage adds it to the active composition")


if __name__ == "__main__":
    main()
