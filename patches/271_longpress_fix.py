#!/usr/bin/env python3
"""长按多选在手机上根本不触发：手动计时那套不可靠，改用 egui 的 long_touched。

The hand-rolled 450 ms timer never fired for touch input, so a long press behaved like a normal click
(select exactly one layer, drop the previous one). `Response::long_touched()` is the platform one.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LONGPRESS_FIX_V1"

OLD = '    // EFFECTCRAFT_OURS_LONGPRESS_MULTI_V1 — 长按 450ms（几乎不移动）= 加选/取消\n    let lp_start = egui::Id::new(("ours-lp-start", layer.id.0));\n    let lp_fired = egui::Id::new(("ours-lp-fired", layer.id.0));\n    let lp_pos = egui::Id::new(("ours-lp-pos", layer.id.0));\n    let now = ui.input(|i| i.time);\n    let pointer = ui.input(|i| i.pointer.interact_pos());\n    if row_resp.is_pointer_button_down_on() {\n        let start: Option<f64> = ctx.data(|d| d.get_temp::<f64>(lp_start));\n        let start = match start {\n            Some(s) => s,\n            None => {\n                ctx.data_mut(|d| {\n                    d.insert_temp(lp_start, now);\n                    d.insert_temp(lp_fired, false);\n                });\n                now\n            }\n        };\n        let fired: bool = ctx.data(|d| d.get_temp::<bool>(lp_fired)).unwrap_or(false);\n        // 只有手指基本没动才算长按（拖动排序不该触发多选）\n        let press_at: Option<egui::Pos2> = ctx.data(|d| d.get_temp::<egui::Pos2>(lp_pos));\n        let held_still = match (press_at, pointer) {\n            (Some(a), Some(b)) => (b - a).length() < 8.0,\n            (None, Some(b)) => {\n                ctx.data_mut(|d| d.insert_temp(lp_pos, b));\n                true\n            }\n            _ => false,\n        };\n        if !fired && held_still && now - start > 0.45 {\n            ctx.data_mut(|d| d.insert_temp(lp_fired, true));\n            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": true})));\n        }\n    }\n    let lp_was_fired: bool = ctx.data(|d| d.get_temp::<bool>(lp_fired)).unwrap_or(false);\n    if !row_resp.is_pointer_button_down_on() && !row_resp.clicked() {\n        ctx.data_mut(|d| d.insert_temp(lp_start, now));\n    }\n'

NEW = '    // EFFECTCRAFT_OURS_LONGPRESS_MULTI_V1 — 长按 = 加选/取消（用 egui 自带的 long_touched，触摸才可靠）\n    if row_resp.long_touched() && !locked {\n        actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": true})));\n        ctx.data_mut(|d| d.insert_temp(egui::Id::new(("ours-lp-fired", layer.id.0)), true));\n    }\n    let lp_was_fired: bool = ctx.data(|d| d.get_temp::<bool>(egui::Id::new(("ours-lp-fired", layer.id.0)))).unwrap_or(false);\n'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("long press already uses long_touched")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("long press now fires on touch")


if __name__ == "__main__":
    main()
