#!/usr/bin/env python3
"""崩溃日志只保留最近 5 个，别越攒越多。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CRASH_ROTATE_V1"

FN = r'''

    /// EFFECTCRAFT_OURS_CRASH_ROTATE_V1 — 只保留最近 5 个 crash-*.txt。
    private void rotateCrashLogs() {
        try {
            java.io.File dir = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft");
            java.io.File[] files = dir.listFiles();
            if (files == null) {
                return;
            }
            java.util.List<java.io.File> logs = new java.util.ArrayList<>();
            for (java.io.File f : files) {
                if (f.isFile() && f.getName().startsWith("crash-") && f.getName().endsWith(".txt")) {
                    logs.add(f);
                }
            }
            if (logs.size() <= 5) {
                return;
            }
            logs.sort(java.util.Comparator.comparingLong(java.io.File::lastModified));
            for (int i = 0; i < logs.size() - 5; i++) {
                logs.get(i).delete();
            }
        } catch (Throwable ignored) {
        }
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("crash rotation already present")
        return
    hook = "        cleanupScripts();\n"
    if src.count(hook) != 1:
        raise SystemExit(f"hook: {src.count(hook)}")
    src = src.replace(hook, hook + "        rotateCrashLogs();\n", 1)
    anchor = "    /// EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("crash logs are rotated")


if __name__ == "__main__":
    main()
