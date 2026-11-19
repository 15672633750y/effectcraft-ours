#!/usr/bin/env python3
"""Blurrr 顶部条的四个动作接线：10 撤销 / 11 重做 / 12 播放 / 13 导出。

之前这些 code 只在 CapCut 播放条内部处理，Blurrr 顶部条把它们丢给 `match fired` 会落到 `_ => {}`，
点了没反应。这里在 `match fired` 里补齐。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BLURRR_ACTIONS_V1"

OLD = '''                Some(8) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''

NEW = '''                Some(8) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                // EFFECTCRAFT_OURS_BLURRR_ACTIONS_V1 — Blurrr 顶部条
                Some(10) => {
                    if crate::menus::invoke(self, ui.ctx(), "edit.undo", serde_json::json!({}))
                        .is_ok()
                    {
                        self.ui.status = "已撤销".into();
                    }
                }
                Some(11) => {
                    if crate::menus::invoke(self, ui.ctx(), "edit.redo", serde_json::json!({}))
                        .is_ok()
                    {
                        self.ui.status = "已恢复".into();
                    }
                }
                Some(12) => {
                    self.playback.playing = !self.playback.playing;
                    ui.ctx().request_repaint();
                }
                Some(13) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("blurrr actions already wired")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("blurrr top actions wired into the shared handler")


if __name__ == "__main__":
    main()
