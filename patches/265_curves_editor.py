#!/usr/bin/env python3
"""曲线编辑器：手机上也能像 AE 一样点/拖曲线控制点。

AE's Curves stores its points as a string ("0,0 0.5,0.6 1,1") on hidden params, so the effect could be
added but never edited on a phone. This adds a graph window: tap empty space to add a point, drag a point
to move it, double-tap a point to remove it, switch channel, reset, and apply — which writes the string
back through `prop.set`.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVES_EDITOR_V1"

CALL_OLD = "        preset_panel(self, ui, full);\n"
CALL_NEW = "        preset_panel(self, ui, full);\n        curves_editor(self, ui, full);\n"

FN = r'''

/// EFFECTCRAFT_OURS_CURVES_EDITOR_V1 — 曲线编辑器（RGB / R / G / B）。
fn curves_editor(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {
    let open_id = egui::Id::unique("ours-curves-open");
    if !ui.ctx().data(|d| d.get_temp::<bool>(open_id).unwrap_or(false)) {
        return;
    }
    let size = egui::vec2(300.0, 360.0);
    let r = egui::Rect::from_min_size(
        egui::pos2(full.center().x - size.x * 0.5, full.center().y - size.y * 0.5),
        size,
    );
    let p = ui.painter().with_clip_rect(full);
    p.rect_filled(r, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 240));
    p.rect_stroke(r, 14.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 90)), egui::StrokeKind::Inside);
    p.text(r.center_top() + egui::vec2(0.0, 20.0), egui::Align2::CENTER_CENTER, "曲线", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));

    // 通道
    let ch_id = egui::Id::unique("ours-curves-channel");
    let mut ch: usize = ui.ctx().data(|d| d.get_temp::<usize>(ch_id).unwrap_or(0));
    let names = ["RGB", "R", "G", "B"];
    let mut y = r.min.y + 40.0;
    for (i, n) in names.iter().enumerate() {
        let b = egui::Rect::from_min_size(egui::pos2(r.min.x + 12.0 + i as f32 * 62.0, y), egui::vec2(58.0, 22.0));
        p.rect_filled(b, 6.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, if i == ch { 55 } else { 20 }));
        p.text(b.center(), egui::Align2::CENTER_CENTER, *n, Tokens::ui(11.0), egui::Color32::from_rgb(235, 237, 242));
        if ui.interact(b, egui::Id::new(("ours-curves-ch", i)), egui::Sense::click()).clicked() {
            ch = i;
            ui.ctx().data_mut(|d| d.insert_temp(ch_id, ch));
        }
    }

    // 图形区域
    let g = egui::Rect::from_min_size(egui::pos2(r.min.x + 16.0, y + 30.0), egui::vec2(size.x - 32.0, size.y - 130.0));
    p.rect_filled(g, 6.0, egui::Color32::from_rgba_unmultiplied(0, 0, 0, 160));
    for k in 1..4 {
        let f = k as f32 / 4.0;
        let x = g.min.x + g.width() * f;
        let yy = g.min.y + g.height() * f;
        p.line_segment([egui::pos2(x, g.min.y), egui::pos2(x, g.max.y)], egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 26)));
        p.line_segment([egui::pos2(g.min.x, yy), egui::pos2(g.max.x, yy)], egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 26)));
    }

    let pts_id = egui::Id::new(("ours-curves-pts", ch));
    let mut pts: Vec<(f32, f32)> = ui.ctx().data(|d| d.get_temp::<Vec<(f32, f32)>>(pts_id)).unwrap_or_else(|| vec![(0.0, 0.0), (1.0, 1.0)]);
    pts.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

    let to_screen = |q: (f32, f32)| egui::pos2(g.min.x + q.0 * g.width(), g.max.y - q.1 * g.height());
    for w in pts.windows(2) {
        p.line_segment([to_screen(w[0]), to_screen(w[1])], egui::Stroke::new(2.0, egui::Color32::from_rgb(90, 220, 200)));
    }
    let mut changed = false;
    for i in 0..pts.len() {
        let c = to_screen(pts[i]);
        let hit = egui::Rect::from_center_size(c, egui::vec2(22.0, 22.0));
        let resp = ui.interact(hit, egui::Id::new(("ours-curves-pt", ch, i)), egui::Sense::click_and_drag());
        if resp.dragged() {
            let d = resp.drag_delta();
            pts[i].0 = (pts[i].0 + d.x / g.width()).clamp(0.0, 1.0);
            pts[i].1 = (pts[i].1 - d.y / g.height()).clamp(0.0, 1.0);
            changed = true;
        }
        if resp.double_clicked() && pts.len() > 2 && i != 0 && i + 1 != pts.len() {
            pts.remove(i);
            changed = true;
            break;
        }
        let col = if resp.hovered() { egui::Color32::WHITE } else { egui::Color32::from_rgb(200, 230, 225) };
        p.circle_filled(c, 4.5, col);
    }
    // 点空白加点
    let area = ui.interact(g, egui::Id::new(("ours-curves-area", ch)), egui::Sense::click());
    if area.clicked() && let Some(q) = ui.input(|i| i.pointer.interact_pos()) && g.contains(q) {
        let nx = ((q.x - g.min.x) / g.width()).clamp(0.0, 1.0);
        let ny = ((g.max.y - q.y) / g.height()).clamp(0.0, 1.0);
        pts.push((nx, ny));
        changed = true;
    }
    if changed {
        pts.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
        ui.ctx().data_mut(|d| d.insert_temp(pts_id, pts.clone()));
    }

    // 底部按钮
    let by = r.max.y - 34.0;
    let apply = egui::Rect::from_min_size(egui::pos2(r.max.x - 96.0, by), egui::vec2(80.0, 24.0));
    p.rect_filled(apply, 6.0, egui::Color32::from_rgba_unmultiplied(90, 220, 200, 90));
    p.text(apply.center(), egui::Align2::CENTER_CENTER, "应用", Tokens::ui(11.0), egui::Color32::from_rgb(20, 26, 26));
    if ui.interact(apply, egui::Id::new("ours-curves-apply"), egui::Sense::click()).clicked() {
        let key = match ch {
            1 => "red",
            2 => "green",
            3 => "blue",
            _ => "rgb",
        };
        let text: String = pts.iter().map(|(x, y)| format!("{x:.4},{y:.4}")).collect::<Vec<_>>().join(" ");
        let _ = app.session.execute(
            "prop.set",
            serde_json::json!({ "path": format!("effects/ec.color.curves/{key}"), "value": text }),
        );
    }
    let reset = egui::Rect::from_min_size(egui::pos2(r.min.x + 16.0, by), egui::vec2(72.0, 24.0));
    p.rect_filled(reset, 6.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 26));
    p.text(reset.center(), egui::Align2::CENTER_CENTER, "重置", Tokens::ui(11.0), egui::Color32::from_rgb(235, 237, 242));
    if ui.interact(reset, egui::Id::new("ours-curves-reset"), egui::Sense::click()).clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(pts_id, vec![(0.0, 0.0), (1.0, 1.0)]));
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("curves editor already present")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("curves editor added")


if __name__ == "__main__":
    main()
