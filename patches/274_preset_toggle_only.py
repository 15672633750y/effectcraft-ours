#!/usr/bin/env python3
"""预设窗口只由按钮开关（去掉“点外面就关”，它偶尔会把窗口自己关掉）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_TOGGLE_ONLY_V1"

OLD = '    // 点击窗口外关闭：忽略打开那一下（以及 0.25 秒内的点击），否则窗口会被自己的开合点击关掉\n    let now = ui.input(|i| i.time);\n    let seen_id = egui::Id::unique("ours-preset-seen-at");\n    let seen: Option<f64> = ui.ctx().data(|d| d.get_temp::<f64>(seen_id));\n    let fresh = seen.is_none();\n    if fresh {\n        ui.ctx().data_mut(|d| d.insert_temp(seen_id, now));\n    }\n    let settled = !fresh && now - seen.unwrap_or(now) > 0.25;\n    let outside = settled\n        && ui.input(|i| i.pointer.primary_clicked() && i.pointer.interact_pos().map_or(false, |q| !r.contains(q)));\n    if outside {\n        ui.ctx().data_mut(|d| {\n            d.insert_temp(open_id, false);\n            d.remove_temp::<f64>(seen_id);\n        });\n    }\n'

NEW = '    // 只由「预设」按钮开关；不再因为点到外面就关（之前偶尔会自己关）\n    let _ = r;\n'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset window is toggle-only")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset window toggled only by its button")


if __name__ == "__main__":
    main()
