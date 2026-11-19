#!/usr/bin/env python3
"""AM（图 3）左侧那排图标：加一条竖向工具栏，只放**真实动作**。

截图里 AM 左边有一列小图标；我们没有那些具体工具，所以只挂真实可用的四个：
撤销 / 重做 / 播放 / 全屏。放在屏幕左侧、垂直居中偏上，宽度 46px。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AM_LEFT_RAIL_V1"

ANCHOR = '''                } else if ws == "blurrr" {'''

INSERT = '''                } else if ws == "am" || ws == "jianying" {
                    // EFFECTCRAFT_OURS_AM_LEFT_RAIL_V1 — AM 左侧竖排：撤销/重做/播放/全屏（都是真实动作）
                    let w = 46.0_f32;
                    let ch = 52.0_f32;
                    let rail = egui::Rect::from_min_size(
                        egui::pos2(screen.min.x + 6.0, screen.center().y - ch * 2.0),
                        egui::vec2(w, ch * 4.0),
                    );
                    ui.painter().rect_filled(rail, 12.0, self.tokens.panel_bg);
                    ui.painter().rect_stroke(
                        rail,
                        12.0,
                        egui::Stroke::new(1.0, self.tokens.separator),
                        egui::StrokeKind::Inside,
                    );
                    let undo_ready = !self.session.history.undo.is_empty();
                    let redo_ready = !self.session.history.redo.is_empty();
                    let items: [(&str, u8, bool); 4] = [
                        ("\\u{27f2}", 5, undo_ready),
                        ("\\u{27f3}", 6, redo_ready),
                        ("\\u{25b6}", 4, true),
                        ("\\u{26f6}", 7, true),
                    ];
                    for (i, (glyph, code, ready)) in items.iter().enumerate() {
                        let cell = egui::Rect::from_min_size(
                            egui::pos2(rail.min.x, rail.min.y + ch * i as f32),
                            egui::vec2(w, ch),
                        );
                        let resp = ui.interact(
                            cell,
                            egui::Id::unique(("ours-am-rail", *code as u64)),
                            egui::Sense::click(),
                        );
                        let hot = resp.hovered();
                        if hot {
                            ui.painter().rect_filled(
                                cell.shrink(3.0),
                                8.0,
                                self.tokens.accent.gamma_multiply(0.16),
                            );
                        }
                        ui.painter().text(
                            cell.center(),
                            egui::Align2::CENTER_CENTER,
                            *glyph,
                            Tokens::ui(15.0),
                            if *ready {
                                self.tokens.text
                            } else {
                                self.tokens.text_faint
                            },
                        );
                        if resp.clicked() && *ready {
                            fired = Some(*code);
                        }
                    }
                } else if ws == "blurrr" {'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("am rail already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("AM gets a left rail with undo/redo/play/fullscreen")


if __name__ == "__main__":
    main()
