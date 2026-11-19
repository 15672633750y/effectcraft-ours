#!/usr/bin/env python3
"""变速改成 AE 式「时间伸缩」输入：0.01×–100×，默认 1×。

点底部「变速」打开一个小面板：速度可拖动（对数刻度）或直接 +/-，预设 0.5/1/2/10/100。
应用时换算成 `layer.timeStretch { percent: 100 / speed }`（速度 2 → 时长 50%）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SPEED_PANEL_V1"

MATCH_OLD = '''                Some(16) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.enableTimeRemap",
                        serde_json::json!({ "value": true }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已为选中图层打开时间重映射（可做变速）".into()
                    } else {
                        "先选中一个图层".into()
                    };
                }'''

MATCH_NEW = '''                Some(16) => {
                    // EFFECTCRAFT_OURS_SPEED_PANEL_V1 — AE 式时间伸缩：0.01×–100×，默认 1×
                    ui.ctx()
                        .data_mut(|d| d.insert_temp(egui::Id::new("ours-speed-open"), true));
                }'''

PANEL_CALL_OLD = '''            crate::header::export_window(self, ui.ctx());
            crate::header::plugin_window(self, ui.ctx());'''

PANEL_CALL_NEW = '''            crate::header::export_window(self, ui.ctx());
            crate::header::plugin_window(self, ui.ctx());
            ours_speed_panel(self, ui);'''

PANEL_FN = '''
/// EFFECTCRAFT_OURS_SPEED_PANEL_V1 — 时间伸缩面板（AE 的"时间伸缩"百分比 = 100 / 速度）。
fn ours_speed_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui) {
    let open_id = egui::Id::new("ours-speed-open");
    let mut open = ui.ctx().data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    let speed_id = egui::Id::new("ours-speed-value");
    let mut speed = ui
        .ctx()
        .data(|d| d.get_temp::<f32>(speed_id).unwrap_or(1.0))
        .clamp(0.01, 100.0);
    let mut apply = false;
    let t = app.tokens;
    egui::Window::new("时间伸缩")
        .id(egui::Id::new("ours-speed-window"))
        .open(&mut open)
        .collapsible(false)
        .resizable(false)
        .default_width(300.0)
        .show(ui.ctx(), |ui| {
            ui.label(egui::RichText::new("速度（1 = 原速，0.01–100）").weak());
            ui.add(
                egui::Slider::new(&mut speed, 0.01..=100.0)
                    .logarithmic(true)
                    .fixed_decimals(2),
            );
            ui.horizontal(|ui| {
                for p in [0.1f32, 0.5, 1.0, 2.0, 10.0, 100.0] {
                    if ui.button(format!("{p}×")).clicked() {
                        speed = p;
                    }
                }
            });
            ui.label(
                egui::RichText::new(format!(
                    "时间伸缩 = {:.2}%（时长 ×{:.3}）",
                    100.0 / speed,
                    1.0 / speed
                ))
                .color(t.text_dim),
            );
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                if ui.button("应用到选中图层").clicked() {
                    apply = true;
                }
            });
        });
    ui.ctx().data_mut(|d| d.insert_temp(speed_id, speed));
    if !open {
        ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
    }
    if apply {
        let percent = 100.0 / speed;
        let r = crate::menus::invoke(
            app,
            ui.ctx(),
            "layer.timeStretch",
            serde_json::json!({ "percent": percent }),
        );
        app.ui.status = if r.is_ok() {
            format!("时间伸缩 {percent:.1}%（速度 {speed}×）已应用")
        } else {
            "先选中一个图层".into()
        };
        ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
    }
}
'''

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("speed panel already present")
        return
    for name, old, new in (("match", MATCH_OLD, MATCH_NEW), ("call", PANEL_CALL_OLD, PANEL_CALL_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    src = src.rstrip("\n") + "\n" + PANEL_FN
    path.write_text(src, encoding="utf-8")
    print("time stretch panel with 0.01x-100x added")


if __name__ == "__main__":
    main()
