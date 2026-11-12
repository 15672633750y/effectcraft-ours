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
    let plug_rect = Rect::from_min_size(pos2(x, cy - 13.0), vec2(44.0, 26.0));
    let plug_resp = ui.interact(plug_rect, egui::Id::unique("ours-plugin-button"), Sense::click());
    p.rect_filled(plug_rect, 4.0, t.switch_well);
    p.text(plug_rect.center(), Align2::CENTER_CENTER, "插件", Tokens::ui(12.0), t.text);
    if plug_resp.clicked() {
        let id = egui::Id::new("ours-plugin-open");
        let now: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
        ui.ctx().data_mut(|d| d.insert_temp(id, !now));
    }
    plugin_window(app, ui.ctx());
    x += 48.0;

    curve_menu(app, ui.ctx(), ui.max_rect());
    x += 4.0;

    let undo_ready = !app.session.history.undo.is_empty();
    let redo_ready = !app.session.history.redo.is_empty();
    for (label, cmd, tip, ready) in [
        ("⟲", "edit.undo", "撤销", undo_ready),
        ("⟳", "edit.redo", "恢复", redo_ready),
    ] {
        let r = Rect::from_min_size(pos2(x, cy - 15.0), vec2(30.0, 26.0));
        let resp = ui.interact(r, egui::Id::unique(("ours-history", cmd)), Sense::click());
        p.rect_filled(r, 5.0, t.switch_well);
        let tint = if ready { t.text } else { t.text_faint };
        // The curved arrows are drawn as vectors: the bundled font has no ↶/↷ glyph, and a
        // missing glyph would show as a narrow box.
        let _ = label;
        draw_history_arrow(&p, r, cmd == "edit.redo", tint);
        let resp = resp.on_hover_text(tip);
        if resp.clicked() && ready {
            if crate::menus::invoke(app, ui.ctx(), cmd, serde_json::json!({})).is_ok() {
                app.ui.status = if cmd == "edit.undo" { "已撤销".into() } else { "已恢复".into() };
            }
        }
        x += 34.0;
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
            // The curve is a set of draggable points: pull any of them down and the curve
            // dips there, pull one up and it arches. Left/right dragging shifts the peak.
            ui.label("自定义缓动（拖动曲线上的点）");
            let pts_id = egui::Id::new("ours-curve-points");
            let mut ys: [f32; 9] = ctx.data(|d| d.get_temp::<[f32; 9]>(pts_id)).unwrap_or([0.06, 0.22, 0.45, 0.66, 0.8, 0.72, 0.55, 0.35, 0.14]);
            let (canvas, _) = ui.allocate_exact_size(vec2(248.0, 248.0), Sense::hover());
            ui.painter().rect_filled(canvas, 6.0, t.switch_well);
            let plot = canvas.shrink2(vec2(18.0, 18.0));
            let px = |i: usize| plot.left() + plot.width() * (i as f32 / 8.0);
            let py = |v: f32| plot.bottom() - plot.height() * v.clamp(0.0, 1.0);
            // Smooth curve through the points (Catmull-Rom).
            let mut path: Vec<egui::Pos2> = Vec::new();
            for seg in 0usize..8 {
                let (a, b, c, d) = (
                    ys[seg.saturating_sub(1)],
                    ys[seg],
                    ys[seg + 1],
                    ys[(seg + 2).min(8)],
                );
                let steps = 16;
                for k in 0..steps {
                    let u = k as f32 / steps as f32;
                    let u2 = u * u;
                    let u3 = u2 * u;
                    let v = 0.5 * ((2.0 * b)
                        + (-a + c) * u
                        + (2.0 * a - 5.0 * b + 4.0 * c - d) * u2
                        + (-a + 3.0 * b - 3.0 * c + d) * u3);
                    let x = px(seg) + (px(seg + 1) - px(seg)) * u;
                    path.push(pos2(x, py(v)));
                }
            }
            path.push(pos2(px(8), py(ys[8])));
            ui.painter().add(egui::Shape::line(path, egui::Stroke::new(2.2, t.accent)));
            // Drag anywhere: the nearest of the nine points follows the finger 1:1, which keeps
            // the curve under the pointer instead of lagging behind it.
            let canvas_resp = ui.interact(canvas, egui::Id::unique("ours-curve-drag"), Sense::drag());
            let mut stopped = false;
            if canvas_resp.dragged() || canvas_resp.drag_started() {
                if let Some(pos) = canvas_resp.interact_pointer_pos() {
                    let t = ((pos.x - plot.left()) / plot.width()).clamp(0.0, 1.0);
                    let idx = ((t * 8.0).round() as usize).min(8);
                    // Between two points, blend so the curve bends smoothly rather than snapping.
                    let exact = t * 8.0;
                    let lo = exact.floor() as usize;
                    let hi = (lo + 1).min(8);
                    let frac = exact - lo as f32;
                    let y = ((plot.bottom() - pos.y) / plot.height()).clamp(0.0, 1.0);
                    if frac < 0.5 {
                        ys[lo] = y;
                    } else {
                        ys[hi] = y;
                    }
                    let _ = idx;
                }
            }
            if canvas_resp.drag_stopped() {
                stopped = true;
            }
            ctx.data_mut(|d| d.insert_temp(pts_id, ys));
            if stopped {
                if app.session.state.selected_keys.is_empty() {
                    app.ui.status = "请先选中关键帧，再应用缓动".into();
                } else {
                    // Slope at each end becomes the keyframe speed; the middle sets the influence.
                    let out_speed = (ys[1] - ys[0]) * 3.0;
                    let in_speed = (ys[8] - ys[7]) * 3.0;
                    let peak = ys[4].clamp(0.05, 1.0);
                    let out_inf = (0.5 + (peak - 0.5) * 1.4).clamp(0.02, 1.0);
                    let in_inf = (0.5 + (peak - 0.5) * 1.4).clamp(0.02, 1.0);
                    let _ = crate::menus::invoke(
                        app,
                        ctx,
                        "keys.velocity",
                        serde_json::json!({
                            "outSpeed": out_speed, "outInfluence": out_inf,
                            "inSpeed": in_speed, "inInfluence": in_inf,
                            "continuous": true,
                        }),
                    );
                }
            }
            let save_id = egui::Id::new("ours-curve-saved");
            ui.horizontal(|ui| {
                if ui.button("保存曲线").clicked() {
                    ctx.data_mut(|d| d.insert_temp(save_id, ys));
                    app.ui.status = "已保存曲线".into();
                }
                if ui.button("删除关键帧").clicked() {
                    if app.session.state.selected_keys.is_empty() {
                        app.ui.status = "请先选中关键帧".into();
                    } else {
                        let _ = crate::menus::invoke(app, ctx, "keys.delete", serde_json::json!({}));
                        app.ui.status = "已删除关键帧".into();
                    }
                }
            });
            let mut restore = None;
            if let Some(sv) = ctx.data(|d| d.get_temp::<[f32; 9]>(save_id)) {
                let (thumb, tresp) = ui.allocate_exact_size(vec2(248.0, 54.0), Sense::click());
                ui.painter().rect_filled(thumb, 5.0, t.switch_well);
                let p0 = thumb.shrink2(vec2(8.0, 6.0));
                let mut tp: Vec<egui::Pos2> = Vec::new();
                for i in 0..=64 {
                    let u = i as f32 / 64.0;
                    let seg = ((u * 8.0) as usize).min(7);
                    let local = u * 8.0 - seg as f32;
                    let (a, b, c, d) = (sv[seg.saturating_sub(1)], sv[seg], sv[seg + 1], sv[(seg + 2).min(8)]);
                    let u2 = local * local;
                    let u3 = u2 * local;
                    let v = 0.5 * ((2.0 * b)
                        + (-a + c) * local
                        + (2.0 * a - 5.0 * b + 4.0 * c - d) * u2
                        + (-a + 3.0 * b - 3.0 * c + d) * u3);
                    tp.push(pos2(p0.left() + p0.width() * u, p0.bottom() - p0.height() * v.clamp(0.0, 1.0)));
                }
                ui.painter().add(egui::Shape::line(tp, egui::Stroke::new(1.8, t.accent)));
                ui.painter().text(pos2(thumb.left() + 6.0, thumb.top() + 8.0), Align2::LEFT_TOP, "已保存", Tokens::ui(10.0), t.text_dim);
                if tresp.on_hover_text("套用保存的曲线").clicked() {
                    restore = Some(sv);
                }
            }
            if let Some(sv) = restore {
                ys = sv;
                ctx.data_mut(|d| d.insert_temp(pts_id, ys));
            }
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

fn plugin_window(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let id = egui::Id::new("ours-plugin-open");
    let mut open = ctx.data(|d| d.get_temp::<bool>(id).unwrap_or(false));
    if !open {
        return;
    }
    let mut close = false;
    egui::Window::new("导入插件")
        .default_pos(egui::pos2(100.0, 150.0))
        .default_width(430.0)
        .show(ctx, |ui| {
            ui.heading("能装的格式");
            ui.label("• .wasm —— EffectCraft 效果插件（唯一能真正跑的效果格式）");
            ui.label("• .jsx / .js —— AE 脚本，装好后在 文件 → 脚本 里运行");
            ui.label("• .zip —— 里面是上面两种时会解开安装");
            ui.separator();
            ui.heading("怎么装");
            ui.label("把文件放进手机这两个文件夹（没有就新建）：");
            ui.label("  Download/EffectCraftPlugins —— .wasm / .zip");
            ui.label("  Download/EffectCraftScripts —— .jsx / .js");
            ui.label("然后完全退出 App 再打开，会自动装好。");
            ui.separator();
            ui.heading("装不了的格式");
            ui.label("• .aex / .dll / CEP 面板（Adobe 电脑版插件）手机跑不了，装了也不会出现在效果列表。");
            ui.separator();
            if ui.button("知道了").clicked() {
                close = true;
            }
        });
    if close {
        open = false;
    }
    ctx.data_mut(|d| d.insert_temp(id, open));
}
fn draw_history_arrow(p: &egui::Painter, r: Rect, mirror: bool, color: egui::Color32) {
    // Fixed size, centred on the button, so it lines up with the neighbouring buttons and the
    // pair is an exact mirror of itself.
    let stroke = egui::Stroke::new(1.8, color);
    let c = r.center();
    let bw = 18.0;
    let bh = 14.0;
    let (top, bot) = (c.y - bh * 0.5, c.y + bh * 0.5);
    let hw = bw * 0.5;
    let rr = (bh * 0.42).min(hw * 0.56);
    let mut local: Vec<egui::Pos2> = Vec::new();
    local.push(pos2(-hw * 0.68, bot));
    local.push(pos2(hw - rr, bot));
    for i in 1..=8 {
        let a = (90.0 - 90.0 * i as f32 / 8.0).to_radians();
        local.push(pos2(hw - rr + rr * a.cos(), bot - rr + rr * a.sin()));
    }
    local.push(pos2(hw, top + rr));
    for i in 1..=8 {
        let a = (-90.0 * i as f32 / 8.0).to_radians();
        local.push(pos2(hw - rr + rr * a.cos(), top + rr + rr * a.sin()));
    }
    local.push(pos2(-hw * 0.9, top));
    let hook = vec![pos2(-hw * 0.9, top), pos2(-hw * 0.34, top - bh * 0.34)];
    let flip = |q: egui::Pos2| pos2(if mirror { c.x - q.x } else { c.x + q.x }, q.y);
    p.add(egui::Shape::line(local.iter().map(|q| flip(*q)).collect::<Vec<_>>(), stroke));
    p.add(egui::Shape::line(hook.iter().map(|q| flip(*q)).collect::<Vec<_>>(), stroke));
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
