#!/usr/bin/env python3
"""保存预设：弹窗命名（不自动命名），三态：命名 -> 覆盖确认 -> 已保存。

- `invoke("anim.savePreset")` 不再写文件，只打开玻璃弹窗（材质/层级同账号提示弹窗）。
- 空名 -> 保存置灰；含非法字符 -> 提示。
- 目标已存在 -> 覆盖确认；写完 -> 「已保存」+ 路径可复制。
- 成功后置 `ours-presets-dirty`，预设库面板下次绘制自动重拉。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_SAVE_DIALOG_V1"

INVOKE_ANCHOR = '''    crate::control::check_script_render(app, id)?;
'''

NEW_SAVE = '''    // EFFECTCRAFT_OURS_PRESET_SAVE_DIALOG_V1 - save preset opens a naming dialog (no SAF).
    if id == "anim.savePreset" {
        let default = app
            .session
            .active_comp()
            .and_then(|c| {
                app.session
                    .state
                    .selected_layers
                    .first()
                    .and_then(|lid| c.layer(*lid))
            })
            .map(|l| l.name.clone())
            .unwrap_or_else(|| "Preset".to_string());
        ctx.data_mut(|d| {
            d.insert_temp(egui::Id::unique("ours-preset-save-name"), default);
            d.insert_temp(egui::Id::unique("ours-preset-save-mode"), 0_u8);
            d.insert_temp(egui::Id::unique("ours-preset-save-error"), String::new());
            d.insert_temp(egui::Id::unique("ours-preset-save-open"), true);
        });
        return Ok(json!({ "dialog": "ours.presetSave" }));
    }
'''

DIALOG = r'''

/// EFFECTCRAFT_OURS_PRESET_SAVE_DIALOG_V1 - glass dialog: name / overwrite / saved.
/// Drawn after every panel, so it is always on top; backdrop click or Esc cancels.
fn preset_save_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: egui::Rect) {
    let open_id = egui::Id::unique("ours-preset-save-open");
    if !ui.ctx().data(|d| d.get_temp::<bool>(open_id).unwrap_or(false)) {
        return;
    }
    let t = app.tokens;
    let mode_id = egui::Id::unique("ours-preset-save-mode");
    let name_id = egui::Id::unique("ours-preset-save-name");
    let path_id = egui::Id::unique("ours-preset-save-path");
    let err_id = egui::Id::unique("ours-preset-save-error");
    let mode: u8 = ui.ctx().data(|d| d.get_temp::<u8>(mode_id).unwrap_or(0));
    let mut name: String = ui.ctx().data(|d| d.get_temp::<String>(name_id).unwrap_or_default());
    let mut error: String = ui.ctx().data(|d| d.get_temp::<String>(err_id).unwrap_or_default());

    ui.painter().rect_filled(full, 0.0, egui::Color32::from_black_alpha(89));
    let backdrop = ui.interact(full, egui::Id::unique("ours-preset-save-backdrop"), egui::Sense::click());
    if backdrop.clicked() || ui.input(|i| i.key_pressed(egui::Key::Escape)) {
        ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
        return;
    }

    let width = 340.0_f32.min(full.width() - 32.0);
    let height = if mode == 0 { 196.0 } else { 180.0 };
    let card = egui::Rect::from_center_size(full.center(), egui::vec2(width, height));
    ui.painter().rect_filled(card, crate::panel_style::RADIUS, crate::panel_style::bg());
    ui.painter().rect_stroke(
        card,
        crate::panel_style::RADIUS,
        egui::Stroke::new(1.0, crate::panel_style::border()),
        egui::StrokeKind::Inside,
    );
    let title = match mode {
        1 => "\u{8986}\u{76d6}\u{9884}\u{8bbe}",
        2 => "\u{5df2}\u{4fdd}\u{5b58}",
        _ => "\u{4fdd}\u{5b58}\u{9884}\u{8bbe}",
    };
    ui.painter().text(
        egui::pos2(card.min.x + 18.0, card.min.y + 28.0),
        egui::Align2::LEFT_CENTER,
        title,
        Tokens::semibold(crate::panel_style::TITLE_SIZE),
        t.text,
    );
    let left = card.min.x + 18.0;
    let inner_w = width - 36.0;

    match mode {
        0 => {
            let field = egui::Rect::from_min_size(egui::pos2(left, card.min.y + 50.0), egui::vec2(inner_w, 34.0));
            ui.painter().rect_filled(field, 8.0, t.field_bg);
            let edit = egui::TextEdit::singleline(&mut name)
                .hint_text("\u{9884}\u{8bbe}\u{540d}\u{5b57}")
                .text_color(t.text)
                .font(Tokens::ui(13.0))
                .margin(egui::Margin::symmetric(8, 7));
            if ui.put(field, edit).changed() {
                ui.ctx().data_mut(|d| d.insert_temp(name_id, name.clone()));
                ui.ctx().data_mut(|d| d.insert_temp(err_id, String::new()));
                error.clear();
            }
            let mut bad_char = false;
            for c in name.trim().chars() {
                if matches!(c, '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|') {
                    bad_char = true;
                }
            }
            let empty = name.trim().is_empty();
            if bad_char {
                error = "\u{540d}\u{5b57}\u{91cc}\u{4e0d}\u{80fd}\u{6709} / \\ : * ? \" < > |".to_string();
            }
            if !error.is_empty() {
                ui.painter().text(
                    egui::pos2(left, card.min.y + 100.0),
                    egui::Align2::LEFT_CENTER,
                    &error,
                    Tokens::ui(11.0),
                    t.warning,
                );
            }
            let btn_y = card.min.y + 128.0;
            let half = (inner_w - 8.0) / 2.0;
            if crate::account_ui::button_pub(
                ui,
                &t,
                egui::Rect::from_min_size(egui::pos2(left, btn_y), egui::vec2(half, crate::panel_style::BUTTON_H)),
                "\u{53d6}\u{6d88}",
                false,
            ) {
                ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
            }
            let valid = !empty && !bad_char;
            if crate::account_ui::button_pub(
                ui,
                &t,
                egui::Rect::from_min_size(egui::pos2(left + half + 8.0, btn_y), egui::vec2(half, crate::panel_style::BUTTON_H)),
                "\u{4fdd}\u{5b58}",
                true,
            ) && valid
            {
                let dir = std::path::PathBuf::from("/storage/emulated/0/DCIM/EffectCraft/Presets");
                let _ = std::fs::create_dir_all(&dir);
                let target = dir.join(format!("{}.ffx", name.trim()));
                let path = target.to_string_lossy().to_string();
                if target.exists() {
                    ui.ctx().data_mut(|d| {
                        d.insert_temp(path_id, path);
                        d.insert_temp(mode_id, 1_u8);
                    });
                } else {
                    match app.session.execute("ours.exportPreset", serde_json::json!({ "path": path })) {
                        Ok(_) => {
                            ui.ctx().data_mut(|d| {
                                d.insert_temp(path_id, path);
                                d.insert_temp(mode_id, 2_u8);
                                d.insert_temp(egui::Id::new("ours-presets-dirty"), true);
                            });
                        }
                        Err(e) => error = format!("save failed: {e}"),
                    }
                }
            }
        }
        1 => {
            let path: String = ui.ctx().data(|d| d.get_temp::<String>(path_id).unwrap_or_default());
            ui.painter().text(
                egui::pos2(left, card.min.y + 64.0),
                egui::Align2::LEFT_CENTER,
                "\u{540c}\u{540d}\u{9884}\u{8bbe}\u{5df2}\u{5b58}\u{5728}\u{ff0c}\u{662f}\u{5426}\u{8986}\u{76d6}\u{ff1f}",
                Tokens::ui(12.5),
                t.text_dim,
            );
            let btn_y = card.min.y + 112.0;
            let half = (inner_w - 8.0) / 2.0;
            if crate::account_ui::button_pub(
                ui,
                &t,
                egui::Rect::from_min_size(egui::pos2(left, btn_y), egui::vec2(half, crate::panel_style::BUTTON_H)),
                "\u{53d6}\u{6d88}",
                false,
            ) {
                ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
            }
            if crate::account_ui::button_pub(
                ui,
                &t,
                egui::Rect::from_min_size(egui::pos2(left + half + 8.0, btn_y), egui::vec2(half, crate::panel_style::BUTTON_H)),
                "\u{8986}\u{76d6}",
                true,
            ) {
                match app.session.execute("ours.exportPreset", serde_json::json!({ "path": path })) {
                    Ok(_) => {
                        ui.ctx().data_mut(|d| {
                            d.insert_temp(mode_id, 2_u8);
                            d.insert_temp(egui::Id::new("ours-presets-dirty"), true);
                        });
                    }
                    Err(e) => error = format!("save failed: {e}"),
                }
            }
        }
        _ => {
            let path: String = ui.ctx().data(|d| d.get_temp::<String>(path_id).unwrap_or_default());
            let file = std::path::Path::new(&path)
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_default();
            ui.painter().text(egui::pos2(left, card.min.y + 56.0), egui::Align2::LEFT_CENTER, file, Tokens::ui(13.0), t.text);
            ui.painter().text(egui::pos2(left, card.min.y + 78.0), egui::Align2::LEFT_CENTER, path, Tokens::ui(10.5), t.text_faint);
            let copy_rect = egui::Rect::from_min_size(egui::pos2(left, card.min.y + 68.0), egui::vec2(inner_w, 22.0));
            let copy = ui.interact(copy_rect, egui::Id::unique("ours-preset-save-copy"), egui::Sense::click());
            if copy.hovered() {
                ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
            }
            if copy.clicked() {
                ui.ctx().copy_text(path.clone());
                app.ui.status = "path copied".to_string();
            }
            let btn = egui::Rect::from_min_size(egui::pos2(left, card.min.y + 116.0), egui::vec2(inner_w, crate::panel_style::BUTTON_H));
            if crate::account_ui::button_pub(ui, &t, btn, "\u{77e5}\u{9053}\u{4e86}", true) {
                ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
            }
        }
    }
    if !error.is_empty() {
        ui.ctx().data_mut(|d| d.insert_temp(err_id, error.clone()));
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    inv = root / "crates/ui-egui/src/menus/invoke.rs"
    src = inv.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(INVOKE_ANCHOR) != 1:
            raise SystemExit(f"invoke anchor: {src.count(INVOKE_ANCHOR)}")
        src = src.replace(INVOKE_ANCHOR, INVOKE_ANCHOR + NEW_SAVE, 1)
        inv.write_text(src, encoding="utf-8")
        print("anim.savePreset opens the naming dialog")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if "fn preset_save_panel" not in src:
        anchor = "        preset_panel(self, ui, full);\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"frame anchor: {src.count(anchor)}")
        src = src.replace(anchor, anchor + "        preset_save_panel(self, ui, full);\n", 1)
        src += DIALOG
        frame.write_text(src, encoding="utf-8")
        print("preset save dialog drawn last")


if __name__ == "__main__":
    main()
