#!/usr/bin/env python3
"""预设库面板：点头像旁边的「预设」条目，列出文件夹里的 .ffx / .gp，点一下套到选中图层。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_PANEL_V1"

CALL_OLD = "        shortcut_panel(self, ui, full);\n"
CALL_NEW = "        shortcut_panel(self, ui, full);\n        preset_panel(self, ui, full);\n"

FN = r'''

/// EFFECTCRAFT_OURS_PRESET_PANEL_V1 — 预设库窗口：列出 DCIM/EffectCraft/Presets 里的预设。
fn preset_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {
    let open_id = egui::Id::unique("ours-preset-open");
    if !ui.ctx().data(|d| d.get_temp::<bool>(open_id).unwrap_or(false)) {
        return;
    }
    let size = egui::vec2(280.0, 360.0);
    let r = egui::Rect::from_min_size(egui::pos2(full.center().x - size.x * 0.5, full.center().y - size.y * 0.5), size);
    let p = ui.painter().with_clip_rect(full);
    p.rect_filled(r, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 235));
    p.rect_stroke(r, 14.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 90)), egui::StrokeKind::Inside);
    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "预设库", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));

    let list = app
        .session
        .execute("ours.presets", serde_json::json!({}))
        .ok()
        .and_then(|v| v.get("items").cloned())
        .and_then(|v| v.as_array().cloned())
        .unwrap_or_default();

    if list.is_empty() {
        p.text(r.center(), egui::Align2::CENTER_CENTER, "把 .ffx / .gp 放到\nDCIM/EffectCraft/Presets/", Tokens::ui(11.0), egui::Color32::from_rgb(160, 163, 172));
    }

    let mut y = r.min.y + 46.0;
    for item in list.iter().take(9) {
        let name = item.get("name").and_then(|v| v.as_str()).unwrap_or("");
        let path = item.get("path").and_then(|v| v.as_str()).unwrap_or("");
        let row = egui::Rect::from_min_size(egui::pos2(r.min.x + 14.0, y), egui::vec2(size.x - 28.0, 28.0));
        p.rect_filled(row, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 18));
        p.text(row.center(), egui::Align2::CENTER_CENTER, name, Tokens::ui(11.0), egui::Color32::from_rgb(235, 237, 242));
        let resp = ui.interact(row, egui::Id::new(("ours-preset", name)), egui::Sense::click());
        if resp.clicked() {
            let _ = app.session.execute("ours.applyPreset", serde_json::json!({ "path": path }));
        }
        y += 32.0;
    }

    // 点击窗口外关闭
    let outside = ui.input(|i| i.pointer.primary_clicked() && i.pointer.interact_pos().map_or(false, |q| !r.contains(q)));
    if outside {
        ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset panel already present")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("preset panel added")


if __name__ == "__main__":
    main()
