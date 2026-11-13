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
        // A custom accent recolours the focus rings, highlights and the accent colour together.
        if let Some(rgb) = parse_hex(&p.appearance.accent) {
            t.accent = rgb;
            t.focus = rgb;
            t.accent_hover = rgb.lerp_to_gamma(Color32::WHITE, 0.22);
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
        ui.add_sized(vec2(250.0, 18.0), egui::Label::new("主题色:").truncate());
        for hex in ["1", "e5484d", "f5a524", "30a46c", "2d8ceb", "8e4ec6", "e93d82", "00b8d9"] {
            let colour = if hex == "1" { t.accent } else { crate::theme::swatch(hex) };
            let (rect, resp) = ui.allocate_exact_size(vec2(22.0, 18.0), egui::Sense::click());
            ui.painter().rect_filled(rect, 3.0, colour);
            if resp.clicked() {
                let value = if hex == "1" { String::new() } else { format!("#{hex}") };
                acts.push(Act::Set("appearance.accent".into(), json!(value)));
            }
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
        if tsrc.count(THEME_ANCHOR) != 1 or tsrc.count(PARSE_ANCHOR) != 1:
            raise SystemExit("theme anchors missing")
        tsrc = tsrc.replace(THEME_ANCHOR, THEME, 1)
        tsrc = tsrc.replace(PARSE_ANCHOR, PARSE_FN + PARSE_ANCHOR, 1)
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
