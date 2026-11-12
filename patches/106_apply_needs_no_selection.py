#!/usr/bin/env python3
"""Double-clicking an effect with nothing selected applies it to the topmost layer instead of doing nothing."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_APPLY_FALLBACK_V1"
OLD = """    if app.session.state.selected_layers.is_empty() {
        app.ui.status = "Select a layer to apply to".into();
        return;
    }
"""
NEW = """    if app.session.state.selected_layers.is_empty() {
        // Falling back to the topmost layer makes a double click always do something visible.
        let top = app.session.active_comp().and_then(|c| c.layers.first().map(|l| l.id));
        if let Some(id) = top {
            app.session.state.selected_layers = vec![id];
        }
        if app.session.state.selected_layers.is_empty() {
            app.ui.status = "请先新建或选中一个图层，再应用效果".into();
            return;
        }
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/effects_presets.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("apply fallback already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"apply guard anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("double click on an effect now applies to the topmost layer")


if __name__ == "__main__":
    main()
