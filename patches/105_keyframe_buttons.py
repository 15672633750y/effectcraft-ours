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
    let t = app.tokens;
    let mut close = false;
    egui::Window::new("曲线")
        .open(&mut open)
        .collapsible(false)
        .resizable(false)
        .show(ctx, |ui| {
            ui.label("缓动预设（点击应用）");
            ui.add_space(4.0);
            let presets: [(&str, &str, u8); 5] = [
                ("缓入缓出", "keys.easyEase", 0),
                ("缓入", "keys.easyEaseIn", 1),
                ("缓出", "keys.easyEaseOut", 2),
                ("平滑", "keys.smooth", 3),
                ("定格", "keys.toggleHold", 4),
            ];
            ui.horizontal_wrapped(|ui| {
                for (label, cmd, kind) in presets {
                    let (rect, resp) = ui.allocate_exact_size(vec2(66.0, 76.0), Sense::click());
                    let bg = if resp.hovered() { t.hover } else { t.switch_well };
                    ui.painter().rect_filled(rect, 5.0, bg);
                    let plot = Rect::from_min_size(rect.min + vec2(9.0, 8.0), vec2(46.0, 42.0));
                    draw_ease_curve(ui.painter(), plot, kind, t.text);
                    ui.painter().text(
                        pos2(rect.center().x, rect.max.y - 13.0),
                        Align2::CENTER_CENTER,
                        label,
                        Tokens::ui(11.0),
                        t.text,
                    );
                    if resp.on_hover_text(label).clicked() {
                        let _ = crate::menus::invoke(app, ctx, cmd, serde_json::json!({}));
                        close = true;
                    }
                }
            });
        });
    ctx.data_mut(|d| d.insert_temp(open_id, open && !close));
}

/// A thumbnail of an easing curve: the shape is what makes the preset recognisable.
fn draw_ease_curve(p: &egui::Painter, r: Rect, kind: u8, color: egui::Color32) {
    let stroke = egui::Stroke::new(1.8, color);
    let mut pts: Vec<egui::Pos2> = Vec::new();
    let steps = 24;
    for i in 0..=steps {
        let x = i as f32 / steps as f32;
        let y = match kind {
            0 => x * x * (3.0 - 2.0 * x),          // ease in and out
            1 => x * x,                             // ease in: slow start
            2 => 1.0 - (1.0 - x) * (1.0 - x),       // ease out: slow finish
            3 => x,                                 // smooth/linear
            _ => 0.0,                               // hold
        };
        pts.push(pos2(r.min.x + r.width() * x, r.max.y - r.height() * y));
    }
    if kind == 4 {
        // Hold: step at the halfway point.
        pts = vec![
            pos2(r.min.x, r.max.y),
            pos2(r.center().x, r.max.y),
            pos2(r.center().x, r.min.y),
            pos2(r.max.x, r.min.y),
        ];
    }
    p.add(egui::Shape::line(pts, stroke));
}

/// A curved undo (or, mirrored, redo) arrow drawn with lines, so it never depends on a font glyph.
fn draw_history_arrow(p: &egui::Painter, c: egui::Pos2, rad: f32, mirror: bool, color: egui::Color32) {
    // A rounded loop with a flat tail and a small hook, as in the reference icon.
    let stroke = egui::Stroke::new(2.0, color);
    let sign = if mirror { -1.0 } else { 1.0 };
    let mut pts: Vec<egui::Pos2> = Vec::new();
    let steps = 28;
    for i in 0..=steps {
        let t = i as f32 / steps as f32;
        // Most of a circle, open just above the left shoulder.
        let a = std::f32::consts::PI * (0.55 + 1.55 * t);
        pts.push(pos2(c.x + sign * rad * a.cos(), c.y + rad * 0.85 * a.sin()));
    }
    p.add(egui::Shape::line(pts.clone(), stroke));
    // Flat tail running out of the opening, then a short hook upward.
    let tail = pts[pts.len() - 1];
    let out = pos2(tail.x - sign * rad * 0.9, tail.y);
    p.add(egui::Shape::line(vec![tail, out], stroke));
    p.add(egui::Shape::line(vec![out, pos2(out.x, out.y - rad * 0.5)], stroke));
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
