#!/usr/bin/env python3
"""The A/V switches (eye, speaker, solo, lock) answer a plain click, the way After Effects' do.

They went through `layer_switch`, whose only trigger is the *press* (`switch_gesture`) and whose
fallback explicitly ignored the primary button — so when the press did not reach the switch the tap
did nothing at all. This gives them their own short handler: a tap toggles, Alt+tap sets the layer
apart (the other layers off, as in After Effects). No drag state, no shared gesture, nothing but a
click — the earlier attempt that touched the shared path crashed and was rolled back.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AV_CLICK_V1"

OLD = '''        lp.rect_filled(br.shrink(0.5), 1.0, t.switch_well);
        layer_switch(
            ui,
            &t,
            &SwitchSpec { row: r, br, icon, on, id: egui::Id::unique(("av", layer.id.0, i)), layer: layer.id.0, name, others: true },
            &comp,
            &app.session.project,
            selected,
            &mut *actions,
        );
'''

NEW = '''        lp.rect_filled(br.shrink(0.5), 1.0, t.switch_well);
        // EFFECTCRAFT_OURS_AV_CLICK_V1 — 手机上没有 Alt：点一下切换，长按=只留这一层（AE 的 Alt+点）
        let hold_id = egui::Id::new(("av-hold", layer.id.0, i));
        let resp = widgets::icon_toggle(ui, br, icon, on, &t, egui::Id::unique(("av", layer.id.0, i)), Sense::click());
        let tip = match name {
            "video" => "点：显示 / 隐藏    长按：只留这一层",
            "audio" => "点：音频开 / 关    长按：只留这一层",
            "solo" => "点：独奏    长按：只留这一层",
            _ => "点：锁定 / 解锁    长按：只留这一层",
        };
        let resp = resp.on_hover_text(tip);
        if resp.is_pointer_button_down_on() && ui.input(|i| i.pointer.primary_pressed()) {
            ui.data_mut(|d| d.insert_temp(hold_id, ui.input(|i| i.time)));
        }
        if resp.clicked() {
            let held = ui.data(|d| d.get_temp::<f64>(hold_id));
            ui.data_mut(|d| d.remove::<f64>(hold_id));
            // 长按 0.45 秒算“只留这一层”；桌面端 Alt+点仍是同一个意思。
            let apart = ui.input(|i| i.modifiers.alt) || held.is_some_and(|at| ui.input(|i| i.time) - at > 0.45);
            if apart {
                let layers = edited_layers(LayerId(layer.id.0), selected);
                actions.push(("layer.setSwitch".into(), json!({"layers": layers, "switch": name, "others": true})));
            } else {
                let layers = switch_targets(&comp, &app.session.project, selected, layer.id.0, name);
                actions.push(("layer.setSwitch".into(), json!({"layers": layers, "switch": name, "value": !on})));
            }
        }
        app.auto.add(&format!("timeline.layer.{}.av.{name}", layer.id.0), br, name);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("A/V switches already clickable")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("A/V switches answer a click (Alt = set apart)")


if __name__ == "__main__":
    main()
