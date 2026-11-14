#!/usr/bin/env python3
"""The activity survives a rotation instead of being torn down and recreated.

Opening EffectCraft while the phone is turning (or rotating it during start-up) crashed it every
time: Android destroys and recreates the activity on a configuration change by default, and the
native window/graphics surface is re-created under the running app. Declaring the configuration
changes the app handles itself keeps the same activity (and the same surface) alive, which is what
every game and video app does.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CONFIG_CHANGES_V1"
CHANGES = "orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden|uiMode|density"

ANCHOR = '''        if activity.get("exported") is not None:
            attrs.append(f'android:exported="{"true" if activity["exported"] else "false"}"')
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/android_project.py"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("config changes already declared")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    add = '''        # EFFECTCRAFT_OURS_CONFIG_CHANGES_V1 — 旋转时不要重建 Activity（否则转屏就崩）
        if not activity.get("config_changes"):
            attrs.append('android:configChanges="''' + CHANGES + '''"')
'''
    path.write_text(src.replace(ANCHOR, ANCHOR + add, 1), encoding="utf-8")
    print("rotation no longer recreates the activity")


if __name__ == "__main__":
    main()
