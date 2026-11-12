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

    let add = Rect::from_min_size(pos2(x, cy - 13.0), vec2(78.0, 26.0));
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
                    serde_json::json!({"layer": layer.0, "prop": uid}),
                );
            }
            None => app.ui.status = "请选择目标后再点击关键帧".into(),
        }
    }
    x += 82.0;

    let curve = Rect::from_min_size(pos2(x, cy - 13.0), vec2(44.0, 26.0));
    let curve_resp = ui.interact(curve, egui::Id::unique("ours-curve-button"), Sense::click());
    p.rect_filled(curve, 4.0, t.switch_well);
    p.text(curve.center(), Align2::CENTER_CENTER, "曲线", Tokens::ui(12.0), t.text);
    if curve_resp.clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-curve-open"), true));
    }
    x += 50.0;

    curve_menu(app, ui.ctx());
    x += 4.0;

    let undo_ready = !app.session.history.undo.is_empty();
    let redo_ready = !app.session.history.redo.is_empty();
    for (label, cmd, tip, ready) in [
        ("⟲", "edit.undo", "撤销", undo_ready),
        ("⟳", "edit.redo", "恢复", redo_ready),
    ] {
        let r = Rect::from_min_size(pos2(x, cy - 15.0), vec2(34.0, 28.0));
        let resp = ui.interact(r, egui::Id::unique(("ours-history", cmd)), Sense::click());
        p.rect_filled(r, 5.0, t.switch_well);
        let tint = if ready { t.text } else { t.text_faint };
        // The curved arrows are drawn as vectors: the bundled font has no ↶/↷ glyph, and a
        // missing glyph would show as a narrow box.
        let _ = label;
        draw_history_arrow(&p, r.center(), r.width() * 0.32, cmd == "edit.redo", tint);
        let resp = resp.on_hover_text(tip);
        if resp.clicked() && ready {
            if crate::menus::invoke(app, ui.ctx(), cmd, serde_json::json!({})).is_ok() {
                app.ui.status = if cmd == "edit.undo" { "已撤销".into() } else { "已恢复".into() };
            }
        }
        x += 38.0;
    }
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

/// A curved undo (or, mirrored, redo) arrow drawn with lines, so it never depends on a font glyph.
fn draw_history_arrow(p: &egui::Painter, c: egui::Pos2, rad: f32, mirror: bool, color: egui::Color32) {
    // A thin hook: most of a ring, open at the bottom, with a short diagonal tip.
    let stroke = egui::Stroke::new(1.8, color);
    let sign = if mirror { -1.0 } else { 1.0 };
    let mut pts: Vec<egui::Pos2> = Vec::new();
    let steps = 22;
    for i in 0..=steps {
        let t = i as f32 / steps as f32;
        let a = std::f32::consts::PI * (0.08 + 1.05 * t);
        pts.push(pos2(c.x + sign * rad * a.sin(), c.y + rad * 0.78 * a.cos()));
    }
    p.add(egui::Shape::line(pts.clone(), stroke));
    let tip = pts[pts.len() - 1];
    let prev = pts[pts.len() - 2];
    let dir = (tip - prev).normalized();
    let hook = egui::vec2(-dir.y, dir.x) * (rad * 0.55);
    p.add(egui::Shape::line(vec![tip, tip + hook], stroke));
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
