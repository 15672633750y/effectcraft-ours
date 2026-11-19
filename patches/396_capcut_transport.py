#!/usr/bin/env python3
"""CapCut（图 1）预览与时间线之间那排播放条：自绘一条，按钮全是真实动作。

截图里是「撤销 / 重做 / Full / 播放 / 上一帧 / 下一帧 / 全屏 / 网格 / 加号」。
我们没有"上一帧/下一帧"的命令，也没有"网格"，所以只挂真实可用的五个：
撤销、重做、播放、全屏、导入（加号）。宁可少，也不放假按钮。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CAPCUT_TRANSPORT_V1"

ANCHOR = '''        // EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1 — 时间线底部横向滚动条（自绘、可拖）'''

INSERT = '''        // EFFECTCRAFT_OURS_CAPCUT_TRANSPORT_V1 — CapCut 布局预览与时间线之间的播放条
        if self.ui.workspace == "capcut" {
            let tl = self
                .dock_rects
                .iter()
                .rev()
                .find(|(k, _)| *k == crate::dock::PanelKind::Timeline)
                .map(|(_, r)| *r);
            if let Some(tl) = tl {
                let bar = egui::Rect::from_min_size(
                    egui::pos2(tl.min.x + 6.0, tl.min.y - 46.0),
                    egui::vec2(tl.width() - 12.0, 40.0),
                );
                if bar.min.y > 0.0 {
                    let t = self.tokens;
                    ui.painter().rect_filled(bar, 10.0, t.panel_bg);
                    ui.painter().rect_stroke(
                        bar,
                        10.0,
                        egui::Stroke::new(1.0, t.separator),
                        egui::StrokeKind::Inside,
                    );
                    let undo_ready = !self.session.history.undo.is_empty();
                    let redo_ready = !self.session.history.redo.is_empty();
                    let items: [(&str, u8, bool); 5] = [
                        ("\\u{27f2}", 10, undo_ready),
                        ("\\u{27f3}", 11, redo_ready),
                        ("\\u{25b6}", 12, true),
                        ("\\u{26f6}", 13, true),
                        ("\\u{ff0b}", 14, true),
                    ];
                    let cw = bar.width() / items.len() as f32;
                    for (i, (glyph, code, ready)) in items.iter().enumerate() {
                        let cell = egui::Rect::from_min_size(
                            egui::pos2(bar.min.x + cw * i as f32, bar.min.y),
                            egui::vec2(cw, bar.height()),
                        );
                        let resp = ui.interact(
                            cell,
                            egui::Id::unique(("ours-capcut-transport", *code as u64)),
                            egui::Sense::click(),
                        );
                        let hot = resp.hovered();
                        if hot {
                            ui.painter().rect_filled(
                                cell.shrink(3.0),
                                8.0,
                                t.accent.gamma_multiply(0.16),
                            );
                        }
                        ui.painter().text(
                            cell.center(),
                            egui::Align2::CENTER_CENTER,
                            *glyph,
                            Tokens::ui(15.0),
                            if *ready { t.text } else { t.text_faint },
                        );
                        if resp.clicked() && *ready {
                            match *code {
                                10 => {
                                    if crate::menus::invoke(
                                        self,
                                        ui.ctx(),
                                        "edit.undo",
                                        serde_json::json!({}),
                                    )
                                    .is_ok()
                                    {
                                        self.ui.status = "已撤销".into();
                                    }
                                }
                                11 => {
                                    if crate::menus::invoke(
                                        self,
                                        ui.ctx(),
                                        "edit.redo",
                                        serde_json::json!({}),
                                    )
                                    .is_ok()
                                    {
                                        self.ui.status = "已恢复".into();
                                    }
                                }
                                12 => {
                                    self.playback.playing = !self.playback.playing;
                                    ui.ctx().request_repaint();
                                }
                                13 => {
                                    let id = egui::Id::new("ours-fullscreen-open");
                                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                                }
                                _ => {
                                    ui.ctx().data_mut(|d| {
                                        d.insert_temp(egui::Id::new("ours-import-open"), true)
                                    });
                                }
                            }
                        }
                    }
                }
            }
        }
        // EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1 — 时间线底部横向滚动条（自绘、可拖）'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("capcut transport already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("capcut gets its own transport bar")


if __name__ == "__main__":
    main()
