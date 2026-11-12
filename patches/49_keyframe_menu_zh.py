#!/usr/bin/env python3
"""Chinese for the keyframe context menu and interpolation names."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_KEY_MENU_ZH_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"

ROWS = '''    // EFFECTCRAFT_OURS_KEY_MENU_ZH_V1
    ("Select Equal Keyframes", "选择相同关键帧"),
    ("Select Previous Keyframes", "选择前面的关键帧"),
    ("Select Following Keyframes", "选择后面的关键帧"),
    ("Linear", "线性"),
    ("Bezier", "贝塞尔"),
    ("Auto Bezier", "自动贝塞尔"),
    ("Continuous Bezier", "连续贝塞尔"),
    ("Hold", "定格"),
    ("Ease In", "缓入"),
    ("Ease Out", "缓出"),
    ("Ease In Ease Out", "缓入缓出"),
    ("Keyframe Interpolation…", "关键帧插值…"),
    ("Keyframe Velocity…", "关键帧速度…"),
    ("Roving Keyframes", "漫游关键帧"),
    ("Toggle Hold Keyframe", "切换定格关键帧"),
    ("Mute Keyframe", "静音关键帧"),
    ("Time-Reverse Keyframes", "时间反向关键帧"),
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("keyframe menu already translated")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"catalog anchor: expected 1, found {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + ROWS, 1), encoding="utf-8")
    print("keyframe context menu is Chinese now")


if __name__ == "__main__":
    main()
