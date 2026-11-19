#!/usr/bin/env python3
"""竖屏品牌布局换成**我们自绘的顶栏**，不再画软件自带的那排 AE 工具（鼠标/移动/放大镜/眼睛…）。

参考 app 的顶栏只有：左标题、右几个动作。这里给：布局名 + 撤销 / 重做 / 播放 / 全屏，
全部接现有命令或现有状态（`edit.undo`、`edit.redo`、`playback.playing`、`ours-fullscreen-open`）。
AE 布局保持原样（横屏桌面工具条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHELL_HEADER_V1"

CALL_OLD = '''        let header = egui::Rect::from_min_size(egui::pos2(full.min.x, top), egui::vec2(full.width(), header_h));
        header::show(self, ui, header);'''

CALL_NEW = '''        let header = egui::Rect::from_min_size(egui::pos2(full.min.x, top), egui::vec2(full.width(), header_h));
        // EFFECTCRAFT_OURS_SHELL_HEADER_V1 — 竖屏布局用自绘顶栏，不再画 AE 的工具条
        if ours_portrait {
            ours_shell_header(self, ui, header);
        } else {
            header::show(self, ui, header);
        }'''

FN = '''
/// EFFECTCRAFT_OURS_SHELL_HEADER_V1 — 竖屏品牌布局的自绘顶栏。
/// 左：布局名；右：撤销 / 重做 / 播放 / 全屏。全部走现有命令或现有 UI 状态。
fn ours_shell_header(app: &mut EffectcraftApp, ui: &mut egui::Ui, bar: egui::Rect) {
    let t = app.tokens;
    let p = ui.painter().with_clip_rect(bar);
    p.rect_filled(bar, 0.0, t.header_bg);
    p.line_segment(
        [bar.left_bottom(), bar.right_bottom()],
        egui::Stroke::new(1.0, t.separator),
    );
    let name = match app.ui.workspace.as_str() {
        "capcut" => "CapCut",
        "kuaishou" => "快影",
        "blurrr" => "Blurrr",
        "am" | "jianying" => "AM",
        _ => "布局",
    };
    p.text(
        egui::pos2(bar.min.x + 14.0, bar.center().y),
        egui::Align2::LEFT_CENTER,
        name,
        Tokens::semibold(13.0),
        t.text,
    );
    let undo_ready = !app.session.history.undo.is_empty();
    let redo_ready = !app.session.history.redo.is_empty();
    let playing = app.playback.playing;
    let cells: [(&str, &str, bool); 4] = [
        ("undo", "\\u{27f2}", undo_ready),
        ("redo", "\\u{27f3}", redo_ready),
        ("play", if playing { "\\u{23f8}" } else { "\\u{25b6}" }, true),
        ("full", "\\u{26f6}", true),
    ];
    let mut x = bar.max.x - 8.0;
    for (key, glyph, ready) in cells.iter().rev() {
        let cell = egui::Rect::from_min_size(
            egui::pos2(x - 34.0, bar.center().y - 13.0),
            egui::vec2(34.0, 26.0),
        );
        let resp = ui.interact(cell, egui::Id::unique(("ours-shell", *key)), egui::Sense::click());
        let hot = resp.hovered();
        if hot {
            p.rect_filled(cell.shrink(2.0), 6.0, t.switch_well);
        }
        p.text(
            cell.center(),
            egui::Align2::CENTER_CENTER,
            *glyph,
            Tokens::ui(13.0),
            if *ready { t.text } else { t.text_faint },
        );
        if resp.clicked() && *ready {
            match *key {
                "undo" => {
                    if crate::menus::invoke(app, ui.ctx(), "edit.undo", serde_json::json!({})).is_ok() {
                        app.ui.status = "已撤销".into();
                    }
                }
                "redo" => {
                    if crate::menus::invoke(app, ui.ctx(), "edit.redo", serde_json::json!({})).is_ok() {
                        app.ui.status = "已恢复".into();
                    }
                }
                "play" => {
                    app.playback.playing = !app.playback.playing;
                    ui.ctx().request_repaint();
                }
                _ => {
                    let id = egui::Id::new("ours-fullscreen-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
            }
        }
        x -= 36.0;
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("shell header already present")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src = src.rstrip("\n") + "\n" + FN
    path.write_text(src, encoding="utf-8")
    print("portrait layouts get our own header")


if __name__ == "__main__":
    main()
