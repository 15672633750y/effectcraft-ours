#!/usr/bin/env python3
"""AM 左侧竖栏的三个新动作：撤销(5) / 重做(6) / 全屏(7)。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RAIL_ACTIONS_V1"

OLD = '''                Some(4) => {
                    self.playback.playing = !self.playback.playing;
                    ui.ctx().request_repaint();
                }
                _ => {}'''

NEW = '''                Some(4) => {
                    self.playback.playing = !self.playback.playing;
                    ui.ctx().request_repaint();
                }
                // EFFECTCRAFT_OURS_RAIL_ACTIONS_V1 — AM 左侧竖栏：撤销 / 重做 / 全屏
                Some(5) => {
                    if crate::menus::invoke(self, ui.ctx(), "edit.undo", serde_json::json!({}))
                        .is_ok()
                    {
                        self.ui.status = "已撤销".into();
                    }
                }
                Some(6) => {
                    if crate::menus::invoke(self, ui.ctx(), "edit.redo", serde_json::json!({}))
                        .is_ok()
                    {
                        self.ui.status = "已恢复".into();
                    }
                }
                Some(7) => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("rail actions already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("undo/redo/fullscreen wired for the AM rail")


if __name__ == "__main__":
    main()
