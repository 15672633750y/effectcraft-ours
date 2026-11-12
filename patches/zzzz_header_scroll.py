#!/usr/bin/env python3
"""Let the tool row slide sideways: drag the empty part of the header to scroll it."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HEADER_SCROLL_V1"
OLD = """    let x = brand_and_home(app, ui, &p, x, cy);
    let x = tool_slots(app, ui, &p, x, cy);
"""
NEW = """    let x = brand_and_home(app, ui, &p, x, cy);
    // The tool row can slide sideways: many buttons do not fit a phone width.
    let scroll_id = egui::Id::new("ours-header-scroll");
    let mut scroll = ui.ctx().data(|d| d.get_temp::<f32>(scroll_id).unwrap_or(0.0));
    let pan = Rect::from_min_max(pos2(x + 90.0, rect.min.y), pos2(rect.max.x - 320.0, rect.max.y));
    let pan_resp = ui.interact(pan, egui::Id::unique("ours-header-pan"), Sense::drag());
    if pan_resp.dragged() {
        // Dragging left reveals what is off the right edge, so the offset is negative.
        scroll = (scroll - pan_resp.drag_delta().x).clamp(-1400.0, 0.0);
        ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
    }
    // Two step buttons at a fixed spot, because a drag is hard to start once buttons fill the row.
    for (dx, label, delta) in [(0.0, "‹", 140.0), (30.0, "›", -140.0)] {
        let r = Rect::from_min_size(pos2(rect.max.x - 330.0 + dx, rect.min.y + 12.0), vec2(26.0, 26.0));
        let resp = ui.interact(r, egui::Id::unique(("ours-header-step", label)), Sense::click());
        ui.painter().rect_filled(r, 4.0, t.switch_well);
        ui.painter().text(r.center(), Align2::CENTER_CENTER, label, Tokens::ui(14.0), t.text);
        if resp.clicked() {
            scroll = (scroll + delta).clamp(-1400.0, 0.0);
            ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
        }
    }
    let x = x + scroll;
    let x = tool_slots(app, ui, &p, x, cy);
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("header scroll already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"header anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    src = src.replace("pub fn show(app: &mut EffectcraftApp", "// " + MARKER + "\npub fn show(app: &mut EffectcraftApp", 1)
    path.write_text(src, encoding="utf-8")
    print("tool row scrolls by dragging the header")


if __name__ == "__main__":
    main()
