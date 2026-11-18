#!/usr/bin/env python3
"""A 全屏 button in the viewer's bottom bar, and a full-screen preview behind it.

Pressing it fills the window with the composition: only the picture, an exit button, a play/pause
button and one slider across the whole duration (dragging it moves the playhead) — the panels,
menus and the toolbar are gone until the exit button is pressed.

The picture itself is the ordinary Composition viewer drawn into the full window, so scrubbing,
playback, zoom and everything else behave exactly as they do docked; the preview's own bottom strip
is painted over the viewer's control bar.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FULLSCREEN_V1"

BUTTON_ANCHOR = "    (tr.right() + 8.0 - bar.left()).max(bar.width())\n}"
BUTTON_NEW = '''    // EFFECTCRAFT_OURS_FULLSCREEN_V1 — 全屏预览按钮
    let fs = Rect::from_min_size(pos2(tr.right() + 8.0, cy - 10.0), vec2(44.0, 20.0));
    let fs_resp = ui.interact(fs, egui::Id::unique("ours-fullscreen-btn"), egui::Sense::click()).on_hover_text("全屏预览");
    p.rect_filled(fs, 4.0, t.switch_well);
    p.text(fs.center(), Align2::CENTER_CENTER, "全屏", Tokens::ui(11.5), t.text);
    if fs_resp.clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-fullscreen-open"), true));
    }
    (tr.right() + 8.0 - bar.left()).max(bar.width())
}'''

DOCK_ANCHOR = "        self.dock_area(ui, body);\n"
DOCK_NEW = '''        // EFFECTCRAFT_OURS_FULLSCREEN_V1 — 全屏预览时不画面板
        if ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-fullscreen-open")).unwrap_or(false)) {
            ours_fullscreen(self, ui, full);
            return;
        }
        self.dock_area(ui, body);
'''

HELPER = r'''
/// EFFECTCRAFT_OURS_FULLSCREEN_V1 — 全屏预览：画面铺满，底部只留退出、播放和整段拖动。
fn ours_fullscreen(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {
    let ctx = ui.ctx().clone();
    let t = app.tokens;
    ui.painter().rect_filled(full, 0.0, egui::Color32::BLACK);
    crate::panels::show(app, ui, crate::dock::PanelKind::Composition, full);
    let bar_h = 52.0;
    let bar = egui::Rect::from_min_max(egui::pos2(full.min.x, full.max.y - bar_h), full.max);
    let p = ui.painter().with_clip_rect(bar);
    p.rect_filled(bar, 0.0, egui::Color32::from_black_alpha(235));
    let cy = bar.center().y;
    let ex = egui::Rect::from_min_size(egui::pos2(bar.min.x + 10.0, cy - 13.0), egui::vec2(78.0, 26.0));
    let ex_resp = ui.interact(ex, egui::Id::unique("ours-fs-exit"), egui::Sense::click());
    p.rect_filled(ex, 6.0, t.switch_well);
    p.text(ex.center(), egui::Align2::CENTER_CENTER, "退出预览", Tokens::ui(12.0), t.text);
    if ex_resp.clicked() {
        ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-fullscreen-open"), false));
    }
    let play = egui::Rect::from_min_size(egui::pos2(ex.max.x + 8.0, cy - 13.0), egui::vec2(34.0, 26.0));
    let play_resp = ui.interact(play, egui::Id::unique("ours-fs-play"), egui::Sense::click());
    p.rect_filled(play, 6.0, t.switch_well);
    let playing = app.playback.playing;
    p.text(play.center(), egui::Align2::CENTER_CENTER, if playing { "II" } else { ">" }, Tokens::ui(12.0), t.text);
    if play_resp.clicked() {
        let _ = crate::menus::invoke(app, &ctx, "playback.toggle", serde_json::json!({}));
    }
    let Some(cid) = app.session.active_comp_id() else { return };
    let Some(comp) = app.session.project.comp(cid) else { return };
    let dur = comp.duration.seconds().max(1e-3);
    let now = app.session.time().seconds().clamp(0.0, dur);
    let track = egui::Rect::from_min_max(egui::pos2(play.max.x + 10.0, cy - 8.0), egui::pos2(bar.max.x - 12.0, cy + 8.0));
    p.rect_filled(track, 4.0, t.switch_well);
    let frac = (now / dur) as f32;
    let knob = egui::pos2(track.min.x + track.width() * frac, cy);
    p.rect_filled(egui::Rect::from_min_max(track.min, egui::pos2(knob.x, track.max.y)), 4.0, t.accent.gamma_multiply(0.55));
    p.circle_filled(knob, 7.0, t.accent);
    let resp = ui.interact(track, egui::Id::unique("ours-fs-scrub"), egui::Sense::click_and_drag());
    if (resp.dragged() || resp.clicked())
        && let Some(pos) = resp.interact_pointer_pos()
    {
        let f = ((pos.x - track.min.x) / track.width().max(1.0)).clamp(0.0, 1.0) as f64;
        app.session.set_time(effectcraft_engine::time::Tick::from_seconds_f64(f * dur));
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    tools = root / "crates/ui-egui/src/panels/viewer_tools.rs"
    src = tools.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(BUTTON_ANCHOR) != 1:
            raise SystemExit(f"button anchor: {src.count(BUTTON_ANCHOR)}")
        tools.write_text(src.replace(BUTTON_ANCHOR, BUTTON_NEW, 1), encoding="utf-8")
        print("全屏 button added to the viewer bar")
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("fullscreen preview already installed")
        return
    if src.count(DOCK_ANCHOR) != 1:
        raise SystemExit(f"dock anchor: {src.count(DOCK_ANCHOR)}")
    src = src.replace(DOCK_ANCHOR, DOCK_NEW, 1)
    src += HELPER
    frame.write_text(src, encoding="utf-8")
    print("fullscreen preview installed")


if __name__ == "__main__":
    main()
