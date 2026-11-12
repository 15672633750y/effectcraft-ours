#!/usr/bin/env python3
"""Columns that the composition never uses (parent, matte) stay hidden instead of taking space."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HIDE_UNUSED_COLUMNS_V1"
OLD = """    if app.ui.timeline.show_modes && rc.layer.source.is_av() {
        layer_mode_cell(app, ui, g, rc);
        layer_matte_cell(app, ui, g, rc);
    }
    if g.tl.vis.parent {
        layer_parent_cell(app, ui, g, rc);
    }"""
NEW = """    // " + MARKER + "
    // Only show the matte and parent columns when the composition actually uses them.
    let any_matte = g.tl.comp.layers.iter().any(|l| l.track_matte.is_some());
    let any_parent = g.tl.comp.layers.iter().any(|l| l.parent.is_some());
    if app.ui.timeline.show_modes && rc.layer.source.is_av() {
        layer_mode_cell(app, ui, g, rc);
        if any_matte {
            layer_matte_cell(app, ui, g, rc);
        }
    }
    if g.tl.vis.parent && any_parent {
        layer_parent_cell(app, ui, g, rc);
    }"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("unused columns already hidden")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("matte and parent columns hide when unused")


if __name__ == "__main__":
    main()
