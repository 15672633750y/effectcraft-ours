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
    // 最大高度对齐快捷键面板（196x320），超出内部滚动，标题栏固定。
    let size = egui::vec2(280.0, (full.height() * 0.6).min(320.0));
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

    // —— 搜索框 + 后缀筛选芯片（与列表是「与」关系）——
    let search_id = egui::Id::unique("ours-preset-search");
    let filter_id = egui::Id::unique("ours-preset-filter");
    let mut query: String = ui.ctx().data(|d| d.get_temp::<String>(search_id).unwrap_or_default());
    let mut filter: u8 = ui.ctx().data(|d| d.get_temp::<u8>(filter_id).unwrap_or(0));
    let field = egui::Rect::from_min_size(egui::pos2(r.min.x + 12.0, r.min.y + 48.0), egui::vec2(size.x - 24.0, 34.0));
    p.rect_filled(field, 8.0, t.field_bg);
    p.text(
        egui::pos2(field.min.x + 14.0, field.center().y),
        egui::Align2::CENTER_CENTER,
        "\u{2315}",
        Tokens::ui(14.0),
        egui::Color32::from_rgb(150, 154, 162),
    );
    let text_rect = egui::Rect::from_min_max(
        egui::pos2(field.min.x + 26.0, field.min.y),
        egui::pos2(field.max.x - if query.is_empty() { 8.0 } else { 30.0 }, field.max.y),
    );
    let edit = egui::TextEdit::singleline(&mut query)
        .hint_text("搜索预设…")
        .text_color(egui::Color32::from_rgb(238, 240, 245))
        .font(Tokens::ui(11.0))
        .frame(false)
        .margin(egui::Margin::symmetric(2, 9));
    if ui.put(text_rect, edit).changed() {
        ui.ctx().data_mut(|d| d.insert_temp(search_id, query.clone()));
        // 过滤后回到顶部
        ui.ctx().data_mut(|d| d.insert_temp(scroll_id, 0.0));
    }
    if !query.is_empty() {
        let clear = egui::Rect::from_min_size(
            egui::pos2(field.max.x - 24.0, field.center().y - 9.0),
            egui::vec2(18.0, 18.0),
        );
        let cresp = ui.interact(clear, egui::Id::unique("ours-preset-search-clear"), egui::Sense::click());
        p.text(clear.center(), egui::Align2::CENTER_CENTER, "\u{00d7}", Tokens::ui(13.0), egui::Color32::from_rgb(200, 204, 212));
        if cresp.clicked() {
            query.clear();
            ui.ctx().data_mut(|d| d.insert_temp(search_id, String::new()));
            ui.ctx().data_mut(|d| d.insert_temp(scroll_id, 0.0));
        }
    }

    // 芯片：全部 / .ffx / .gp / .json（单选，记住上次选择）
    let chips: [(&str, u8); 4] = [("全部", 0), (".ffx", 1), (".gp", 2), (".json", 3)];
    let mut chip_x = r.min.x + 12.0;
    let chip_y = field.max.y + 6.0;
    for (label, value) in chips {
        let w = 14.0 + label.chars().count() as f32 * 7.0;
        let chip = egui::Rect::from_min_size(egui::pos2(chip_x, chip_y), egui::vec2(w, 26.0));
        let selected = filter == value;
        if selected {
            p.rect_filled(chip, 13.0, crate::panel_style::tint(t.accent, 41));
        } else {
            p.rect_stroke(chip, 13.0, egui::Stroke::new(1.0, crate::panel_style::border()), egui::StrokeKind::Inside);
        }
        p.text(chip.center(), egui::Align2::CENTER_CENTER, label, Tokens::ui(9.5), if selected { t.text } else { t.text_dim });
        let cresp = ui.interact(chip, egui::Id::unique(("ours-preset-chip", value)), egui::Sense::click());
        if cresp.clicked() && !selected {
            filter = value;
            ui.ctx().data_mut(|d| d.insert_temp(filter_id, value));
            ui.ctx().data_mut(|d| d.insert_temp(scroll_id, 0.0));
        }
        chip_x += w + 4.0;
    }

    // 过滤（大小写不敏感，先名字再后缀）
    let needle = query.trim().to_lowercase();
    let list: Vec<serde_json::Value> = list
        .into_iter()
        .filter(|item| {
            let name = item.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let kind = item.get("kind").and_then(|v| v.as_str()).unwrap_or("");
            let kind_ok = match filter {
                1 => matches!(kind, "local" | "rifx" | "xml"),
                2 => kind == "gp",
                3 => kind == "json",
                _ => true,
            };
            kind_ok && (needle.is_empty() || name.contains(&needle))
        })
        .collect();

    if list.is_empty() {
        let text = if needle.is_empty() && filter == 0 {
            "把 .ffx 放到\nDCIM/EffectCraft/Presets/"
        } else {
            "没有匹配的预设"
        };
        p.text(r.center(), egui::Align2::CENTER_CENTER, text, Tokens::ui(11.0), egui::Color32::from_rgb(160, 163, 172));
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
        egui::pos2(r.min.x + 8.0, chip_y + 32.0),
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
                        let read_list = |key: &str| -> Vec<String> {
                            v.get(key)
                                .and_then(|x| x.as_array())
                                .map(|a| a.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
                                .unwrap_or_default()
                        };
                        let n = v.get("applied").and_then(|x| x.as_u64()).unwrap_or(0);
                        let missing = read_list("missing");
                        let skipped = read_list("skipped");
                        let failed = read_list("failed");
                        let warnings = read_list("warnings");
                        // 界面只报三种：已导入 X / 跳过 Y（原因）/ 失败 Z（名单）
                        let mut parts: Vec<String> = vec![format!("已导入 {n}")];
                        if !missing.is_empty() {
                            let head: Vec<String> = missing.iter().take(5).cloned().collect();
                            parts.push(format!("缺 {} 个：{}", missing.len(), head.join("、")));
                        }
                        if !skipped.is_empty() {
                            parts.push(format!("跳过 {}", skipped.len()));
                        }
                        if !failed.is_empty() {
                            let head: Vec<String> = failed.iter().take(3).cloned().collect();
                            parts.push(format!("失败：{}", head.join("、")));
                        }
                        if let Some(first) = warnings.first() {
                            parts.push(first.clone());
                        }
                        notice = Some(parts.join("；"));
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

    // 滚动条：内容超出视口时画一条，thumb 位置跟随 scroll（拖它不影响下面的时间线，
    // 因为整块面板已经先注册了 click_and_drag）。
    let content_h = list.len() as f32 * (crate::panel_style::ROW_H + 6.0);
    if content_h > view.height() {
        let track = egui::Rect::from_min_max(
            egui::pos2(r.max.x - 7.0, view.min.y),
            egui::pos2(r.max.x - 3.0, view.max.y),
        );
        p.rect_filled(track, 2.0, t.switch_well);
        let view_h = view.height();
        let thumb_h = (view_h * (view_h / content_h)).max(18.0).min(view_h);
        let max_scroll = (content_h - view_h).max(1.0);
        let off = (scroll / max_scroll).clamp(0.0, 1.0);
        let thumb_y = view.min.y + (view_h - thumb_h) * off;
        p.rect_filled(
            egui::Rect::from_min_size(egui::pos2(track.min.x, thumb_y), egui::vec2(track.width(), thumb_h)),
            2.0,
            t.text_dim,
        );
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
