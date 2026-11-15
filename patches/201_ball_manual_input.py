#!/usr/bin/env python3
"""悬浮球改成手动处理指针（按/拖/松三个阶段用闩锁），彻底绕开 egui 多趟与命中问题。

The widget-based version could not be dragged and the panel flickered: `resp.dragged()`/`clicked()`
are evaluated once per pass, so state changed twice a frame. This reads the pointer itself:

* press inside the ball → remember it (`latched`) and the grab offset
* while the button is down and latched → the ball follows the pointer
* release → moved less than 8 px counts as a tap (toggles the panel), otherwise snap to an edge

The `latched` flag clears on the press edge, so a release is handled exactly once however many passes
a frame runs.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BALL_INPUT_V1"

START = "    let resp = ui.interact(r, egui::Id::unique(\"shortcut-ball-hit\"), egui::Sense::click_and_drag()).on_hover_text(\"快捷\");\n"
END = "    let alpha = if edge != 0 && !open { 44 } else { 255 };\n"

NEW = '''    // EFFECTCRAFT_OURS_BALL_INPUT_V1 — 手动处理按下/拖动/松开（每帧多趟也只算一次）
    let latch_id = egui::Id::unique("shortcut-ball-latch");
    let moved_id = egui::Id::unique("shortcut-ball-moved");
    let mut latched: bool = ctx.data(|d| d.get_temp::<bool>(latch_id)).unwrap_or(false);
    let mut moved: f32 = ctx.data(|d| d.get_temp::<f32>(moved_id)).unwrap_or(0.0);
    let (pressed, down, released, ppos) = ui.input(|i| {
        (i.pointer.primary_pressed(), i.pointer.primary_down(), i.pointer.primary_released(), i.pointer.interact_pos())
    });
    if pressed
        && let Some(p) = ppos
        && r.contains(p)
    {
        latched = true;
        moved = 0.0;
    }
    if latched && down {
        let d = ui.input(|i| i.pointer.delta());
        if d.length() > 0.0 {
            moved += d.length();
            pos += d;
            pos.x = pos.x.clamp(full.min.x + 4.0, full.max.x - size - 4.0);
            pos.y = pos.y.clamp(full.min.y + 4.0, full.max.y - size - 4.0);
            edge = 0;
        }
    }
    if released && latched {
        latched = false;
        if moved < 8.0 {
            open = !open;
            edge = 0;
        } else if pos.x - full.min.x < 24.0 {
            pos.x = full.min.x - size * 0.55;
            edge = 1;
        } else if full.max.x - (pos.x + size) < 24.0 {
            pos.x = full.max.x - size * 0.45;
            edge = 2;
        } else if full.max.y - (pos.y + size) < 48.0 {
            pos.y = full.max.y - size * 0.5;
            edge = 3;
        }
    }
    ctx.data_mut(|d| {
        d.insert_temp(latch_id, latched);
        d.insert_temp(moved_id, moved);
    });
    let alpha = if edge != 0 && !open { 44 } else { 255 };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("manual input already installed")
        return
    start = src.find(START)
    end = src.find(END, start)
    if start == -1 or end == -1:
        raise SystemExit(f"block not found ({start}, {end})")
    src = src[:start] + NEW + src[end + len(END):]
    path.write_text(src, encoding="utf-8")
    print("ball handles the pointer itself")


if __name__ == "__main__":
    main()
