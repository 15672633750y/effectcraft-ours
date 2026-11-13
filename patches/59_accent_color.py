#!/usr/bin/env python3
"""Theme accent colour: a row of swatches in Appearance Settings, kept in the preferences."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCENT_V1"
FIELD_ANCHOR = "    brightness: f64 = 0.0,\n"
FIELD = '    /// Custom interface accent colour as "#rrggbb"; empty keeps the theme\'s own.\n    accent: String = String::new(),\n'

THEME_ANCHOR = "        let mut t = Tokens::for_kind(kind).with_brightness(p.appearance.brightness as f32);\n"
THEME = THEME_ANCHOR + '''        // " + MARKER + "
        // A custom accent recolours the focus rings, highlights and the accent colour together —
        // and everything else that carries the accent: the playhead and the timecode, the value
        // text of properties, a selected keyframe, selected rows, the selected layer's graph and
        // an active effect header. Without these the theme only moved buttons and sliders.
        if let Some(rgb) = parse_hex(&p.appearance.accent) {
            t.accent = rgb;
            t.focus = rgb;
            t.accent_hover = rgb.lerp_to_gamma(Color32::WHITE, 0.22);
            t.cti = rgb;
            t.timecode = rgb;
            t.hot_text = rgb;
            t.keyframe_selected = rgb;
            t.row_selected = t.row.lerp_to_gamma(rgb, 0.38);
            t.tl_graph_selected = t.tl_bg.lerp_to_gamma(rgb, 0.30);
            t.fx_header_active = t.fx_header.lerp_to_gamma(rgb, 0.42);
        }
'''

PARSE_ANCHOR = "    pub fn from_prefs(p: &effectcraft_engine::prefs::Prefs, kind: ThemeKind) -> Tokens {\n"
PARSE_FN = '''/// The colour of a swatch in the appearance settings.
pub fn swatch(hex: &str) -> Color32 {
    parse_hex(hex).unwrap_or(Color32::from_rgb(0x2d, 0x8c, 0xeb))
}

/// "#rrggbb" (or "#rgb") to a colour; anything else is ignored.
fn parse_hex(text: &str) -> Option<Color32> {
    let hex = text.trim().trim_start_matches('#');
    let byte = |s: &str| u8::from_str_radix(s, 16).ok();
    match hex.len() {
        6 => Some(Color32::from_rgb(
            byte(&hex[0..2])?,
            byte(&hex[2..4])?,
            byte(&hex[4..6])?,
        )),
        3 => Some(Color32::from_rgb(
            byte(&hex[0..1])? * 17,
            byte(&hex[1..2])? * 17,
            byte(&hex[2..3])? * 17,
        )),
        _ => None,
    }
}

'''

UI_ANCHOR = "    ui.add_space(6.0);\n    let system_light = app.system_light(ui.ctx());\n"
UI = '''    // " + MARKER + "
    ui.horizontal(|ui| {
        ui.add_sized(vec2(250.0, 18.0), egui::Label::new("主题色：").truncate());
        let (rect, resp) = ui.allocate_exact_size(vec2(22.0, 18.0), egui::Sense::click());
        ui.painter().rect_filled(rect, 3.0, t.accent);
        ui.painter().rect_stroke(rect, 3.0, egui::Stroke::new(1.0, t.text), egui::StrokeKind::Inside);
        if resp.on_hover_text("跟随主题（默认）").clicked() {
            acts.push(Act::Set("appearance.accent".into(), json!("")));
        }
    });
    // The whole pool: eight hues, five shades each, so any brightness of any family is one tap.
    for row in [
        ["ee9696", "eebf96", "eed896", "96eeb3", "96eeee", "96baee", "c296ee", "ee96c2"],
        ["e66565", "e6a165", "e6c665", "65e690", "65e6e6", "659be6", "a665e6", "e665a6"],
        ["df3a3a", "df873a", "dfb63a", "3adf71", "3adfdf", "3a7edf", "8c3adf", "df3a8c"],
        ["c52020", "c56d20", "c59c20", "20c557", "20c5c5", "2065c5", "7320c5", "c52073"],
        ["951818", "955318", "957618", "189542", "189595", "184c95", "571895", "951857"],
    ] {
        ui.horizontal(|ui| {
            for hex in row {
                let (rect, resp) = ui.allocate_exact_size(vec2(22.0, 18.0), egui::Sense::click());
                ui.painter().rect_filled(rect, 3.0, crate::theme::swatch(hex));
                if resp.clicked() {
                    acts.push(Act::Set("appearance.accent".into(), json!(format!("#{hex}"))));
                }
            }
        });
    }
    // 16 进制输入 + 取色器：色板只是快捷方式，这一行能选任意颜色。
    let hex_buf_id = egui::Id::new("ours-accent-hex");
    let mut hex_buf = ui.data(|d| d.get_temp::<String>(hex_buf_id)).unwrap_or_else(|| {
        let a = &app.session.prefs.appearance.accent;
        if a.is_empty() {
            String::new()
        } else {
            a.clone()
        }
    });
    ui.horizontal(|ui| {
        ui.add_sized(vec2(250.0, 18.0), egui::Label::new("十六进制：").truncate());
        let edit = ui.add(egui::TextEdit::singleline(&mut hex_buf).hint_text("#2d8ceb").desired_width(96.0));
        if edit.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
            let v = hex_buf.trim().trim_start_matches('#').to_string();
            let valid = (v.len() == 6 || v.len() == 3) && v.chars().all(|c| c.is_ascii_hexdigit());
            if valid {
                acts.push(Act::Set("appearance.accent".into(), json!(format!("#{v}"))));
            } else if v.is_empty() {
                acts.push(Act::Set("appearance.accent".into(), json!("")));
            }
        }
        ui.data_mut(|d| d.insert_temp(hex_buf_id, hex_buf));
        // 取色器：和合成里的颜色一样，一个完整的拾色弹窗。
        let picker_id = egui::Id::new("ours-accent-picker");
        let hex_now = if app.session.prefs.appearance.accent.is_empty() {
            "#2d8ceb".to_string()
        } else {
            app.session.prefs.appearance.accent.clone()
        };
        let current = crate::theme::swatch(&hex_now);
        let [r, g, b, _] = current.to_srgba_unmultiplied();
        let mut rgb = [f32::from(r) / 255.0, f32::from(g) / 255.0, f32::from(b) / 255.0];
        if ui.button("取色器…").clicked() {
            crate::widgets::open_popup(ui, picker_id);
        }
        let anchor = ui.min_rect().left_bottom();
        if crate::widgets::color_popup(ui, picker_id, anchor, &mut rgb) {
            let to = |v: f32| (v.clamp(0.0, 1.0) * 255.0).round() as u8;
            acts.push(Act::Set("appearance.accent".into(), json!(format!("#{:02x}{:02x}{:02x}", to(rgb[0]), to(rgb[1]), to(rgb[2])))));
        }
    });
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    sections = root / "crates/engine/src/settings/prefs/sections.rs"
    src = sections.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FIELD_ANCHOR) != 1:
            raise SystemExit("brightness field anchor missing")
        src = src.replace(FIELD_ANCHOR, FIELD_ANCHOR + FIELD, 1)
        sections.write_text(src, encoding="utf-8")

    theme = root / "crates/ui-egui/src/theme.rs"
    tsrc = theme.read_text(encoding="utf-8")
    if MARKER not in tsrc:
        if tsrc.count(THEME_ANCHOR) != 1:
            raise SystemExit("theme anchors missing")
        tsrc = tsrc.replace(THEME_ANCHOR, THEME, 1)
        # Module-scope helpers at the end of the file, not inside an impl block.
        tsrc = tsrc + "\n" + PARSE_FN
        theme.write_text(tsrc, encoding="utf-8")

    settings = root / "crates/ui-egui/src/panels/settings.rs"
    ssrc = settings.read_text(encoding="utf-8")
    if MARKER not in ssrc:
        if ssrc.count(UI_ANCHOR) != 1:
            raise SystemExit("appearance ui anchor missing")
        ssrc = ssrc.replace(UI_ANCHOR, UI + UI_ANCHOR, 1)
        settings.write_text(ssrc, encoding="utf-8")
    print("accent colour: preference, theme override and swatches installed")


if __name__ == "__main__":
    main()
