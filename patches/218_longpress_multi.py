#!/usr/bin/env python3
"""长按图层行 = 加选/取消（手机上没有 Cmd 键，用它代替 Cmd+点击）。

Selection already supports `toggle` and shift-ranges (engine `layer.select`), but on a phone there is
no modifier key. Holding a row for 450 ms while not moving toggles that layer in the selection; the
click that follows the release is swallowed so it cannot collapse the selection back to one layer.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LONGPRESS_MULTI_V1"

ANCHOR = '''    app.auto.add(&format!("timeline.layer.{}.row", layer.id.0), left, &layer.name);
    if row_resp.clicked() && !locked {
'''
NEW = '''    app.auto.add(&format!("timeline.layer.{}.row", layer.id.0), left, &layer.name);
    // EFFECTCRAFT_OURS_LONGPRESS_MULTI_V1 — 长按 450ms（几乎不移动）= 加选/取消
    let lp_start = egui::Id::new(("ours-lp-start", layer.id.0));
    let lp_fired = egui::Id::new(("ours-lp-fired", layer.id.0));
    let now = ui.input(|i| i.time);
    if row_resp.is_pointer_button_down_on() {
        let start: Option<f64> = ctx.data(|d| d.get_temp::<f64>(lp_start));
        let start = match start {
            Some(s) => s,
            None => {
                ctx.data_mut(|d| {
                    d.insert_temp(lp_start, now);
                    d.insert_temp(lp_fired, false);
                });
                now
            }
        };
        let fired: bool = ctx.data(|d| d.get_temp::<bool>(lp_fired)).unwrap_or(false);
        if !fired && now - start > 0.45 {
            ctx.data_mut(|d| d.insert_temp(lp_fired, true));
            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": true})));
        }
    }
    let lp_was_fired: bool = ctx.data(|d| d.get_temp::<bool>(lp_fired)).unwrap_or(false);
    if !row_resp.is_pointer_button_down_on() && !row_resp.clicked() {
        ctx.data_mut(|d| d.insert_temp(lp_start, now));
    }
    if row_resp.clicked() && !locked && !lp_was_fired {
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("long-press multi-select already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, NEW, 1), encoding="utf-8")
    print("long-press toggles selection")


if __name__ == "__main__":
    main()
