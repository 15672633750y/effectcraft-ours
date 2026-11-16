#!/usr/bin/env python3
"""修预设库「点开就关」：打开的那一下点击被当成「点外面」，于是立刻关闭。

The outside-click check saw the very press that opened the window (it is outside the panel rect), so the
window closed in the same frame. It now ignores presses during the first 0.25 s after opening, and the
`预设` button toggles it closed itself.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_CLOSE_FIX_V1"

OLD = """    // 点击窗口外关闭
    let outside = ui.input(|i| i.pointer.primary_clicked() && i.pointer.interact_pos().map_or(false, |q| !r.contains(q)));
    if outside {
        ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
    }
"""

NEW = """    // 点击窗口外关闭：忽略打开那一下（以及 0.25 秒内的点击），否则窗口会被自己的开合点击关掉
    let now = ui.input(|i| i.time);
    let seen_id = egui::Id::unique("ours-preset-seen-at");
    let seen: Option<f64> = ui.ctx().data(|d| d.get_temp::<f64>(seen_id));
    let fresh = seen.is_none();
    if fresh {
        ui.ctx().data_mut(|d| d.insert_temp(seen_id, now));
    }
    let settled = !fresh && now - seen.unwrap_or(now) > 0.25;
    let outside = settled
        && ui.input(|i| i.pointer.primary_clicked() && i.pointer.interact_pos().map_or(false, |q| !r.contains(q)));
    if outside {
        ui.ctx().data_mut(|d| {
            d.insert_temp(open_id, false);
            d.remove_temp::<f64>(seen_id);
        });
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset panel close already fixed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset panel no longer closes on its own opening click")


if __name__ == "__main__":
    main()
