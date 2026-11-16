#!/usr/bin/env python3
"""删掉面板拖动改动后遗留的 `latched`（编译错误 E0425）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LATCH_CLEANUP_V1"

OLD = """    ui.ctx().data_mut(|d| {
        d.insert_temp(off_id, off);
        d.insert_temp(latch_id, latched);
    });
"""
NEW = """    ui.ctx().data_mut(|d| {
        d.insert_temp(off_id, off);
    });
    let _ = latch_id;
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("latch leftover already removed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("removed the stale latched reference")


if __name__ == "__main__":
    main()
