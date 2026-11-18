#!/usr/bin/env python3
"""主题色改成亮青（原来是偏暗的蓝 #2D8CEB）。

用户反馈「效果控件那个蓝色也不正常，主题色没有那么暗」「很多场景下都会这样有蓝色」。
排查下来全站所有「蓝」都来自 theme.rs 的这两个值，而它们是蓝色不是主题青：

    accent:       #2D8CEB
    accent_hover: #4AA0F5

改成亮青，和界面里其它青色元素（时间码、播放头）一致：

    accent:       #00E5FF
    accent_hover: #5CF0FF
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCENT_CYAN_V1"

OLD = """            accent: Color32::from_rgb(0x2d, 0x8c, 0xeb),
            accent_hover: Color32::from_rgb(0x4a, 0xa0, 0xf5),"""
NEW = """            // EFFECTCRAFT_OURS_ACCENT_CYAN_V1 — 荧光青（原来是偏暗的蓝 #2D8CEB）
            accent: Color32::from_rgb(0x00, 0xe5, 0xff),
            accent_hover: Color32::from_rgb(0x5c, 0xf0, 0xff),"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/theme.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("accent already cyan")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"accent anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("accent -> #00E5FF (cyan)")


if __name__ == "__main__":
    main()
