#!/usr/bin/env python3
"""面板里放真正的功能方块：P/S/R/T/A、裁剪、裁剪前/后、U。

Each tile is a small transparent box with the name on top and After Effects' key underneath, and it
runs the matching command through the session — the same route a menu entry takes.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_TILES_V1"

CALL_OLD = "        shortcut_panel(ui, full);\n"
CALL_NEW = "        shortcut_panel(self, ui, full);\n"

SIG_OLD = "fn shortcut_panel(ui: &mut egui::Ui, full: egui::Rect) {"
SIG_NEW = "fn shortcut_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {"

BODY_OLD = '''    p.text(r.center_top() + egui::vec2(0.0, 26.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(14.0), egui::Color32::from_rgb(242, 243, 247));
    p.text(r.center() + egui::vec2(0.0, 10.0), egui::Align2::CENTER_CENTER, "（功能加入中）", Tokens::ui(12.0), egui::Color32::from_gray(180));
'''
BODY_NEW = '''    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "快捷键", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));
    // EFFECTCRAFT_OURS_SHORTCUT_TILES_V1 — 功能方块：上面大字，下面键位
    let tiles: &[(&str, &str, &str, serde_json::Value)] = &[
        ("位置", "P", "layer.revealProperty", serde_json::json!({"prop": "position"})),
        ("缩放", "S", "layer.revealProperty", serde_json::json!({"prop": "scale"})),
        ("旋转", "R", "layer.revealProperty", serde_json::json!({"prop": "rotation"})),
        ("不透明度", "T", "layer.revealProperty", serde_json::json!({"prop": "opacity"})),
        ("锚点", "A", "layer.revealProperty", serde_json::json!({"prop": "anchor"})),
        ("裁剪", "Ctrl+Shift+D", "edit.splitLayer", serde_json::json!({})),
        ("裁剪前", "Alt+[", "layer.stretchInToTime", serde_json::json!({})),
        ("裁剪后", "Alt+]", "layer.stretchOutToTime", serde_json::json!({})),
        ("关键帧", "U", "anim.reveal", serde_json::json!({"kind": "keyframes"})),
    ];
    let tw = 56.0;
    let th = 40.0;
    let gap = 6.0;
    let cols = 3usize;
    let rows = tiles.len().div_ceil(cols);
    let grid_w = cols as f32 * tw + (cols as f32 - 1.0) * gap;
    let grid_h = rows as f32 * th + (rows as f32 - 1.0) * gap;
    let origin = egui::pos2(r.center().x - grid_w * 0.5, r.center().y - grid_h * 0.5 + 10.0);
    let mut run: Option<&str> = None;
    let mut payload = serde_json::Value::Null;
    for (i, (name, key, cmd, args)) in tiles.iter().enumerate() {
        let cx = i % cols;
        let cy = i / cols;
        let tr = egui::Rect::from_min_size(
            origin + egui::vec2(cx as f32 * (tw + gap), cy as f32 * (th + gap)),
            egui::vec2(tw, th),
        );
        let id = egui::Id::unique(("ours-tile", *cmd, cx, cy));
        let resp = ui.interact(tr, id, egui::Sense::click());
        let hot = resp.hovered();
        p.rect_filled(tr, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, if hot { 40 } else { 18 }));
        p.rect_stroke(tr, 8.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, if hot { 140 } else { 80 })), egui::StrokeKind::Inside);
        p.text(tr.center_top() + egui::vec2(0.0, 12.0), egui::Align2::CENTER_CENTER, *name, Tokens::ui(11.0), egui::Color32::from_rgb(244, 245, 248));
        p.text(tr.center_top() + egui::vec2(0.0, 27.0), egui::Align2::CENTER_CENTER, *key, Tokens::ui(8.5), egui::Color32::from_gray(170));
        if resp.clicked() {
            run = Some(cmd);
            payload = args.clone();
        }
    }
    if let Some(cmd) = run {
        match app.session.execute(cmd, payload) {
            Ok(_) => {}
            Err(e) => {
                app.ui.status = format!("{e}");
            }
        }
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tiles already installed")
        return
    for old, new in ((CALL_OLD, CALL_NEW), (SIG_OLD, SIG_NEW), (BODY_OLD, BODY_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:32]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("shortcut tiles wired to commands")


if __name__ == "__main__":
    main()
