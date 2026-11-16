#!/usr/bin/env python3
"""设置跟着公共目录走：换包名（装成新 App）后，主题色/亮度/语言等不再重置。

The app's settings live in its private files dir, so a new package name starts with everything back at
defaults. This mirrors `prefs.json` to `DCIM/EffectCraft/settings.json`: on start it is restored when no
local settings exist yet, and on pause the current settings are written back.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1"

# 补丁按文件名字典序应用，`302_...` 排在 `99_crash_log.py` **之前**（ASCII 里 '3' < '9'），
# 那时 `installCrashLogger()` 还没被插入，用它当锚点会 0 次命中、整条构建失败。
# 改用 onCreate 里一定存在的一行，恢复设置的调用插在它后面，不依赖别的补丁。
HOOK = """        super.onCreate(savedInstanceState);
"""

FN = r'''

    /// EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1 — 公共目录里的 settings.json 是设置的唯一备份点。
    private void restoreSettingsBackup() {
        try {
            java.io.File pub = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft/settings.json");
            if (!pub.isFile()) {
                return;
            }
            java.io.File dir = new java.io.File(getFilesDir(), "settings");
            if (!dir.isDirectory() && !dir.mkdirs()) {
                return;
            }
            java.io.File local = new java.io.File(dir, "prefs.json");
            if (local.isFile() && local.length() > 0) {
                return; // 已经有本地设置，不动
            }
            copyFile(pub, local);
        } catch (Throwable ignored) {
        }
    }

    /// 把当前设置写回公共目录，换包/重装后可恢复。
    private void saveSettingsBackup() {
        try {
            java.io.File dir = new java.io.File(getFilesDir(), "settings");
            java.io.File local = new java.io.File(dir, "prefs.json");
            if (!local.isFile()) {
                return;
            }
            java.io.File out = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft");
            if (!out.isDirectory() && !out.mkdirs()) {
                return;
            }
            copyFile(local, new java.io.File(out, "settings.json"));
        } catch (Throwable ignored) {
        }
    }

    private void copyFile(java.io.File from, java.io.File to) throws java.io.IOException {
        try (java.io.InputStream in = new java.io.FileInputStream(from);
             java.io.OutputStream os = new java.io.FileOutputStream(to)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                os.write(buf, 0, n);
            }
        }
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("settings backup already present")
        return
    if src.count(HOOK) != 1:
        raise SystemExit(f"hook anchor: {src.count(HOOK)}")
    src = src.replace(HOOK, HOOK + "        restoreSettingsBackup();\n", 1)
    # 在 onDestroy 之前插入保存逻辑 + 方法体
    anchor = "    @Override\n    protected void onDestroy() {"
    if src.count(anchor) != 1:
        raise SystemExit(f"onDestroy anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    src = src.replace(anchor, "    @Override\n    protected void onDestroy() {\n        saveSettingsBackup();", 1)
    path.write_text(src, encoding="utf-8")
    print("settings are mirrored to DCIM/EffectCraft/settings.json")


if __name__ == "__main__":
    main()
