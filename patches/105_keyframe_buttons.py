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

    curve_menu(app, ui.ctx(), ui.max_rect());
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

fn curve_menu(app: &mut EffectcraftApp, ctx: &egui::Context, host: egui::Rect) {
    let open_id = egui::Id::new("ours-curve-open");
    let kind_id = egui::Id::new("ours-curve-kind");
    let mut open = ctx.data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    let mut kind = ctx.data(|d| d.get_temp::<u8>(kind_id).unwrap_or(0));
    let t = app.tokens;
    let mut close = false;
    // Docked under the toolbar on the left, over the column beside the viewer.
    let screen = host;
    egui::Window::new("曲线")
        .open(&mut open)
        .collapsible(false)
        .resizable(false)
        .default_pos(pos2(screen.left() + 186.0, screen.top() + 74.0))
        .movable(true)
        .default_width(232.0)
        .show(ctx, |ui| {
            // Top: a square custom curve. The two handles are the keyframe influences.
            ui.label("自定义缓动（拖动手柄）");
            let c1 = egui::Id::new("ours-curve-in");
            let c2 = egui::Id::new("ours-curve-out");
            let mut i1 = ctx.data(|d| d.get_temp::<f32>(c1).unwrap_or(0.33));
            let mut i2 = ctx.data(|d| d.get_temp::<f32>(c2).unwrap_or(0.33));
            let dragged_last = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-curve-dragged")).unwrap_or(false));
            let mut prev_dragged = dragged_last;
            let (canvas, _) = ui.allocate_exact_size(vec2(248.0, 248.0), Sense::hover());
            ui.painter().rect_filled(canvas, 6.0, t.switch_well);
            let plot = canvas.shrink2(vec2(18.0, 18.0));
            let p0 = pos2(plot.left(), plot.bottom());
            let p1 = pos2(plot.left() + plot.width() * i1, plot.bottom());
            let p2 = pos2(plot.left() + plot.width() * (1.0 - i2), plot.top());
            let p3 = pos2(plot.right(), plot.top());
            let mut pts: Vec<egui::Pos2> = Vec::new();
            for k in 0..=32 {
                let u = k as f32 / 32.0;
                let v = 1.0 - u;
                let x = v * v * v * p0.x + 3.0 * v * v * u * p1.x + 3.0 * v * u * u * p2.x + u * u * u * p3.x;
                let y = v * v * v * p0.y + 3.0 * v * v * u * p1.y + 3.0 * v * u * u * p2.y + u * u * u * p3.y;
                pts.push(pos2(x, y));
            }
            ui.painter().add(egui::Shape::line(pts, egui::Stroke::new(2.0, t.accent)));
            let h1 = ui.interact(Rect::from_center_size(p1, vec2(22.0, 22.0)), egui::Id::unique("ours-c1"), Sense::drag());
            let h2 = ui.interact(Rect::from_center_size(p2, vec2(22.0, 22.0)), egui::Id::unique("ours-c2"), Sense::drag());
            if h1.dragged() {
                i1 = (i1 + h1.drag_delta().x / plot.width()).clamp(0.02, 0.98);
            }
            if h2.dragged() {
                i2 = (i2 - h2.drag_delta().x / plot.width()).clamp(0.02, 0.98);
            }
            // Remember the shape a drag started from, so the previous curve can stay visible.
            let start_id = egui::Id::new("ours-curve-start");
            if h1.drag_started() || h2.drag_started() {
                ctx.data_mut(|d| d.insert_temp(start_id, (i1, i2)));
            }
            let ghost = ctx.data(|d| d.get_temp::<(f32, f32)>(start_id));
            if let Some((q1, q2)) = ghost {
                let a1 = pos2(plot.left() + plot.width() * q1, plot.bottom());
                let a2 = pos2(plot.left() + plot.width() * (1.0 - q2), plot.top());
                let mut ghost_pts: Vec<egui::Pos2> = Vec::new();
                for k in 0..=32 {
                    let u = k as f32 / 32.0;
                    let v = 1.0 - u;
                    let x = v * v * v * p0.x + 3.0 * v * v * u * a1.x + 3.0 * v * u * u * a2.x + u * u * u * p3.x;
                    let y = v * v * v * p0.y + 3.0 * v * v * u * a1.y + 3.0 * v * u * u * a2.y + u * u * u * p3.y;
                    ghost_pts.push(pos2(x, y));
                }
                ui.painter().add(egui::Shape::line(ghost_pts, egui::Stroke::new(1.4, t.text_faint)));
            }
            for (hh, at) in [(&h1, p1), (&h2, p2)] {
                ui.painter().circle_filled(at, if hh.hovered() { 7.0 } else { 5.0 }, t.text);
            }
            ctx.data_mut(|d| {
                d.insert_temp(c1, i1);
                d.insert_temp(c2, i2);
            });
            // Letting go of a handle applies at once: no second button to remember.
            if h1.drag_stopped() || h2.drag_stopped() {
                if app.session.state.selected_keys.is_empty() {
                    app.ui.status = "请先选中关键帧，再应用缓动".into();
                } else {
                    let _ = crate::menus::invoke(
                        app,
                        ctx,
                        "keys.velocity",
                        serde_json::json!({
                            "outSpeed": 0.0, "outInfluence": i1,
                            "inSpeed": 0.0, "inInfluence": i2,
                            "continuous": true,
                        }),
                    );
                }
            }
            let clip_id = egui::Id::new("ours-curve-clip");
            ui.horizontal(|ui| {
                if ui.button("复制曲线").clicked() {
                    ctx.data_mut(|d| d.insert_temp(clip_id, (i1, i2)));
                    app.ui.status = "已复制曲线".into();
                }
                if ui.button("粘贴曲线").clicked() {
                    match ctx.data(|d| d.get_temp::<(f32, f32)>(clip_id)) {
                        Some((q1, q2)) => {
                            i1 = q1;
                            i2 = q2;
                            ctx.data_mut(|d| {
                                d.insert_temp(c1, i1);
                                d.insert_temp(c2, i2);
                            });
                            app.ui.status = "已粘贴曲线".into();
                        }
                        None => app.ui.status = "还没有复制过曲线".into(),
                    }
                }
            });
            ui.add_space(6.0);
            ui.label("缓动预设（点击应用）");
            ui.add_space(2.0);
            // The last number is the minimum number of selected keyframes the command needs.
            let presets: [(&str, &str, u8, usize); 5] = [
                ("缓入缓出", "keys.easyEase", 0, 1),
                ("缓入", "keys.easyEaseIn", 1, 1),
                ("缓出", "keys.easyEaseOut", 2, 1),
                ("平滑", "keys.smooth", 3, 3),
                ("定格", "keys.toggleHold", 4, 1),
            ];
            ui.horizontal_wrapped(|ui| {
                for (label, cmd, k, need) in presets {
                    let (rect, resp) = ui.allocate_exact_size(vec2(66.0, 74.0), Sense::click());
                    let bg = if kind == k { t.accent.gamma_multiply(0.35) } else if resp.hovered() { t.hover } else { t.switch_well };
                    ui.painter().rect_filled(rect, 5.0, bg);
                    let cell = Rect::from_min_size(rect.min + vec2(9.0, 8.0), vec2(46.0, 40.0));
                    draw_ease_curve(ui.painter(), cell, k, t.text);
                    ui.painter().text(
                        pos2(rect.center().x, rect.max.y - 13.0),
                        Align2::CENTER_CENTER,
                        label,
                        Tokens::ui(11.0),
                        t.text,
                    );
                    if resp.on_hover_text(label).clicked() {
                        let have = app.session.state.selected_keys.len();
                        if have < need {
                            app.ui.status = if need > 1 {
                                format!("「{label}」需要选中至少 {need} 个关键帧")
                            } else {
                                "请先选中关键帧，再应用缓动".to_string()
                            };
                        } else {
                            let _ = crate::menus::invoke(app, ctx, cmd, serde_json::json!({}));
                            kind = k;
                        }
                    }
                }
            });
        });
    ctx.data_mut(|d| {
        d.insert_temp(open_id, open);
        d.insert_temp(kind_id, kind);
    });
    let _ = close;
    close = false;
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
    // Rounded square loop, open on the left, with a short tick: the reference icon mirrored.
    let stroke = egui::Stroke::new(2.0, color);
    let sign = if mirror { -1.0 } else { 1.0 };
    let w = rad * 0.9;
    let h = rad * 0.75;
    let r = rad * 0.35;
    let left = c.x - sign * w;
    let right = c.x + sign * w;
    let top = c.y - h;
    let bottom = c.y + h;
    let mut pts: Vec<egui::Pos2> = Vec::new();
    // Top edge, from the tick to the rounded top corner.
    pts.push(pos2(left + sign * r * 0.4, top));
    pts.push(pos2(right - sign * r, top));
    // Rounded top-right corner.
    for i in 0..=6 {
        let a = -std::f32::consts::FRAC_PI_2 + std::f32::consts::FRAC_PI_2 * (i as f32 / 6.0);
        pts.push(pos2(right - sign * r + sign * r * a.cos(), top + r + r * a.sin()));
    }
    // Down the right side, round the bottom corner, along the bottom to the left.
    pts.push(pos2(right, bottom - r));
    for i in 0..=6 {
        let a = std::f32::consts::FRAC_PI_2 * (i as f32 / 6.0);
        pts.push(pos2(right - sign * r + sign * r * a.cos(), bottom - r + r * a.sin()));
    }
    pts.push(pos2(left + sign * r, bottom));
    p.add(egui::Shape::line(pts, stroke));
    // The tick at the opening.
    p.add(egui::Shape::line(
        vec![pos2(left + sign * r * 0.4, top), pos2(left + sign * r * 0.4, top - rad * 0.35)],
        stroke,
    ));
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
