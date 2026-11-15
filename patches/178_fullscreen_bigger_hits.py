#!/usr/bin/env python3
"""The full-screen preview's controls are easier to hit with a finger.

The bar was 52 px tall with a 34×26 play button and a 16 px scrub track — fine for a mouse, cramped
on a phone, and during playback the finger competes with the moving picture. The bar is now 64 px,
the buttons are 44 px tall (exit 96 wide, play 60), and the scrub track is 28 px tall with a padded
hit rect, so a tap lands even when it is a little off.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FULLSCREEN_BIG_HITS_V1"

START = "    let bar_h = 52.0;"

NEW = '''    let bar_h = 64.0;
    let bar = egui::Rect::from_min_max(egui::pos2(full.min.x, full.max.y - bar_h), full.max);
    let p = ui.painter().with_clip_rect(bar);
    p.rect_filled(bar, 0.0, egui::Color32::from_black_alpha(235));
    let cy = bar.center().y;
    // Exit: a tall button with a padded hit rect.
    let ex = egui::Rect::from_min_size(egui::pos2(bar.min.x + 10.0, cy - 22.0), egui::vec2(96.0, 44.0));
    let ex_resp = ui.interact(ex.expand(6.0), egui::Id::unique("ours-fs-exit"), egui::Sense::click());
    p.rect_filled(ex, 8.0, t.switch_well);
    p.text(ex.center(), egui::Align2::CENTER_CENTER, "退出预览", Tokens::ui(13.0), t.text);
    if ex_resp.clicked() {
        ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-fullscreen-open"), false));
    }
    // Play / pause: 60 wide, the whole bar height, so it is easy to hit while it plays.
    let play = egui::Rect::from_min_size(egui::pos2(ex.max.x + 10.0, cy - 22.0), egui::vec2(60.0, 44.0));
    let play_resp = ui.interact(play.expand(6.0), egui::Id::unique("ours-fs-play"), egui::Sense::click());
    p.rect_filled(play, 8.0, t.switch_well);
    let playing = app.playback.playing;
    p.text(play.center(), egui::Align2::CENTER_CENTER, if playing { "II" } else { ">" }, Tokens::ui(16.0), t.text);
    if play_resp.clicked() {
        let _ = crate::menus::invoke(app, &ctx, "playback.toggle", serde_json::json!({}));
    }
    let Some(cid) = app.session.active_comp_id() else { return };
    let Some(comp) = app.session.project.comp(cid) else { return };
    let dur = comp.duration.seconds().max(1e-3);
    let now = app.session.time().seconds().clamp(0.0, dur);
    // Scrub: a 28 px track, with an invisible hit area as tall as the bar.
    let track = egui::Rect::from_min_max(egui::pos2(play.max.x + 12.0, cy - 14.0), egui::pos2(bar.max.x - 12.0, cy + 14.0));
    p.rect_filled(track, 7.0, t.switch_well);
    let frac = (now / dur) as f32;
    let knob = egui::pos2(track.min.x + track.width() * frac, cy);
    p.rect_filled(egui::Rect::from_min_max(track.min, egui::pos2(knob.x, track.max.y)), 7.0, t.accent.gamma_multiply(0.55));
    p.circle_filled(knob, 9.0, t.accent);
    let resp = ui.interact(track.expand2(egui::vec2(0.0, 8.0)), egui::Id::unique("ours-fs-scrub"), egui::Sense::click_and_drag());
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
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("fullscreen hits already enlarged")
        return
    start = src.find(START)
    if start == -1:
        raise SystemExit("fullscreen bar not found (174_fullscreen_preview must run first)")
    path.write_text(src[:start] + NEW, encoding="utf-8")
    print("full-screen controls are finger sized")


if __name__ == "__main__":
    main()
