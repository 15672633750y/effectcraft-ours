#!/usr/bin/env python3
"""设置的真实位置是 `<files>/prefs.json`，不是 `<files>/settings/prefs.json`——备份一直找错地方。

`DirConfig` 把 `prefs.json` 直接放在配置目录根下（引擎里 `c.read(PREFS_FILE)`），所以按旧路径
复制永远找不到文件，`settings.json` 也就从未生成。两个位置都找，找到哪个用哪个。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SETTINGS_PATH_V1"

OLD = """            java.io.File dir = new java.io.File(getFilesDir(), "settings");
"""
NEW = """            java.io.File dir = prefsDir();
"""
FN = r'''

    /// EFFECTCRAFT_OURS_SETTINGS_PATH_V1 — prefs.json 可能在 files/ 根下，也可能在 files/settings/。
    private java.io.File prefsDir() {
        java.io.File flat = getFilesDir();
        if (new java.io.File(flat, "prefs.json").isFile()) {
            return flat;
        }
        java.io.File nested = new java.io.File(flat, "settings");
        if (new java.io.File(nested, "prefs.json").isFile()) {
            return nested;
        }
        return flat;
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("settings path already fixed")
        return
    if src.count(OLD) != 2:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    src = src.replace(OLD, NEW)
    anchor = "    /// EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor2: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("settings backup looks in both locations")


if __name__ == "__main__":
    main()
