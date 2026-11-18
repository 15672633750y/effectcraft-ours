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
/// 可拖动；整块面板吃掉点击（不会穿到下面的时间线）；套用结果如实显示。
fn preset_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {
    let open_id = egui::Id::unique("ours-preset-open");
    if !ui.ctx().data(|d| d.get_temp::<bool>(open_id).unwrap_or(false)) {
        return;
    }
    let pos_id = egui::Id::unique("ours-preset-pos");
    let notice_id = egui::Id::unique("ours-preset-notice");
    let scroll_id = egui::Id::unique("ours-preset-scroll");
    // 限高 60vh，内容超出就在面板内滚动（和「快捷键」面板同一套圆角/材质）。
    let size = egui::vec2(280.0, (full.height() * 0.6).min(380.0));
    let mut top_left = ui
        .ctx()
        .data(|d| d.get_temp::<egui::Pos2>(pos_id))
        .unwrap_or_else(|| full.center() - size * 0.5);
    let r = egui::Rect::from_min_size(top_left, size);
    // 整块面板先登记一个 click_and_drag：它在这帧靠后注册，优先级高于时间线等面板，
    // 所以面板上的点击不会穿过去；拖动就是移动面板。
    let body = ui.interact(r, egui::Id::unique("ours-preset-body"), egui::Sense::click_and_drag());
    if body.dragged() {
        top_left += body.drag_delta();
        top_left.x = top_left.x.clamp(full.min.x - size.x + 60.0, full.max.x - 60.0);
        top_left.y = top_left.y.clamp(full.min.y, full.max.y - 40.0);
        ui.ctx().data_mut(|d| d.insert_temp(pos_id, top_left));
    }
    let r = egui::Rect::from_min_size(top_left, size);
    let p = ui.painter().with_clip_rect(full);
    p.rect_filled(r, crate::panel_style::RADIUS, crate::panel_style::bg());
    p.rect_stroke(r, crate::panel_style::RADIUS, egui::Stroke::new(1.0, crate::panel_style::border()), egui::StrokeKind::Inside);
    p.text(r.center_top() + egui::vec2(0.0, 22.0), egui::Align2::CENTER_CENTER, "预设库", Tokens::ui(13.0), egui::Color32::from_rgb(242, 243, 247));
    p.text(
        r.center_top() + egui::vec2(0.0, 38.0),
        egui::Align2::CENTER_CENTER,
        "拖动可移动",
        Tokens::ui(9.5),
        egui::Color32::from_rgb(120, 124, 132),
    );

    // 保存预设后置了 ours-presets-dirty：立刻重拉，不用关掉再打开。
    let dirty = ui.ctx().data(|d| d.get_temp::<bool>(egui::Id::new("ours-presets-dirty")).unwrap_or(false));
    if dirty {
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::new("ours-presets-dirty"), false));
        ui.ctx().request_repaint();
    }
    let list = app
        .session
        .execute("ours.presets", serde_json::json!({ "refresh": dirty }))
        .ok()
        .and_then(|v| v.get("items").cloned())
        .and_then(|v| v.as_array().cloned())
        .unwrap_or_default();

    if list.is_empty() {
        p.text(r.center(), egui::Align2::CENTER_CENTER, "把 .ffx 放到\nDCIM/EffectCraft/Presets/", Tokens::ui(11.0), egui::Color32::from_rgb(160, 163, 172));
    }

    let mut notice: Option<String> = ui.ctx().data(|d| d.get_temp::<String>(notice_id));
    // 滚轮：只在指针落在面板内时响应，避免抢时间线的滚动。
    let mut scroll = ui.ctx().data(|d| d.get_temp::<f32>(scroll_id)).unwrap_or(0.0);
    if body.hovered() {
        let delta = ui.input(|i| i.smooth_scroll_delta.y);
        if delta.abs() > 0.0 {
            scroll = (scroll - delta).clamp(0.0, (list.len() as f32 * 50.0 - (size.y - 110.0)).max(0.0));
            ui.ctx().data_mut(|d| d.insert_temp(scroll_id, scroll));
        }
    }
    let view = egui::Rect::from_min_max(
        egui::pos2(r.min.x + 8.0, r.min.y + 50.0),
        egui::pos2(r.max.x - 8.0, r.max.y - 34.0),
    );
    let mut y = view.min.y - scroll;
    for item in list.iter() {
        let name = item.get("name").and_then(|v| v.as_str()).unwrap_or("");
        let path = item.get("path").and_then(|v| v.as_str()).unwrap_or("");
        let kind = item.get("kind").and_then(|v| v.as_str()).unwrap_or("");
        // .gp 不是「不支持」：237_gp_presets 会解析它的 JSON 参数并套用，238 补几何参数。
        // 之前这里硬编码成 `kind != "gp"` 才导致点不了。
        let supported = true;
        let row = egui::Rect::from_min_size(egui::pos2(r.min.x + 14.0, y), egui::vec2(size.x - 28.0, crate::panel_style::ROW_H));
        // 滚出视口的行直接跳过（自绘面板没有 clip，手动剔除）。
        if row.max.y < view.min.y || row.min.y > view.max.y {
            y += crate::panel_style::ROW_H + 6.0;
            continue;
        }
        let p = ui.painter().with_clip_rect(view);
        p.rect_filled(row, 8.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, if supported { 18 } else { 8 }));
        let text_color = if supported {
            egui::Color32::from_rgb(235, 237, 242)
        } else {
            egui::Color32::from_rgba_unmultiplied(235, 237, 242, 110)
        };
        p.text(row.center() - egui::vec2(if supported { 0.0 } else { 22.0 }, 0.0), egui::Align2::CENTER_CENTER, name, Tokens::ui(11.0), text_color);
        // 右侧标格式：本机预设 / AE 二进制 / AE 文本 / Sapphire .gp（由 257 读文件头给出）
        let kind_label = item.get("label").and_then(|x| x.as_str()).unwrap_or("");
        if !kind_label.is_empty() {
            p.text(
                egui::pos2(row.max.x - 10.0, row.center().y),
                egui::Align2::RIGHT_CENTER,
                kind_label,
                Tokens::ui(9.5),
                egui::Color32::from_rgba_unmultiplied(180, 184, 192, 170),
            );
        }
        // 全部可点，不再画「敬请期待」标签。
        // 行在面板内后注册，所以行优先于整块面板
        let resp = ui.interact(row, egui::Id::new(("ours-preset", name)), egui::Sense::click());
        if resp.clicked() {
            {
                match app.session.execute("ours.applyPreset", serde_json::json!({ "path": path })) {
                    Ok(v) => {
                        let n = v.get("effects").and_then(|x| x.as_u64()).unwrap_or(0);
                        let missing: Vec<String> = v
                            .get("missing")
                            .and_then(|x| x.as_array())
                            .map(|a| a.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
                            .unwrap_or_default();
                        notice = Some(if n > 0 {
                            if missing.is_empty() {
                                format!("已应用 {n} 个效果")
                            } else {
                                format!("已应用 {n} 个效果（缺失 {} 个）", missing.len())
                            }
                        } else if missing.is_empty() {
                            "此预设的效果本软件都没有".to_string()
                        } else {
                            let head: Vec<String> = missing.iter().take(5).cloned().collect();
                            format!("此预设的效果本软件都没有：{}", head.join("、"))
                        });
                    }
                    Err(e) => {
                        let text = e.to_string();
                        notice = Some(if kind == "gp" {
                            format!("无法解析该 .gp 预设：{text}")
                        } else {
                            text
                        });
                    }
                }
            }
        }
        y += crate::panel_style::ROW_H + 6.0;
    }

    // 结果提示：贴在面板底部
    if let Some(msg) = &notice {
        if !msg.is_empty() {
            let shown: String = msg.chars().take(46).collect();
            p.text(
                egui::pos2(r.center().x, r.max.y - 18.0),
                egui::Align2::CENTER_CENTER,
                shown,
                Tokens::ui(10.0),
                egui::Color32::from_rgb(232, 196, 128),
            );
        }
    }
    ui.ctx().data_mut(|d| d.insert_temp(notice_id, notice.unwrap_or_default()));

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
