#!/usr/bin/env python3
"""「多选」方块：切换多选模式（界面状态，不派发命令）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MULTI_TILE_V1"

OLD = '            run = Some(cmd);\n            payload = args.clone();'

NEW = '            // 多选是界面状态，不走命令\n            if *cmd == "ours.multiSelect" {\n                let id = egui::Id::new("ours-multi-mode");\n                let cur: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));\n                ui.ctx().data_mut(|d| d.insert_temp(id, !cur));\n            } else {\n                run = Some(cmd);\n                payload = args.clone();\n            }'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("multi tile already handled")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("multi tile toggles the mode")


if __name__ == "__main__":
    main()
