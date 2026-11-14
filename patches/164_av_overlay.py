#!/usr/bin/env python3
"""An extra hit layer over the eye and speaker of every layer row.

The row's own switches take their clicks through a shared press/drag handler; on the phone that
path does not receive taps on those two cells (the ones on the right of the row do). Instead of
touching that handler — two attempts at it crashed the app — this adds an *independent* thin
overlay on top of the two cells: a plain click region that runs the same command the app's own
switches run (`layer.setSwitch`), exactly like the toolbar's undo/redo buttons run theirs.

It covers a slightly larger area than the drawn cell, so a finger has room, and it changes nothing
else: no ids, no sense, no order of the existing widgets.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AV_OVERLAY_V1"

FUNC = '''
/// A separate click layer over the A/V cells: runs `layer.setSwitch` itself.
fn ours_av_overlay(app: &mut EffectcraftApp, ui: &mut egui::Ui, g: &mut Rw, rc: &RowCtx<'_>) {
    let cw = &g.tl.cw;
    let cy = rc.cy;
    let layer = rc.layer;
    let selected = app.session.state.selected_layers.clone();
    let ctx = ui.ctx().clone();
    for (i, (name, on)) in [("video", layer.switches.video), ("audio", layer.switches.audio)].iter().enumerate() {
        let br = Rect::from_center_size(pos2(cw.av + 9.0 + 17.0 * i as f32, cy), vec2(19.0, 23.0));
        let id = egui::Id::unique(("ours-av-hit", layer.id.0, i));
        let resp = ui.interact(br, id, Sense::click());
        let resp = resp.on_hover_text(if *name == "video" { "显示 / 隐藏" } else { "音频开 / 关" });
        if resp.clicked() {
            // 和软件自己的开关走同一个命令；有多个图层被选中时一起切。
            let layers = edited_layers(layer.id, &selected);
            let _ = crate::menus::invoke(app, &ctx, "layer.setSwitch", json!({"layers": layers, "switch": name, "value": !on}));
        }
    }
}
'''

CALL_OLD = '''    if g.tl.vis.parent {
        layer_parent_cell(app, ui, g, rc);
    }
'''
CALL_NEW = '''    if g.tl.vis.parent {
        layer_parent_cell(app, ui, g, rc);
    }
    // EFFECTCRAFT_OURS_AV_OVERLAY_V1 — 最后注册，压在上面，只负责眼睛/喇叭的点击
    if g.tl.vis.av {
        ours_av_overlay(app, ui, g, rc);
    }
'''

ANCHOR_FN = "/// The layer's duration bar: source extent, move and trim, markers.\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("A/V overlay already installed")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    if src.count(ANCHOR_FN) != 1:
        raise SystemExit(f"fn anchor: {src.count(ANCHOR_FN)}")
    src = src.replace(ANCHOR_FN, FUNC + "\n" + ANCHOR_FN, 1)
    path.write_text(src, encoding="utf-8")
    print("A/V overlay added")


if __name__ == "__main__":
    main()
