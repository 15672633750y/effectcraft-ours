#!/usr/bin/env python3
"""CapCut 顶栏右侧那个「1080P ▾」胶囊（图 1 右上）。

我们导出的分辨率就在导出对话框里，所以这个胶囊点开导出对话框——
显示当前导出分辨率，点了能改，不是装饰。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HEADER_PILL_V1"

ANCHOR = '''    let undo_ready = !app.session.history.undo.is_empty();
    let redo_ready = !app.session.history.redo.is_empty();
    let playing = app.playback.playing;
    let cells: [(&str, &str, bool); 4] = ['''

INSERT = '''    // EFFECTCRAFT_OURS_HEADER_PILL_V1 — CapCut 顶栏的「1080P」胶囊：显示导出分辨率，点开导出对话框
    if app.ui.workspace == "capcut" {
        let idx = ui
            .ctx()
            .data(|d| d.get_temp::<usize>(egui::Id::new("ours-export-res")).unwrap_or(0));
        let res = ["跟随工程", "480P", "720P", "1080P", "1440P", "2160P"]
            [idx.min(5)]
        .to_string();
        let pill = egui::Rect::from_min_size(
            egui::pos2(bar.max.x - 34.0 * 4.0 - 74.0, bar.center().y - 12.0),
            egui::vec2(68.0, 24.0),
        );
        let resp = ui.interact(pill, egui::Id::unique("ours-header-res"), egui::Sense::click());
        p.rect_filled(
            pill,
            12.0,
            if resp.hovered() { t.switch_well } else { t.field_bg },
        );
        p.text(
            pill.center(),
            egui::Align2::CENTER_CENTER,
            res,
            Tokens::ui(11.0),
            t.text,
        );
        if resp.clicked() {
            let id = egui::Id::new("ours-export-open");
            ui.ctx().data_mut(|d| d.insert_temp(id, true));
        }
    }
    let undo_ready = !app.session.history.undo.is_empty();
    let redo_ready = !app.session.history.redo.is_empty();
    let playing = app.playback.playing;
    let cells: [(&str, &str, bool); 4] = ['''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("header pill already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("capcut header gained a resolution pill")


if __name__ == "__main__":
    main()
