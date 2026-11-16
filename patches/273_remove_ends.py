#!/usr/bin/env python3
"""删掉还在引用 `ends` 的选点逻辑（手柄已经不再画了，编译报 E0425）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NO_ENDS_V1"

OLD = """            // 拖哪个点在手按下的那一刻决定一次，之后不换，免得线中途跳到另一个点。
            if canvas_resp.drag_started()
                && let Some(pos) = canvas_resp.interact_pointer_pos()
            {
                let which = u8::from(ends[1].distance_sq(pos) < ends[0].distance_sq(pos));
                ctx.data_mut(|d| d.insert_temp(pick_id, which));
            }
"""
NEW = """            // 没有手柄了：按下时不需要再选点，拖动时按位置自动决定改哪一段。
            let _ = pick_id;
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("ends already removed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("stale pick-by-handle code removed")


if __name__ == "__main__":
    main()
