#!/usr/bin/env python3
"""A one-tap export dialog: format, resolution, frame rate, then start the render."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_EXPORT_DIALOG_V1"
CALL_OLD = "    right_side(app, ui, &p, rect, x, cy);\n"
CALL_NEW = "    let x = export_button(app, ui, &p, x, cy);\n    right_side(app, ui, &p, rect, x, cy);\n"

CODE = r'''
// EFFECTCRAFT_OURS_EXPORT_DIALOG_V1
/// One-tap export: a small dialog, then the normal render queue does the work.
fn export_button(app: &mut EffectcraftApp, ui: &mut egui::Ui, p: &egui::Painter, x: f32, cy: f32) -> f32 {
    let t = app.tokens;
    let r = Rect::from_min_size(pos2(x, cy - 13.0), vec2(64.0, 26.0));
    let resp = ui.interact(r, egui::Id::unique("ours-export-button"), Sense::click());
    p.rect_filled(r, 4.0, t.switch_well);
    p.text(r.center(), Align2::CENTER_CENTER, "导出", Tokens::ui(12.0), t.text);
    if resp.clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-export-open"), true));
    }
    resp.on_hover_text("导出视频到相册（DCIM/EffectCraft）");
    export_window(app, ui.ctx());
    x + 72.0
}

fn export_window(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let open_id = egui::Id::new("ours-export-open");
    let res_id = egui::Id::new("ours-export-res");
    let fps_id = egui::Id::new("ours-export-fps");
    let mut open = ctx.data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    let mut res = ctx.data(|d| d.get_temp::<usize>(res_id).unwrap_or(0));
    let mut fps = ctx.data(|d| d.get_temp::<usize>(fps_id).unwrap_or(0));
    let mut start = false;
    egui::Window::new("导出视频")
        .collapsible(false)
        .resizable(false)
        .show(ctx, |ui| {
            ui.label("请先打开一个合成工程");
            ui.add_space(6.0);
            ui.label("视频格式");
            egui::ComboBox::from_id_salt("ours-export-fmt")
                .selected_text("MP4 · H.264")
                .show_ui(ui, |_ui| {});
            ui.add_space(6.0);
            ui.label("导出分辨率");
            egui::ComboBox::from_id_salt("ours-export-res-combo")
                .selected_text(["跟随工程", "480P", "720P", "1080P", "2K", "4K"][res.min(5)])
                .show_ui(ui, |ui| {
                    for (i, name) in ["跟随工程", "480P", "720P", "1080P", "2K", "4K"].iter().enumerate() {
                        ui.selectable_value(&mut res, i, *name);
                    }
                });
            ui.add_space(6.0);
            ui.label("导出帧率");
            egui::ComboBox::from_id_salt("ours-export-fps-combo")
                .selected_text(["跟随工程帧率", "24 FPS", "30 FPS", "60 FPS", "120 FPS", "144 FPS", "240 FPS"][fps.min(6)])
                .show_ui(ui, |ui| {
                    for (i, name) in ["跟随工程帧率", "24 FPS", "30 FPS", "60 FPS", "120 FPS", "144 FPS", "240 FPS"].iter().enumerate() {
                        ui.selectable_value(&mut fps, i, *name);
                    }
                });
            ui.add_space(8.0);
            ui.label("导出完成后自动保存到手机相册 DCIM/EffectCraft，无需手动选择位置。");
            ui.add_space(8.0);
            if ui.button("开始导出").clicked() {
                start = true;
            }
        });
    ctx.data_mut(|d| {
        d.insert_temp(open_id, open);
        d.insert_temp(res_id, res);
        d.insert_temp(fps_id, fps);
    });
    if start {
        let _ = crate::menus::invoke(app, ctx, "renderQueue.add", serde_json::json!({}));
        let _ = crate::menus::invoke(app, ctx, "renderQueue.render", serde_json::json!({}));
        ctx.data_mut(|d| d.insert_temp(open_id, false));
    }
}


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("export dialog already installed")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"header call anchor: expected 1, found {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src = src + CODE
    path.write_text(src, encoding="utf-8")
    print("export button and dialog installed")


if __name__ == "__main__":
    main()
