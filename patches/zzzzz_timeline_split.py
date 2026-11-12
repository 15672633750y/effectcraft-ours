#!/usr/bin/env python3
"""Drag the timeline's name column edge: the track area takes the rest and adapts."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_SPLIT_V1"

TL_DECL = '''
// EFFECTCRAFT_OURS_TIMELINE_SPLIT_V1
thread_local! {
    /// Extra width the user dragged onto the timeline's name column.
    static NAME_EXTRA: std::cell::Cell<f32> = const { std::cell::Cell::new(0.0) };
}
'''

COLS_OLD = "    let name_w = (width - vis.fixed()).max(120.0);"
COLS_NEW = "    let name_w = (width - vis.fixed() + NAME_EXTRA.with(|c| c.get())).max(120.0);"

EDGE_OLD = "    let cw = &g.cw;\n    let actions = &mut g.actions;\n    let ch = Rect::from_min_max(pos2(rect.min.x, top + header_h), pos2(rect.max.x, top + header_h + colhdr_h));\n"
EDGE_NEW = EDGE_OLD + '''    // The name column edge drags: the track area below adapts to whatever is left.
    let edge = Rect::from_center_size(pos2(cw.name_end - 1.0, ch.center().y), vec2(14.0, ch.height()));
    let edge_resp = ui.interact(edge, egui::Id::unique("tl-name-edge"), Sense::click_and_drag());
    if edge_resp.hovered() || edge_resp.dragged() {
        ui.ctx().set_cursor_icon(egui::CursorIcon::ResizeColumn);
    }
    if edge_resp.dragged() {
        NAME_EXTRA.with(|c| c.set((c.get() + edge_resp.drag_delta().x).clamp(-700.0, 700.0)));
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("timeline splitter already installed")
        return
    for old, new in ((COLS_OLD, COLS_NEW), (EDGE_OLD, EDGE_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor: expected 1, found {src.count(old)}: {old[:40]}")
        src = src.replace(old, new, 1)
    src = TL_DECL + src
    path.write_text(src, encoding="utf-8")
    print("timeline name column edge is draggable")


if __name__ == "__main__":
    main()
