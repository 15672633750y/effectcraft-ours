#!/usr/bin/env python3
"""Keep the previous session's log where a file manager can see it, and drop old copies.

The session log lives under `Android/data/<package>/files/config/Logs`, which scoped storage hides,
and a native crash leaves nothing this side can write. So every launch copies the previous session's
log into `DCIM/EffectCraft` through MediaStore (which the export path already proves works). Only
the three newest copies are kept, so the folder never fills up.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LOG_EXPORT_V2"
ANCHOR = "        installCrashLogger();\n"

CODE = """        // 首帧之后再读日志、清理旧文件，别和启动抢时间
        try {
            final android.view.View lv = getWindow() != null ? getWindow().getDecorView() : null;
            final Runnable lj = () -> {
                try { oursExportLastLog(); } catch (Throwable ignored) { }
                try { oursCleanPendingRenders(); } catch (Throwable ignored) { }
            };
            if (lv != null) lv.postDelayed(lj, 1800L); else lj.run();
        } catch (Throwable ignored) {
        }
"""

METHODS = '''
    // EFFECTCRAFT_OURS_LOG_EXPORT_V2
    private static String oursReadText(java.io.File file) {
        try (java.io.InputStream in = new java.io.FileInputStream(file)) {
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] buffer = new byte[64 * 1024];
            int count;
            while ((count = in.read(buffer)) != -1) {
                out.write(buffer, 0, count);
                if (out.size() > 4 * 1024 * 1024) break;
            }
            return out.toString("UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    /** The previous session's log, published so a file manager can see it (keeps the newest three). */
    private void oursExportLastLog() {
        try {
            java.io.File ext = getExternalFilesDir(null);
            if (ext == null) return;
            java.io.File logs = new java.io.File(ext, "config/Logs");
            // 取最近改动过的那个日志：Rust 那边启动时才轮转，所以我们看到的
            // `effectcraft.log` 往往还是上一次会话的内容，`.1.log` 可能更旧。
            java.io.File previous = null;
            for (String candidate : new String[] {"effectcraft.log", "effectcraft.1.log", "effectcraft.2.log"}) {
                java.io.File f = new java.io.File(logs, candidate);
                if (!f.isFile() || f.length() <= 0) continue;
                if (previous == null || f.lastModified() > previous.lastModified()) previous = f;
            }
            if (previous == null) return;
            // 正在写的那个（刚改过）不复制，否则每次启动都会复制一份半截日志。
            if (System.currentTimeMillis() - previous.lastModified() < 5000L) return;
            java.io.File stamp = new java.io.File(logs, ".exported");
            if (stamp.isFile() && stamp.lastModified() >= previous.lastModified()) return;
            String text = oursReadText(previous);
            if (text.isEmpty()) return;
            String name = "effectcraft-log-" + System.currentTimeMillis() + ".txt";
            android.content.ContentValues values = new android.content.ContentValues();
            values.put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, name);
            values.put(android.provider.MediaStore.MediaColumns.MIME_TYPE, "text/plain");
            values.put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, "DCIM/EffectCraft");
            android.net.Uri target = getContentResolver().insert(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (target != null) {
                try (java.io.OutputStream out = getContentResolver().openOutputStream(target, "w")) {
                    if (out != null) out.write(text.getBytes("UTF-8"));
                }
            }
            stamp.createNewFile();
            stamp.setLastModified(previous.lastModified());
            oursTrimOldLogs();
        } catch (Throwable ignored) {
        }
    }

    /** Keep the three newest `effectcraft-log-*.txt` copies in DCIM/EffectCraft. */
    private void oursTrimOldLogs() {
        try {
            java.util.ArrayList<android.net.Uri> found = new java.util.ArrayList<>();
            java.util.ArrayList<Long> stamps = new java.util.ArrayList<>();
            String[] cols = {android.provider.MediaStore.MediaColumns._ID, android.provider.MediaStore.MediaColumns.DISPLAY_NAME};
            String where = android.provider.MediaStore.MediaColumns.DISPLAY_NAME + " LIKE ?";
            try (android.database.Cursor c = getContentResolver().query(
                    android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, cols, where, new String[] {"effectcraft-log-%"}, null)) {
                if (c == null) return;
                int idCol = c.getColumnIndex(android.provider.MediaStore.MediaColumns._ID);
                int nameCol = c.getColumnIndex(android.provider.MediaStore.MediaColumns.DISPLAY_NAME);
                while (c.moveToNext()) {
                    String n = c.getString(nameCol);
                    long stamp = 0;
                    try {
                        String digits = n.replaceAll("[^0-9]", "");
                        if (!digits.isEmpty()) stamp = Long.parseLong(digits);
                    } catch (Exception ignored) {
                    }
                    found.add(android.content.ContentUris.withAppendedId(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, c.getLong(idCol)));
                    stamps.add(stamp);
                }
            }
            while (stamps.size() > 3) {
                int oldest = 0;
                for (int i = 1; i < stamps.size(); i++) {
                    if (stamps.get(i) < stamps.get(oldest)) oldest = i;
                }
                try {
                    getContentResolver().delete(found.get(oldest), null, null);
                } catch (Exception ignored) {
                }
                found.remove(oldest);
                stamps.remove(oldest);
            }
        } catch (Throwable ignored) {
        }
    }

    /** Remove `.pending-*.mp4` a killed publish left in DCIM/EffectCraft (nothing lists them). */
    private void oursCleanPendingRenders() {
        try {
            java.io.File dir = new java.io.File("/storage/emulated/0/DCIM/EffectCraft");
            java.io.File[] files = dir.listFiles();
            if (files == null) return;
            long cutoff = System.currentTimeMillis() - 24L * 60L * 60L * 1000L;
            for (java.io.File file : files) {
                String name = file.getName();
                if (!name.startsWith(".pending-") || !file.isFile()) continue;
                if (file.lastModified() < cutoff) file.delete();
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
        print("log export already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + CODE, 1)
    helper = "    private static String mimeFor(String fileName) {"
    if src.count(helper) != 1:
        raise SystemExit(f"mimeFor anchor: {src.count(helper)}")
    path.write_text(src.replace(helper, METHODS + "\n" + helper, 1), encoding="utf-8")
    print("every launch keeps the previous session log (newest three)")


if __name__ == "__main__":
    main()
