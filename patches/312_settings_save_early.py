#!/usr/bin/env python3
"""设置备份：不只靠 onDestroy（用户划掉应用时常常不触发），启动 2.5 秒后和 onPause 都写一次。

The backup only ran from `onDestroy`, which Android often skips when the task is swiped away — so
`settings.json` never appeared and a new install had nothing to restore. This writes it shortly after
start-up as well, and on every pause.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SETTINGS_SAVE_EARLY_V1"

HOOK_OLD = "        restoreSettingsBackup();\n"
HOOK_NEW = (
    "        restoreSettingsBackup();\n"
    "        // 启动 2.5 秒后再写一次备份（onDestroy 不一定会被调用）\n"
    "        getWindow().getDecorView().postDelayed(this::saveSettingsBackup, 2500);\n"
)

PAUSE_METHOD = r'''

    /// EFFECTCRAFT_OURS_SETTINGS_SAVE_EARLY_V1 — 每次切到后台都写一次，划掉应用也不会丢。
    @Override
    protected void onPause() {
        super.onPause();
        saveSettingsBackup();
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("early settings save already present")
        return
    if src.count(HOOK_OLD) != 1:
        raise SystemExit(f"hook anchor: {src.count(HOOK_OLD)}")
    src = src.replace(HOOK_OLD, HOOK_NEW, 1)
    anchor = "    @Override\n    protected void onDestroy() {"
    if src.count(anchor) != 1:
        raise SystemExit(f"onDestroy anchor: {src.count(anchor)}")
    src = src.replace(anchor, PAUSE_METHOD + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("settings are saved early and on pause")


if __name__ == "__main__":
    main()
