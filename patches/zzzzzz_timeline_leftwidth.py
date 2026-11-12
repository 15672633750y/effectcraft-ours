#!/usr/bin/env python3
"""The divider between the timeline's layer columns and the tracks drags; the tracks adapt."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_LEFTWIDTH_V1"

DECL = '''
// EFFECTCRAFT_OURS_TIMELINE_LEFTWIDTH_V1
thread_local! {
    /// How far the user moved the divider between the layer columns and the tracks.
    static LEFT_EXTRA: std::cell::Cell<f32> = const { std::cell::Cell::new(0.0) };
}
'''

OLD_W = "    let left_w = (vis.fixed() + 190.0).clamp(420.0, (rect.width() * 0.72).max(420.0));"
NEW_W = "    let left_w = (vis.fixed() + 190.0 + LEFT_EXTRA.with(|c| c.get())).clamp(220.0, (rect.width() * 0.9).max(220.0));"

OLD_G = "    let graph_x0 = rect.min.x + left_w + 1.0;\n"
NEW_G = OLD_G + '''    // The handle lives in a foreground area: the rows underneath would otherwise take the press.
    egui::Area::new(egui::Id::unique("tl-left-split"))
        .order(egui::Order::Foreground)
        .fixed_pos(pos2(graph_x0 - 6.0, rect.min.y))
        .show(ui.ctx(), |area_ui| {
            let (handle, resp) = area_ui.allocate_exact_size(vec2(12.0, rect.height()), Sense::drag());
            if resp.hovered() || resp.dragged() {
                area_ui.ctx().set_cursor_icon(egui::CursorIcon::ResizeColumn);
            }
            if resp.dragged() {
                LEFT_EXTRA.with(|c| c.set((c.get() + resp.drag_delta().x).clamp(-600.0, 900.0)));
            }
            if resp.hovered() {
                area_ui.painter().rect_filled(handle, 0.0, app.tokens.accent.gamma_multiply(0.35));
            }
        });
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("timeline divider already draggable")
        return
    for old, new in ((OLD_W, NEW_W), (OLD_G, NEW_G)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor: expected 1, found {src.count(old)}: {old[:44]}")
        src = src.replace(old, new, 1)
    if src.count("struct Cols {") != 1:
        raise SystemExit("Cols anchor missing")
    src = src.replace("struct Cols {", DECL + "\nstruct Cols {", 1)
    path.write_text(src, encoding="utf-8")
    print("timeline divider drags (foreground handle) and the tracks adapt")


if __name__ == "__main__":
    main()
