#!/usr/bin/env python3
"""一次性清理：删掉 Scripts 里那几个明显不是效果插件的大压缩包。

`Android/data/<pkg>/` 只有应用自己能写，用户用文件管理器进不去，所以让 App 启动时自己删一次。
结果写到 DCIM/EffectCraft/cleanup.txt，删了什么、省了多少空间一目了然。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLEANUP_SCRIPTS_V1"

HOOK = "        restoreSettingsBackup();\n"
FN = r'''

    /// EFFECTCRAFT_OURS_CLEANUP_SCRIPTS_V1 — 一次性删掉 Scripts 里的无关大文件。
    private void cleanupScripts() {
        try {
            java.io.File ext = getExternalFilesDir(null);
            if (ext == null) {
                return;
            }
            java.io.File dir = new java.io.File(new java.io.File(ext, "config"), "Scripts");
            String[] junk = {"LM Arena", "DeepSeek Harness", "XRecorder", "搜图神器", "QQagent"};
            StringBuilder log = new StringBuilder();
            long freed = 0;
            java.io.File[] files = dir.listFiles();
            if (files != null) {
                for (java.io.File f : files) {
                    if (!f.isFile()) {
                        continue;
                    }
                    for (String key : junk) {
                        if (f.getName().contains(key)) {
                            long len = f.length();
                            if (f.delete()) {
                                freed += len;
                                log.append("deleted ").append(f.getName()).append(" (").append(len).append("B)\n");
                            } else {
                                log.append("failed  ").append(f.getName()).append('\n');
                            }
                            break;
                        }
                    }
                }
            }
            log.append("freed=").append(freed / 1048576).append(" MB\n");
            java.io.File out = new java.io.File(new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft"), "cleanup.txt");
            try (java.io.FileWriter w = new java.io.FileWriter(out, false)) {
                w.write(log.toString());
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
        print("cleanup already present")
        return
    if src.count(HOOK) != 1:
        raise SystemExit(f"hook: {src.count(HOOK)}")
    src = src.replace(HOOK, "        restoreSettingsBackup();\n        cleanupScripts();\n", 1)
    anchor = "    /// EFFECTCRAFT_OURS_SETTINGS_BACKUP_V1"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("one-shot Scripts cleanup enabled")


if __name__ == "__main__":
    main()
