#!/usr/bin/env python3
"""「快捷」悬浮球：可拖动、贴边半隐藏（极低不透明度）、点开一个空面板。

这一批只做外观与手感，不含任何快捷键功能。

* 圆形图标（仓库里的 assets/shortcut-btn.png，按行高绘制）
* 轻点 → 展开/收起空面板；按住拖动 → 跟手移动
* 松手靠近屏幕左右/下边缘 → 贴边，并把不透明度降到极低（只留一点可见度）
* 再次交互（点一下）→ 恢复正常不透明度并弹出面板
* 位置与贴边状态记在 egui 的临时数据里，重启回到默认位置
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_BALL_V1"

CALL_OLD = "        self.draw_toast(ui, full, lift);\n"
CALL_NEW = CALL_OLD + "        // EFFECTCRAFT_OURS_SHORTCUT_BALL_V1 — 悬浮的“快捷”球（本批只做外观与手感）\n        shortcut_ball(ui, full);\n"

FUNC = r'''

/// EFFECTCRAFT_OURS_SHORTCUT_BALL_V1 — 可拖动、可贴边的「快捷」悬浮球 + 空面板。
static SHORTCUT_ICON: &[u8] = include_bytes!("../../assets/shortcut-btn.png");

#[derive(Clone, Copy, PartialEq)]
enum BallEdge {
    Free,
    Left,
    Right,
    Bottom,
}

fn shortcut_ball(ui: &mut egui::Ui, full: egui::Rect) {
    let ctx = ui.ctx().clone();
    let size = 46.0;
    let pos_id = egui::Id::unique("shortcut-ball-pos");
    let edge_id = egui::Id::unique("shortcut-ball-edge");
    let open_id = egui::Id::unique("shortcut-ball-open");
    let tex_id = egui::Id::unique("shortcut-ball-tex");
    let default = egui::pos2(full.max.x - size - 18.0, full.max.y - 260.0);
    let mut pos: egui::Pos2 = ctx.data(|d| d.get_temp::<egui::Pos2>(pos_id)).unwrap_or(default);
    let mut edge: u8 = ctx.data(|d| d.get_temp::<u8>(edge_id)).unwrap_or(0);
    let mut open: bool = ctx.data(|d| d.get_temp::<bool>(open_id)).unwrap_or(false);
    let tex = ctx.data(|d| d.get_temp::<Option<egui::TextureHandle>>(tex_id)).unwrap_or_else(|| {
        let tex = image::load_from_memory_with_format(SHORTCUT_ICON, image::ImageFormat::Png).ok().map(|img| {
            let img = img.to_rgba8();
            let ci = egui::ColorImage::from_rgba_unmultiplied([img.width() as usize, img.height() as usize], img.as_raw());
            ctx.load_texture("shortcut-ball", ci, egui::TextureOptions::LINEAR)
        });
        ctx.data_mut(|d| d.insert_temp(tex_id, tex.clone()));
        tex
    });
    let rect = egui::Rect::from_min_size(pos, egui::vec2(size, size));
    egui::Area::new(egui::Id::unique("shortcut-ball-area"))
        .order(egui::Order::Foreground)
        .fixed_pos(pos)
        .show(&ctx, |area_ui| {
            let (r, resp) = area_ui.allocate_exact_size(egui::vec2(size, size), egui::Sense::click_and_drag());
            let resp = resp.on_hover_text("快捷");
            if resp.dragged() {
                pos += resp.drag_delta();
                pos.x = pos.x.clamp(full.min.x + 4.0, full.max.x - size - 4.0);
                pos.y = pos.y.clamp(full.min.y + 4.0, full.max.y - size - 4.0);
                edge = 0;
            }
            if resp.drag_stopped() {
                // 贴边：左右 24px 内、底部 48px 内吸附，并降到极低不透明度
                if pos.x - full.min.x < 24.0 {
                    pos.x = full.min.x - size * 0.55;
                    edge = 1;
                } else if full.max.x - (pos.x + size) < 24.0 {
                    pos.x = full.max.x - size * 0.45;
                    edge = 2;
                } else if full.max.y - (pos.y + size) < 48.0 {
                    pos.y = full.max.y - size * 0.5;
                    edge = 3;
                }
            }
            if resp.clicked() {
                open = !open;
                edge = 0;
            }
            let alpha = if edge != 0 && !open { 44 } else { 255 };
            let tint = egui::Color32::from_white_alpha(alpha);
            let p = area_ui.painter();
            p.circle_filled(r.center(), size * 0.5, egui::Color32::from_black_alpha((alpha as f32 * 0.25) as u8));
            if let Some(t) = &tex {
                p.image(t.id(), r, egui::Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0)), tint);
            } else {
                p.circle_filled(r.center(), size * 0.5, tint);
            }
            let _ = rect;
        });
    // 空面板：透明底、尽量小、显示在球的左侧
    if open {
        let panel = egui::Rect::from_min_size(
            egui::pos2((pos.x - 168.0).max(full.min.x + 8.0), pos.y.min(full.max.y - 160.0)),
            egui::vec2(160.0, 120.0),
        );
        egui::Area::new(egui::Id::unique("shortcut-ball-panel"))
            .order(egui::Order::Foreground)
            .fixed_pos(panel.min)
            .show(&ctx, |pui| {
                pui.set_min_size(panel.size());
                let r = egui::Rect::from_min_size(pui.min_rect().min, panel.size());
                let p = pui.painter();
                p.rect_filled(r, 12.0, egui::Color32::from_rgba_unmultiplied(10, 10, 12, 90));
                p.rect_stroke(r, 12.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 70)), egui::StrokeKind::Inside);
                p.text(r.center(), egui::Align2::CENTER_CENTER, "快捷键\n（待添加）", Tokens::ui(13.0), egui::Color32::from_rgb(240, 241, 245));
            });
    }
    ctx.data_mut(|d| {
        d.insert_temp(pos_id, pos);
        d.insert_temp(edge_id, edge);
        d.insert_temp(open_id, open);
    });
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("shortcut ball already installed")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    src += FUNC
    path.write_text(src, encoding="utf-8")
    print("shortcut ball installed")


if __name__ == "__main__":
    main()
