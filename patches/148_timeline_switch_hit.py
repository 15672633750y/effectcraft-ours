#!/usr/bin/env python3
"""The A/V switches (the eye and the speaker at the start of a layer row) could not be tapped.

Two reasons, both in `layer_switch`'s callers:

* the left-hand switches are registered first in the row, so the row's own select/drag area sits
  above them — the same switches on the right of the row are registered last and work;
* a primary pointer click was only handled by `switch_gesture` (the press), and the fallback
  explicitly skipped the primary button (`!resp.clicked_by(Primary)`), so when the press did not
  reach the switch the release did nothing at all — silently.

Now the A/V switches are registered last in the row (on top of the row area, like the right-hand
ones), every switch takes clicks from a hit area a few points larger than the drawn well (15 px is
a fingernail), and a click that the press path missed still toggles — once, because a stamp keeps
the release of the same press from toggling it back.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SWITCH_HIT_V1"

ROW_OLD = """    layer_row_background(g, rc);
    layer_av_switches(app, ui, g, rc);
    layer_label_swatch(app, ui, g, rc);
"""
ROW_NEW = """    layer_row_background(g, rc);
    layer_label_swatch(app, ui, g, rc);
"""

SWITCH_TAIL_OLD = """    layer_row_actions(app, ui, g, rc, &row_resp);
    layer_switches(app, ui, g, rc);
"""
SWITCH_TAIL_NEW = """    layer_row_actions(app, ui, g, rc, &row_resp);
    layer_switches(app, ui, g, rc);
    // EFFECTCRAFT_OURS_SWITCH_HIT_V1 — 最后注册：压在整行拖拽区上面，手指点得到（和右侧开关一致）
    layer_av_switches(app, ui, g, rc);
"""

TOGGLE_OLD = """    let resp = widgets::icon_toggle(ui, br, icon, on, t, id, Sense::click_and_drag());
"""
TOGGLE_NEW = """    // EFFECTCRAFT_OURS_SWITCH_HIT_V1
    // 画的是 15px 的井，接的是大一圈的命中框：手机上 15px 只有指甲盖大。
    let hit = br.expand2(vec2(3.5, 4.0));
    let resp = ui.interact(hit, id, Sense::click());
    if resp.hovered() {
        ui.painter().rect_filled(br, 2.0, t.hover);
    }
    if on || resp.hovered() {
        icons::paint(ui.painter(), br.shrink(br.width() * 0.18), icon, if on { t.icon } else { t.text_faint });
    }
    widgets::focus_outline(ui, &resp, t);
    let press_stamp = egui::Id::new(("sw-press-at", id));
"""

CLICK_OLD = """    } else if resp.clicked() && !resp.clicked_by(egui::PointerButton::Primary) {
        // Keyboard or accessibility activation (a pointer press was handled above).
        let layers = switch_targets(comp, project, selected, layer, name);
        actions.push(("layer.setSwitch".into(), json!({"layers": layers, "switch": name, "value": !on})));
    }
"""
CLICK_NEW = """    } else if resp.clicked() {
        // The press path above missed this click (a covering widget, a tap that landed a hair
        // late). The release still has to do something — but not when the press already did,
        // or one tap would flip the switch twice.
        let already = ui.data(|d| d.get_temp::<f64>(press_stamp)).is_some_and(|at| ui.input(|i| i.time) - at < 2.0);
        if !already {
            let layers = switch_targets(comp, project, selected, layer, name);
            actions.push(("layer.setSwitch".into(), json!({"layers": layers, "switch": name, "value": !on})));
        }
    }
"""

STAMP_OLD = """    if let Some((value, merge)) = switch_gesture(ui, &resp, row, name, on) {
        let layers = switch_targets(comp, project, selected, layer, name);
"""
STAMP_NEW = """    if let Some((value, merge)) = switch_gesture(ui, &resp, row, name, on) {
        ui.data_mut(|d| d.insert_temp(press_stamp, ui.input(|i| i.time)));
        let layers = switch_targets(comp, project, selected, layer, name);
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("switch hit areas already fixed")
        return
    for old, new in ((ROW_OLD, ROW_NEW), (SWITCH_TAIL_OLD, SWITCH_TAIL_NEW), (TOGGLE_OLD, TOGGLE_NEW), (STAMP_OLD, STAMP_NEW), (CLICK_OLD, CLICK_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:40]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("A/V switches: registered last, bigger hit area, click fallback")


if __name__ == "__main__":
    main()
