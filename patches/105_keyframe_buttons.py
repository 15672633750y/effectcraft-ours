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
            // One grab point pulls the whole curve: drag down and it bows down, drag up and it
            // arches over, drag sideways and it leans that way.
            ui.label("自定义缓动（按住方块拖动）");
            let gx = egui::Id::new("ours-c-gx");
            let gy = egui::Id::new("ours-c-gy");
            let mut q = ctx.data(|d| d.get_temp::<egui::Pos2>(gx));
            let cur = q.unwrap_or(pos2(0.5, 0.5));
            let (canvas, _) = ui.allocate_exact_size(vec2(248.0, 248.0), Sense::hover());
            ui.painter().rect_filled(canvas, 6.0, t.switch_well);
            let plot = canvas.shrink2(vec2(18.0, 18.0));
            let drag = ui.interact(canvas, egui::Id::unique("ours-curve-drag"), Sense::drag());
            let mut nq = cur;
            if drag.dragged() {
                let d = drag.drag_delta();
                nq.x = (nq.x + d.x / plot.width() * 1.8).clamp(-0.6, 1.6);
                nq.y = (nq.y - d.y / plot.height() * 1.8).clamp(0.0, 1.0);
            }
            // A bell, like the reference panel: drag up to raise the peak, sideways to move it.
            let h = nq.y.clamp(0.0, 1.0);
            let skew = (nq.x.clamp(0.05, 0.95)) as f32;
            let mut pts: Vec<egui::Pos2> = Vec::new();
            for k in 0..=60 {
                let t = k as f32 / 60.0;
                // Shift the sine so its peak sits where the grab point is.
                let u = if t < skew { 0.5 * t / skew } else { 0.5 + 0.5 * (t - skew) / (1.0 - skew) };
                let v = (std::f32::consts::PI * u).sin();
                let x = plot.left() + plot.width() * t;
                let y = plot.bottom() - plot.height() * h * v;
                pts.push(pos2(x, y.clamp(plot.top(), plot.bottom())));
            }
            ui.painter().add(egui::Shape::line(pts, egui::Stroke::new(2.2, t.accent)));
            let knob = pos2(plot.left() + plot.width() * nq.x.clamp(0.0, 1.0), plot.bottom() - plot.height() * nq.y.clamp(0.0, 1.0));
            ui.painter().circle_filled(knob, if drag.dragged() || drag.hovered() { 7.0 } else { 5.0 }, t.text);
            ctx.data_mut(|d| d.insert_temp(gx, nq));
            if drag.drag_stopped() {
                if app.session.state.selected_keys.is_empty() {
                    app.ui.status = "请先选中关键帧，再应用缓动".into();
                } else {
                    let out_inf = (0.5 + (nq.x - 0.5) * 0.9).clamp(0.02, 1.0);
                    let in_inf = (0.5 - (nq.x - 0.5) * 0.9).clamp(0.02, 1.0);
                    let slope = (nq.y - 0.5) * 2.4;
                    let _ = crate::menus::invoke(
                        app,
                        ctx,
                        "keys.velocity",
                        serde_json::json!({
                            "outSpeed": slope, "outInfluence": out_inf,
                            "inSpeed": -slope, "inInfluence": in_inf,
                            "continuous": true,
                        }),
                    );
                }
            }
            let save_id = egui::Id::new("ours-curve-saved");
            ui.horizontal(|ui| {
                if ui.button("保存曲线").clicked() {
                    ctx.data_mut(|d| d.insert_temp(save_id, nq));
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
            ui.add_space(6.0);
            // The saved curve shows here; click it to apply again.
            if let Some(sv) = ctx.data(|d| d.get_temp::<egui::Pos2>(save_id)) {
                let (thumb, tresp) = ui.allocate_exact_size(vec2(248.0, 62.0), Sense::click());
                ui.painter().rect_filled(thumb, 5.0, t.switch_well);
                let pad = thumb.shrink2(vec2(10.0, 8.0));
                let hh = sv.y.clamp(0.0, 1.0);
                let sk = sv.x.clamp(0.05, 0.95);
                let mut tp: Vec<egui::Pos2> = Vec::new();
                for k in 0..=40 {
                    let tt = k as f32 / 40.0;
                    let u = if tt < sk { 0.5 * tt / sk } else { 0.5 + 0.5 * (tt - sk) / (1.0 - sk) };
                    let v = (std::f32::consts::PI * u).sin();
                    tp.push(pos2(pad.left() + pad.width() * tt, (pad.bottom() - pad.height() * hh * v).clamp(pad.top(), pad.bottom())));
                }
                ui.painter().add(egui::Shape::line(tp, egui::Stroke::new(1.8, t.accent)));
                ui.painter().text(pos2(thumb.left() + 6.0, thumb.top() + 9.0), Align2::LEFT_TOP, "已保存", Tokens::ui(10.0), t.text_dim);
                if tresp.on_hover_text("应用保存的曲线").clicked() {
                    ctx.data_mut(|d| d.insert_temp(gx, sv));
                }
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
