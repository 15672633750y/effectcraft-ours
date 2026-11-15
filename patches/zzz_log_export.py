#!/usr/bin/env python3
"""The previous session's log lands in DCIM/EffectCraft as a text file, readable from a file manager.

The engine writes its log somewhere private — several places are possible, and on Android the
"config" directory can fall back to the cache. This copies the newest log it can find next to the
renders, so a crash can be looked at without a computer. It runs on a background thread 300 ms after
the window exists: a frozen interface thread must not be able to prevent it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LOG_EXPORT_V3"

CODE = '''
    // EFFECTCRAFT_OURS_LOG_EXPORT_V3 — 把上一次的日志复制到相册目录，文件管理器能直接看
    private void oursExportLogOnce() {
        try {
            java.util.ArrayList<java.io.File> dirs = new java.util.ArrayList<>();
            if (getExternalFilesDir(null) != null) {
                dirs.add(new java.io.File(getExternalFilesDir(null), "config/Logs"));
                dirs.add(new java.io.File(getExternalFilesDir(null), "Logs"));
            }
            if (getFilesDir() != null) {
                dirs.add(new java.io.File(getFilesDir(), "config/Logs"));
                dirs.add(new java.io.File(getFilesDir(), "Logs"));
            }
            if (getCacheDir() != null) dirs.add(new java.io.File(getCacheDir(), "Logs"));
            java.io.File newest = null;
            for (java.io.File dir : dirs) {
                java.io.File[] entries = dir.listFiles();
                if (entries == null) continue;
                for (java.io.File f : entries) {
                    if (!f.isFile() || f.length() <= 0) continue;
                    String n = f.getName().toLowerCase(java.util.Locale.ROOT);
                    if (!n.endsWith(".log") && !n.contains("effectcraft")) continue;
                    if (newest == null || f.lastModified() > newest.lastModified()) newest = f;
                }
            }
            if (newest == null) return;
            if (System.currentTimeMillis() - newest.lastModified() < 3000L) return;
            java.io.File outDir = new java.io.File("/storage/emulated/0/DCIM/EffectCraft");
            if (!outDir.isDirectory()) return;
            java.text.SimpleDateFormat fmt = new java.text.SimpleDateFormat("MMdd-HHmmss", java.util.Locale.ROOT);
            String stamp = fmt.format(new java.util.Date());
            java.io.File out = new java.io.File(outDir, "effectcraft-log-" + stamp + ".txt");
            try (java.io.InputStream in = new java.io.FileInputStream(newest);
                 java.io.OutputStream os = new java.io.FileOutputStream(out)) {
                byte[] buffer = new byte[64 * 1024];
                long copied = 0;
                int count;
                while ((count = in.read(buffer)) != -1 && copied < 8L * 1024L * 1024L) {
                    os.write(buffer, 0, count);
                    copied += count;
                }
                os.flush();
            }
            android.media.MediaScannerConnection.scanFile(this, new String[]{out.getAbsolutePath()}, null, null);
            // 只留最近 3 份。
            java.io.File[] logs = outDir.listFiles((d, n) -> n.startsWith("effectcraft-log-"));
            if (logs != null && logs.length > 3) {
                java.util.Arrays.sort(logs, (a, b) -> Long.compare(a.lastModified(), b.lastModified()));
                for (int i = 0; i < logs.length - 3; i++) logs[i].delete();
            }
        } catch (Throwable ignored) {
        }
    }
'''

CALL_OLD = '        installCrashLogger();\n'
CALL_NEW = '''        installCrashLogger();
        // 日志导出：后台线程，界面卡死也不影响它。
        try {
            new Thread(() -> {
                try {
                    Thread.sleep(300L);
                } catch (InterruptedException ignored) {
                }
                oursExportLogOnce();
            }, "log-export").start();
        } catch (Throwable ignored) {
        }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("log export already installed")
        return
    anchor = "    private void installCrashLogger() {"
    if src.count(anchor) != 1:
        raise SystemExit(f"method anchor: {src.count(anchor)}")
    src = src.replace(anchor, CODE + "\n" + anchor, 1)
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("the previous log is copied next to the renders")


if __name__ == "__main__":
    main()
