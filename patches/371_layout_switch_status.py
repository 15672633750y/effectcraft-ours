#!/usr/bin/env python3
"""切换布局后给一句明确反馈：`已切换到 CapCut（竖屏排法）`。

中央浮出的名字只在画布中央出现约 1 秒，如果当时在看别处就错过了；状态栏这行留得更久。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_SWITCH_STATUS_V1"

OLD = '''                if applied {
                    ui.data_mut(|d| d.insert_temp(chosen_id, (now, name.to_string())));'''

NEW = '''                if applied {
                    // EFFECTCRAFT_OURS_LAYOUT_SWITCH_STATUS_V1 — 状态栏也给一句，别只靠中央浮字
                    let orient = if matches!(workspace, "capcut" | "blurrr" | "kuaishou" | "jianying") {
                        "竖屏排法"
                    } else {
                        "横屏排法"
                    };
                    self.ui.status = format!("已切换到 {name}（{orient}）");
                    ui.data_mut(|d| d.insert_temp(chosen_id, (now, name.to_string())));'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("switch status already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("layout switch reports layout + orientation in the status bar")


if __name__ == "__main__":
    main()
