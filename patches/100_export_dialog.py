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
    let r = Rect::from_min_size(pos2(x, cy - 13.0), vec2(56.0, 26.0));
    let resp = ui.interact(r, egui::Id::unique("ours-export-button"), Sense::click());
    p.rect_filled(r, 4.0, t.switch_well);
    p.text(r.center(), Align2::CENTER_CENTER, "导出", Tokens::ui(12.0), t.text);
    if resp.clicked() {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-export-open"), true));
    }
    resp.on_hover_text("导出视频到相册（DCIM/EffectCraft）");
    export_window(app, ui.ctx());
    x + 62.0
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
    let fmt_id = egui::Id::new("ours-export-fmt");
    let mut fmt = ctx.data(|d| d.get_temp::<usize>(fmt_id).unwrap_or(0));
    let mut start = false;
    let mut cancel = false;
    let mut keep_open = open;
    let comp_info = app
        .session
        .active_comp()
        .map(|c| format!("当前工程：{}×{} · {:.2} fps", c.width, c.height, c.frame_rate.as_f64()))
        .unwrap_or_else(|| "未打开合成".to_string());
    egui::Window::new("导出视频")
        .open(&mut keep_open)
        .collapsible(false)
        .resizable(false)
        .show(ctx, |ui| {
            // Only when there is nothing to render: with a composition open this line read like an
            // error next to the composition's own details.
            if comp_info == "未打开合成" {
                ui.label("请先打开一个合成工程");
            }
            ui.label(egui::RichText::new(comp_info.clone()).weak());
            ui.add_space(6.0);
            ui.label("视频格式");
            egui::ComboBox::from_id_salt("ours-export-fmt-combo")
                .selected_text(["MP4 · H.264", "MOV · ProRes", "GIF 动图", "PNG 序列"][fmt.min(3)])
                .show_ui(ui, |ui| {
                    for (i, name) in ["MP4 · H.264", "MOV · ProRes", "GIF 动图", "PNG 序列"].iter().enumerate() {
                        ui.selectable_value(&mut fmt, i, *name);
                    }
                });
            ui.add_space(6.0);
            ui.label("导出分辨率");
            egui::ComboBox::from_id_salt("ours-export-res-combo")
                .selected_text(["跟随工程", "480p", "720p (HD)", "1080p (FHD)", "1440p (QHD)", "2160p (4K)"][res.min(5)])
                .show_ui(ui, |ui| {
                    for (i, name) in ["跟随工程", "480p", "720p (HD)", "1080p (FHD)", "1440p (QHD)", "2160p (4K)"].iter().enumerate() {
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
            let mut follow = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-preview-follow")).unwrap_or(true));
            // AfterCodecs' export sheet asks for one number: quality 0-100 (70 by default). Same
            // idea here: the slider is the CRF dial, and 70 is CRF 20 — its default position.
            let mut hq = ctx.data(|d| d.get_temp::<i32>(egui::Id::new("ours-export-hq")).unwrap_or(70));
            ui.label("画质（1–100）");
            if ui.add(egui::Slider::new(&mut hq, 1..=100)).changed() {
                ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-export-hq"), hq));
            }
            // Encoding speed, like AfterCodecs' speed presets: slower spends more time looking
            // for better matches, faster trades a little quality for time.
            let speed_id = egui::Id::new("ours-export-speed");
            let mut speed = ctx.data(|d| d.get_temp::<usize>(speed_id).unwrap_or(0));
            ui.label("编码速度");
            egui::ComboBox::from_id_salt("ours-export-speed-combo")
                .selected_text(["标准", "慢（画质优先）", "快（速度优先）"][speed.min(2)])
                .show_ui(ui, |ui| {
                    for (i, name) in ["标准", "慢（画质优先）", "快（速度优先）"].iter().enumerate() {
                        ui.selectable_value(&mut speed, i, *name);
                    }
                });
            ctx.data_mut(|d| d.insert_temp(speed_id, speed));
            // Draft quality renders much faster and is what you want while roughing out a cut.
            let mut draft = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-export-draft")).unwrap_or(false));
            if ui.checkbox(&mut draft, "草稿画质（更快）").changed() {
                ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-export-draft"), draft));
            }
            ui.label(
                egui::RichText::new("恒定质量编码：画质 70 ≈ AfterCodecs 默认 Q70（CRF 20）；草稿画质改用固定码率")
                    .weak(),
            );
            if ui.checkbox(&mut follow, "渲染时预览跟随").changed() {
                ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-preview-follow"), follow));
            }
            ui.label("导出完成后自动保存到手机相册 DCIM/EffectCraft，无需手动选择位置。");
            ui.add_space(8.0);
            ui.horizontal(|ui| {
                if ui.button("开始导出").clicked() {
                    start = true;
                }
                if ui.button("取消").clicked() {
                    cancel = true;
                }
            });
        });
    if cancel {
        keep_open = false;
    }
    open = keep_open;
    ctx.data_mut(|d| {
        d.insert_temp(open_id, open);
        d.insert_temp(res_id, res);
        d.insert_temp(fps_id, fps);
        d.insert_temp(fmt_id, fmt);
    });
    if start {
        let format = match fmt {
            1 => "prores",
            2 => "gif",
            3 => "png",
            _ => "h264",
        };
        let mut params = serde_json::json!({"format": format});
        if let Some((w, h)) = match res {
            1 => Some((854u32, 480u32)),
            2 => Some((1280, 720)),
            3 => Some((1920, 1080)),
            4 => Some((2560, 1440)),
            5 => Some((3840, 2160)),
            _ => None,
        } {
            params["resize"] = serde_json::json!({"width": w, "height": h});
        }
        if let Some(r) = match fps {
            1 => Some(24.0),
            2 => Some(30.0),
            3 => Some(60.0),
            4 => Some(120.0),
            5 => Some(144.0),
            6 => Some(240.0),
            _ => None,
        } {
            params["frameRate"] = serde_json::json!(r);
        }
        // One call carries the whole setup: the queue item is created with these settings, so
        // the file that comes out really is PNG/4K/120 as chosen.
        // Draft quality renders much faster; the checkbox above sets it.
        let draft = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-export-draft")).unwrap_or(false));
        params["quality"] = serde_json::json!(if draft { "draft" } else { "best" });
        if !draft {
            // Constant quality: H.264 reads the Output Module's codec quality as its CRF level
            // (8 + (100 - q) * 0.4), so 70 is CRF 20 — the AfterCodecs default's equivalent.
            let hq = ctx.data(|d| d.get_temp::<i32>(egui::Id::new("ours-export-hq")).unwrap_or(70));
            params["rateControl"] = serde_json::json!("quality");
            params["codecQuality"] = serde_json::json!(hq);
            let speed = ctx.data(|d| d.get_temp::<usize>(egui::Id::new("ours-export-speed")).unwrap_or(0));
            params["encodeSpeed"] = serde_json::json!(speed);
        }
        // 只保留这一次导出：先把队列里旧的项目去掉，否则每导一次都会多一项，
        // 点“渲染”时把历史上所有勾选的项重新渲染一遍。
        let existing = app.session.project.render_queue.len();
        for i in (1..=existing).rev() {
            let _ = crate::menus::invoke(app, ctx, "renderQueue.remove", serde_json::json!({"index": i}));
        }
        if crate::menus::invoke(app, ctx, "renderQueue.add", params).is_ok() {
            let _ = crate::menus::invoke(app, ctx, "renderQueue.render", serde_json::json!({}));
        }
        ctx.data_mut(|d| d.insert_temp(open_id, false));
    }
}
'''


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
    path.write_text(src + CODE, encoding="utf-8")
    print("export button and dialog installed")


if __name__ == "__main__":
    main()
