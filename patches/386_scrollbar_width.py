#!/usr/bin/env python3
"""滚动条加粗到 12px，手机上才拖得住。

原来用 egui 默认宽度（约 6px），手指根本抓不到，看起来"画了但拖不动"。
这里把滚动条统一加宽、内边距收紧、常显（不只在悬停时出现）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SCROLL_WIDTH_V1"

OLD = '''        s.spacing.scroll = egui::style::ScrollStyle::solid();
        // The handle takes the text colour: the fill it would otherwise get is the colour of its
        // track (both are the field background), which left it invisible until hovered.
        s.spacing.scroll.foreground_color = true;'''

NEW = '''        // EFFECTCRAFT_OURS_SCROLL_WIDTH_V1 — 手机上手指抓不住 6px 的滚动条：统一加宽到 12px，常显。
        s.spacing.scroll = egui::style::ScrollStyle {
            bar_width: 12.0,
            bar_inner_margin: 3.0,
            bar_outer_margin: 2.0,
            floating: false,
            ..egui::style::ScrollStyle::solid()
        };
        // The handle takes the text colour: the fill it would otherwise get is the colour of its
        // track (both are the field background), which left it invisible until hovered.
        s.spacing.scroll.foreground_color = true;'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("scroll width already set")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("scroll bars widened to 12px")


if __name__ == "__main__":
    main()
