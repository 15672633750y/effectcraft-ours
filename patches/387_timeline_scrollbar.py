#!/usr/bin/env python3
"""时间线底部自绘一条**能拖的横向滚动条**。

上游时间线没有可拖的横向滚动条（只有捏合/滚轮），用户看到的细线不是它。
这里在时间轴面板底部画轨道 + 滑块：拖动改 `ui.timeline.start`，按 pps 换算，限制在 0..max_start。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1"

ANCHOR = '''                Some(4) => {
                    self.playback.playing = !self.playback.playing;
                    ui.ctx().request_repaint();
                }
                _ => {}
            }
        }'''

INSERT = ANCHOR + '''
        // EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1 — 时间线底部横向滚动条（自绘、可拖）
        {
            let tl_rect = self
                .dock_rects
                .iter()
                .rev()
                .find(|(k, _)| *k == crate::dock::PanelKind::Timeline)
                .map(|(_, r)| *r);
            if let Some(tl) = tl_rect {
                if let (Some(pps), Some(cid)) =
                    (self.ui.timeline.pps, self.session.active_comp_id())
                {
                    if let Some(comp) = self.session.project.comp_arc(cid) {
                        let total = comp.duration.seconds().max(0.001);
                        let visible = (tl.width() as f64 / pps.max(0.0001)).min(total);
                        let max_start = (total - visible).max(0.0);
                        if max_start > 0.0 && tl.height() > 60.0 {
                            let track = egui::Rect::from_min_size(
                                egui::pos2(tl.min.x + 6.0, tl.max.y - 12.0),
                                egui::vec2((tl.width() - 12.0).max(40.0), 8.0),
                            );
                            let t = self.tokens;
                            ui.painter().rect_filled(track, 4.0, t.switch_well);
                            let frac = (visible / total) as f32;
                            let thumb_w = (track.width() * frac).max(40.0);
                            let progress =
                                (self.ui.timeline.start / max_start).clamp(0.0, 1.0) as f32;
                            let thumb_x =
                                track.min.x + (track.width() - thumb_w) * progress;
                            let thumb = egui::Rect::from_min_size(
                                egui::pos2(thumb_x, track.min.y),
                                egui::vec2(thumb_w, track.height()),
                            );
                            let resp = ui.interact(
                                thumb.expand2(egui::vec2(0.0, 10.0)),
                                egui::Id::unique("ours-timeline-hscroll"),
                                egui::Sense::drag(),
                            );
                            if resp.dragged() {
                                let span = (track.width() - thumb_w).max(1.0);
                                let ratio = (resp.drag_delta().x / span) as f64;
                                self.ui.timeline.start = (self.ui.timeline.start
                                    + ratio * max_start)
                                    .clamp(0.0, max_start);
                                ui.ctx().request_repaint();
                            }
                            let hot = resp.hovered() || resp.dragged();
                            ui.painter().rect_filled(
                                thumb,
                                4.0,
                                if hot { t.accent } else { t.text_dim },
                            );
                        }
                    }
                }
            }
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("timeline scrollbar already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("timeline gets a self-drawn horizontal scrollbar")


if __name__ == "__main__":
    main()
