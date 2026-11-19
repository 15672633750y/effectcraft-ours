#!/usr/bin/env python3
"""工具条位置修正：不要压在底部状态条/提示上。

用户截图里底部工具条把「已切换到 …」的提示压在下面，而且紧贴屏幕边。
现在底部条上移 28px（让出状态行），右侧竖排整体上移 24px，顶部横条贴着我们自绘顶栏下方。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TRAY_POS_V1"

OLD_BOTTOM = '''                    let bar = egui::Rect::from_min_size(
                        egui::pos2(screen.min.x + 10.0, screen.max.y - h - 8.0),
                        egui::vec2(screen.width() - 20.0, h),
                    );'''
NEW_BOTTOM = '''                    // EFFECTCRAFT_OURS_TRAY_POS_V1 — 让出底部状态行，别把提示压住
                    let bar = egui::Rect::from_min_size(
                        egui::pos2(screen.min.x + 10.0, screen.max.y - h - 36.0),
                        egui::vec2(screen.width() - 20.0, h),
                    );'''

OLD_RAIL = '''                    let rail = egui::Rect::from_min_size(
                        egui::pos2(screen.max.x - w - 6.0, screen.center().y - ch * 2.0),
                        egui::vec2(w, ch * 4.0),
                    );'''
NEW_RAIL = '''                    let rail = egui::Rect::from_min_size(
                        egui::pos2(screen.max.x - w - 6.0, screen.center().y - ch * 2.0 - 24.0),
                        egui::vec2(w, ch * 4.0),
                    );'''

OLD_TOP = '''                    let strip = egui::Rect::from_min_size(
                        egui::pos2(screen.min.x + 8.0, screen.min.y + 40.0),
                        egui::vec2(screen.width() - 16.0, 42.0),
                    );'''
NEW_TOP = '''                    let strip = egui::Rect::from_min_size(
                        egui::pos2(screen.min.x + 8.0, screen.min.y + 6.0),
                        egui::vec2(screen.width() - 16.0, 42.0),
                    );'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tray position already fixed")
        return
    for name, old, new in (("bottom", OLD_BOTTOM, NEW_BOTTOM), ("rail", OLD_RAIL, NEW_RAIL), ("top", OLD_TOP, NEW_TOP)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("tool bars moved clear of the status line")


if __name__ == "__main__":
    main()
