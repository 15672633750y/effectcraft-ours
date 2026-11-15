#!/usr/bin/env python3
"""悬浮球点一下只切换一次（egui 每帧会跑多趟，点击被处理了两次 → 面板刚开就关）。

The frame runs more than one pass, so `resp.clicked()` was seen twice and the panel opened and closed
in the same tap. The toggle is now keyed on the input time, so only the first pass acts.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BALL_CLICK_ONCE_V1"

OLD = '''    if resp.clicked() {
        open = !open;
        edge = 0;
    }
    let alpha = if edge != 0 && !open { 44 } else { 255 };
'''
NEW = '''    // EFFECTCRAFT_OURS_BALL_CLICK_ONCE_V1 — 同一时刻只处理一次点击（egui 每帧多趟）
    let now = ui.input(|i| i.time);
    let click_id = egui::Id::unique("shortcut-ball-click-at");
    let last: f64 = ctx.data(|d| d.get_temp::<f64>(click_id)).unwrap_or(-1.0);
    if resp.clicked() && (now - last).abs() > 1e-4 {
        ctx.data_mut(|d| d.insert_temp(click_id, now));
        open = !open;
        edge = 0;
    }
    let alpha = if edge != 0 && !open { 44 } else { 255 };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("click guard already installed")
        return
    if src.count(OLD) < 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("ball toggles once per tap")


if __name__ == "__main__":
    main()
