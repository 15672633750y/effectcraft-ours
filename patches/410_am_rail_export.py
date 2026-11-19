#!/usr/bin/env python3
"""AM 左侧竖栏加到 5 格：多一个**导出**（code 13，已在共享处理器里接好）。

参考图里 AM 左侧那列有 5~6 个图标，我们原来只有 4 个（撤销/重做/播放/全屏）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AM_RAIL_EXPORT_V1"

HEIGHT_OLD = '''                        egui::pos2(screen.min.x + 6.0, screen.center().y - ch * 2.0),
                        egui::vec2(w, ch * 4.0),'''
HEIGHT_NEW = '''                        egui::pos2(screen.min.x + 6.0, screen.center().y - ch * 2.5),
                        egui::vec2(w, ch * 5.0),'''

ITEMS_OLD = '''                    let items: [(&str, u8, bool); 4] = [
                        ("\\u{27f2}", 5, undo_ready),
                        ("\\u{27f3}", 6, redo_ready),
                        ("\\u{25b6}", 4, true),
                        ("\\u{26f6}", 7, true),
                    ];'''
ITEMS_NEW = '''                    let items: [(&str, u8, bool); 5] = [
                        ("\\u{27f2}", 5, undo_ready),
                        ("\\u{27f3}", 6, redo_ready),
                        ("\\u{25b6}", 4, true),
                        ("\\u{26f6}", 7, true),
                        ("\\u{2191}", 13, true),
                    ];'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("rail export already present")
        return
    for name, old, new in (("height", HEIGHT_OLD, HEIGHT_NEW), ("items", ITEMS_OLD, ITEMS_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("AM rail now has undo/redo/play/fullscreen/export")


if __name__ == "__main__":
    main()
