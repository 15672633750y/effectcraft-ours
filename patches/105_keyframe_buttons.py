#!/usr/bin/env python3
"""Text buttons in the toolbar: add a keyframe at the playhead, and open the easing presets."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_KEYFRAME_BUTTONS_V1"
ANCHOR = "    let x = export_button(app, ui, &p, x, cy);\n"
CALL = "    let x = keyframe_buttons(app, ui, &p, x, cy);\n"

CODE = r'''
// EFFECTCRAFT_OURS_KEYFRAME_BUTTONS_V1
fn keyframe_buttons(app: &mut EffectcraftApp, ui: &mut egui::Ui, p: &egui::Painter, x: f32, cy: f32) -> f32 {
    let t = app.tokens;
    let mut x = x;

    let add = Rect::from_min_size(pos2(x, cy - 13.0), vec2(88.0, 26.0));
    let add_resp = ui.interact(add, egui::Id::unique("ours-add-keyframe"), Sense::click());
    p.rect_filled(add, 4.0, t.switch_well);
    p.text(add.center(), Align2::CENTER_CENTER, "添加关键帧", Tokens::ui(12.0), t.text);
    if add_resp.clicked() {
        match app.session.state.selected_props.first().copied() {
            // Only the selected parameter gets a key, exactly like the stopwatch.
            Some((layer, uid)) => {
                let _ = crate::menus::invoke(
                    app,
                    ui.ctx(),
                    "prop.toggleKey",
                    serde_json::json!({"layer": layer.0, "uid": uid}),
                );
            }
            None => app.ui.status = "请选择目标后再点击关键帧".into(),
        }
    }
    x += 94.0;

    let curve = Rect::from_min_size(pos2(x, cy - 13.0), vec2(52.0, 26.0));
    let curve_resp = ui.interact(curve, egui::Id::unique("ours-curve-button"), Sense::click());
    p.rect_filled(curve, 4.0, t.switch_well);
    p.text(curve.center(), Align2::CENTER_CENTER, "曲线", Tokens::ui(12.0), t.text);
    if curve_resp.clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-curve-open"), true));
    }
    x += 58.0;

    curve_menu(app, ui.ctx());
    x
}

fn curve_menu(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let open_id = egui::Id::new("ours-curve-open");
    let mut open = ctx.data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    let mut close = false;
    egui::Window::new("曲线")
        .open(&mut open)
        .collapsible(false)
        .resizable(false)
        .show(ctx, |ui| {
            ui.label("缓动预设");
            ui.add_space(4.0);
            for (label, cmd) in [
                ("缓入缓出（Easy Ease）", "keys.easyEase"),
                ("缓入（Easy Ease In）", "keys.easyEaseIn"),
                ("缓出（Easy Ease Out）", "keys.easyEaseOut"),
                ("平滑（Smooth）", "keys.smooth"),
                ("定格（Hold）", "keys.toggleHold"),
            ] {
                if ui.button(label).clicked() {
                    let _ = crate::menus::invoke(app, ctx, cmd, serde_json::json!({}));
                    close = true;
                }
            }
        });
    ctx.data_mut(|d| d.insert_temp(open_id, open && !close));
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("keyframe buttons already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"export anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + CALL, 1)
    path.write_text(src + CODE, encoding="utf-8")
    print("keyframe and curve buttons installed")


if __name__ == "__main__":
    main()
