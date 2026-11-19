#!/usr/bin/env python3
"""Blurrr 也加底部工具条（参考图里它底部同样有一排：剪辑/音乐/文字/特效/重叠/字幕）。

之前 Blurrr 只有顶部操作条，没有底部工具。现在两者都有：顶部管历史与导出，底部管素材与功能。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BLURRR_TRAY_V1"

OLD = '''                if ws == "capcut" || ws == "am" || ws == "kuaishou" {'''
NEW = '''                // EFFECTCRAFT_OURS_BLURR_TRAY_V1 — Blurrr 也保留底部工具条（顶条管历史/导出）
                if ws == "capcut" || ws == "am" || ws == "kuaishou" || ws == "blurrr" {'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("blurrr tray already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("blurrr got a bottom tray as well")


if __name__ == "__main__":
    main()
