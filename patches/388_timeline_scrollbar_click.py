#!/usr/bin/env python3
"""时间线横向滚动条：点轨道也能跳（不用非抓住滑块）。

在 387 的基础上给轨道加 click：按点击位置换算成进度，直接改 `ui.timeline.start`。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_CLICK_V1"

OLD = '''                            let resp = ui.interact(
                                thumb.expand2(egui::vec2(0.0, 10.0)),
                                egui::Id::unique("ours-timeline-hscroll"),
                                egui::Sense::drag(),
                            );'''

NEW = '''                            let resp = ui.interact(
                                thumb.expand2(egui::vec2(0.0, 10.0)),
                                egui::Id::unique("ours-timeline-hscroll"),
                                egui::Sense::drag(),
                            );
                            // EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_CLICK_V1 — 点轨道直接跳
                            let track_resp = ui.interact(
                                egui::Rect::from_min_size(
                                    track.min,
                                    egui::vec2(track.width(), track.height() + 12.0),
                                ),
                                egui::Id::unique("ours-timeline-hscroll-track"),
                                egui::Sense::click(),
                            );
                            if track_resp.clicked() {
                                if let Some(pos) = track_resp.interact_pointer_pos() {
                                    let span = (track.width() - thumb_w).max(1.0);
                                    let ratio =
                                        ((pos.x - track.min.x) - thumb_w * 0.5) / span;
                                    self.ui.timeline.start = (ratio.clamp(0.0, 1.0) as f64
                                        * max_start)
                                        .clamp(0.0, max_start);
                                    ui.ctx().request_repaint();
                                }
                            }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("track click already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("timeline scrollbar track is clickable")


if __name__ == "__main__":
    main()
