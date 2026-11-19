#!/usr/bin/env python3
"""每套布局还有自己的**主色**，不只是亮/暗差别：

* CapCut  蓝  #3D9BFF
* 快影     红橙 #FF5A5A
* AM      青绿 #00D6B4
* Blurrr / AE 用用户自己的主题色

主色同时改写 accent / focus / cti / timecode / hot_text，这样播放头、时间码、选中行都跟着变。
布局变化时重建 tokens，离开布局自动回到用户设置。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_BRAND_ACCENT_V1"

OLD = '''        // EFFECTCRAFT_OURS_LAYOUT_AM_V1 — 布局自带的主题色系：参考 app 里 capcut/快影/AM 都是亮色界面
        {
            let light_layout = matches!(self.ui.workspace.as_str(), "capcut" | "kuaishou" | "am");
            let want = if light_layout {
                crate::theme::ThemeKind::Light
            } else {
                self.ui.theme
            };
            if self.tokens.kind != want {
                self.tokens = Tokens::from_prefs(&self.session.prefs, want);
                crate::theme::apply_visuals(&ctx, &self.tokens);
                ctx.set_theme(crate::theme::theme_preference(
                    &self.session.prefs.appearance.appearance_mode,
                    want.is_light(),
                ));
            }
        }'''

NEW = '''        // EFFECTCRAFT_OURS_LAYOUT_BRAND_ACCENT_V1 — 布局自带主题色系 + 品牌主色。
        // 不需要新增状态：用 tokens 当前值判断是否已经应用到目标。
        {
            let ws = self.ui.workspace.as_str().to_string();
            let light_layout = matches!(ws.as_str(), "capcut" | "kuaishou" | "am");
            let brand: Option<egui::Color32> = match ws.as_str() {
                "capcut" => Some(egui::Color32::from_rgb(0x3d, 0x9b, 0xff)),
                "kuaishou" => Some(egui::Color32::from_rgb(0xff, 0x5a, 0x5a)),
                "am" => Some(egui::Color32::from_rgb(0x00, 0xd6, 0xb4)),
                _ => None,
            };
            let want = if light_layout {
                crate::theme::ThemeKind::Light
            } else {
                self.ui.theme
            };
            let brand_colors = [
                egui::Color32::from_rgb(0x3d, 0x9b, 0xff),
                egui::Color32::from_rgb(0xff, 0x5a, 0x5a),
                egui::Color32::from_rgb(0x00, 0xd6, 0xb4),
            ];
            let branded = brand_colors.contains(&self.tokens.accent);
            let needs = match brand {
                Some(c) => self.tokens.kind != want || self.tokens.accent != c,
                None => self.tokens.kind != want || branded,
            };
            if needs {
                let mut t = Tokens::from_prefs(&self.session.prefs, want);
                if let Some(c) = brand {
                    t.accent = c;
                    t.focus = c;
                    t.accent_hover = c.lerp_to_gamma(egui::Color32::WHITE, 0.22);
                    t.cti = c;
                    t.timecode = c;
                    t.hot_text = c;
                    t.keyframe_selected = c;
                }
                self.tokens = t;
                crate::theme::apply_visuals(&ctx, &self.tokens);
                ctx.set_theme(crate::theme::theme_preference(
                    &self.session.prefs.appearance.appearance_mode,
                    want.is_light(),
                ));
            }
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("brand accents already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("per-layout brand accent colours")


if __name__ == "__main__":
    main()
