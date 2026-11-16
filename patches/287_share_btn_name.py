#!/usr/bin/env python3
"""按钮改名：完整工程分享 → 导出完整工程分享（说明文字同步）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHARE_BTN_NAME_V1"

EDITS = [('if ui.button("完整工程分享").clicked() {', 'if ui.button("导出完整工程分享").clicked() {'), ('egui::RichText::new("打包后保存在 DCIM/EffectCraft；点「完整工程分享」会弹出系统分享面板，可发给任意 App。").weak(),', 'egui::RichText::new("打包后保存在 DCIM/EffectCraft；点「导出完整工程分享」会弹出系统分享面板，可发给任意 App。").weak(),')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("button already renamed")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("share button renamed")


if __name__ == "__main__":
    main()
