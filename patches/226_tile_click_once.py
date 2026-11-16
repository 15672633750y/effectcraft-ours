#!/usr/bin/env python3
"""面板方块一次点击只执行一次（egui 每帧可能跑多趟，否则「裁剪」会被执行两遍）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILE_CLICK_ONCE_V1"

OLD = """        if resp.clicked() {
            run = Some(cmd);
            payload = args.clone();
        }
"""
NEW = """        // EFFECTCRAFT_OURS_TILE_CLICK_ONCE_V1 — 同一时刻只处理一次点击
        let now = ui.input(|i| i.time);
        let click_at = egui::Id::unique("ours-tile-click-at");
        let last: f64 = ui.ctx().data(|d| d.get_temp::<f64>(click_at)).unwrap_or(-1.0);
        if resp.clicked() && (now - last).abs() > 1e-4 {
            ui.ctx().data_mut(|d| d.insert_temp(click_at, now));
            run = Some(cmd);
            payload = args.clone();
        }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tile clicks already deduped")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("tile clicks run once per tap")


if __name__ == "__main__":
    main()
