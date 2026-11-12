#!/usr/bin/env python3
"""Bigger switch icons and a forgiving hit area, so small toggles (fx, eye, lock) are easy to tap."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FX_HIT_V1"


def replace_once(text: str, old: str, new: str, what: str) -> str:
    found = text.count(old)
    if found != 1:
        raise SystemExit(f"{what}: expected 1 match, found {found}")
    return text.replace(old, new, 1)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    widgets = root / "crates/ui-egui/src/widgets.rs"
    src = widgets.read_text(encoding="utf-8")
    if MARKER not in src:
        src = replace_once(
            src,
            "pub fn icon_toggle(ui: &mut Ui, rect: Rect, icon: Icon, on: bool, t: &Tokens, id: egui::Id, sense: Sense) -> Response {\n    let resp = ui.interact(rect, id, sense);",
            "pub fn icon_toggle(ui: &mut Ui, rect: Rect, icon: Icon, on: bool, t: &Tokens, id: egui::Id, sense: Sense) -> Response {\n    // " + MARKER + "\n    // The drawn icon stays the same size; only the touch target grows, which matters on a phone.\n    let resp = ui.interact(rect.expand(3.0), id, sense);",
            "icon_toggle hit area",
        )
        widgets.write_text(src, encoding="utf-8")
        print("switch hit areas are 3px larger on every side")

    timeline = root / "crates/ui-egui/src/panels/timeline.rs"
    tl = timeline.read_text(encoding="utf-8")
    if "const SW: f32 = 30.0;" in tl:
        tl = tl.replace("const SW: f32 = 30.0;", "const SW: f32 = 34.0;", 1)
        print("switch column is 34px wide")
    if "vec2(26.0, 26.0)" in tl:
        tl = tl.replace("vec2(26.0, 26.0)", "vec2(30.0, 30.0)", 1)
        print("switch icons are 30px")
    timeline.write_text(tl, encoding="utf-8")


if __name__ == "__main__":
    main()
