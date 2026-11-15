#!/usr/bin/env python3
"""悬浮球改用当前帧的画笔直接画（Area 方案在这版 egui 里没显示出来）。

The first version put the ball in its own `Area`. Nothing appeared on the phone, so it is painted
straight into the frame's painter — which is where the toast draws, and that is known to be visible —
and interacted through `ui.interact`. Same behaviour: drag to move, edge-snap with a very low alpha,
tap to open/close the empty panel.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_BALL_V2"

OLD = '''fn shortcut_ball(ui: &mut egui::Ui, full: egui::Rect) {'''
NEW = '''fn shortcut_ball(ui: &mut egui::Ui, full: egui::Rect) {
    // EFFECTCRAFT_OURS_SHORTCUT_BALL_V2 — 直接画在本帧画笔上（Area 方案不显示）
    shortcut_ball_direct(ui, full);
}

fn shortcut_ball_direct(ui: &mut egui::Ui, full: egui::Rect) {'''

BODY_OLD = '''    let rect = egui::Rect::from_min_size(pos, egui::vec2(size, size));
    egui::Area::new(egui::Id::unique("shortcut-ball-area"))'''
BODY_NEW = '''    let r = egui::Rect::from_min_size(pos, egui::vec2(size, size));
    let resp = ui.interact(r, egui::Id::unique("shortcut-ball-hit"), egui::Sense::click_and_drag()).on_hover_text("快捷");
    if resp.dragged() {
        pos += resp.drag_delta();
        pos.x = pos.x.clamp(full.min.x + 4.0, full.max.x - size - 4.0);
        pos.y = pos.y.clamp(full.min.y + 4.0, full.max.y - size - 4.0);
        edge = 0;
    }
    if resp.drag_stopped() {
        if pos.x - full.min.x < 24.0 {
            pos.x = full.min.x - size * 0.55;
            edge = 1;
        } else if full.max.x - (pos.x + size) < 24.0 {
            pos.x = full.max.x - size * 0.45;
            edge = 2;
        } else if full.max.y - (pos.y + size) < 48.0 {
            pos.y = full.max.y - size * 0.5;
            edge = 3;
        }
    }
    if resp.clicked() {
        open = !open;
        edge = 0;
    }
    let alpha = if edge != 0 && !open { 44 } else { 255 };
    let tint = egui::Color32::from_white_alpha(alpha);
    {
        let p = ui.painter().with_clip_rect(full);
        p.circle_filled(r.center(), size * 0.5, egui::Color32::from_black_alpha((alpha as f32 * 0.25) as u8));
        if let Some(t) = &tex {
            p.image(t.id(), r, egui::Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0)), tint);
        } else {
            p.circle_filled(r.center(), size * 0.5, tint);
        }
    }
    // 空面板（直接画在球左边）
    if open {
        let panel = egui::Rect::from_min_size(
            egui::pos2((pos.x - 168.0).max(full.min.x + 8.0), pos.y.min(full.max.y - 160.0)),
            egui::vec2(160.0, 120.0),
        );
        let p = ui.painter().with_clip_rect(full);
        p.rect_filled(panel, 12.0, egui::Color32::from_rgba_unmultiplied(10, 10, 12, 90));
        p.rect_stroke(panel, 12.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 70)), egui::StrokeKind::Inside);
        p.text(panel.center(), egui::Align2::CENTER_CENTER, "快捷键\\n（待添加）", Tokens::ui(13.0), egui::Color32::from_rgb(240, 241, 245));
    }
    let _ = r;
    let _ = (edge, open);
    return;
    #[allow(unreachable_code)]
    egui::Area::new(egui::Id::unique("shortcut-ball-area"))'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("ball already painted directly")
        return
    for old, new in ((OLD, NEW), (BODY_OLD, BODY_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("ball paints directly into the frame")


if __name__ == "__main__":
    main()
