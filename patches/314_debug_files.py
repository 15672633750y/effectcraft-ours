#!/usr/bin/env python3
"""把应用私有目录的文件树写到 DCIM/EffectCraft/debug-files.txt，用来确认设置到底存在哪。

The settings backup never found `prefs.json`, so instead of guessing again this dumps the real layout of
`getFilesDir()` (3 levels deep) on start-up. One run then tells us the exact path.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DEBUG_FILES_V1"

HOOK = "        restoreSettingsBackup();\n"
FN = r'''

    /// EFFECTCRAFT_OURS_DEBUG_FILES_V1 — 把私有目录的文件树写出来，方便确认设置文件真实位置。
    private void dumpFiles() {
        try {
            StringBuilder sb = new StringBuilder();
            sb.append("filesDir=").append(getFilesDir()).append('\n');
            walk(getFilesDir(), "", 0, sb);
            java.io.File dir = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft");
            if (dir.isDirectory() || dir.mkdirs()) {
                try (java.io.FileWriter w = new java.io.FileWriter(new java.io.File(dir, "debug-files.txt"), false)) {
                    w.write(sb.toString());
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private void walk(java.io.File dir, String prefix, int depth, StringBuilder sb) {
        if (depth > 3) {
            return;
        }
        java.io.File[] kids = dir.listFiles();
        if (kids == null) {
            return;
        }
        for (java.io.File f : kids) {
            sb.append(prefix).append(f.getName());
            if (f.isFile()) {
                sb.append("  (").append(f.length()).append("B)");
            }
            sb.append('\n');
            if (f.isDirectory()) {
                walk(f, prefix + "  ", depth + 1, sb);
            }
        }
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("debug dump already present")
        return
    if src.count(HOOK) != 1:
        raise SystemExit(f"hook: {src.count(HOOK)}")
    src = src.replace(HOOK, "        restoreSettingsBackup();\n        dumpFiles();\n", 1)
    anchor = "    /// EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("file tree dump enabled")


if __name__ == "__main__":
    main()
