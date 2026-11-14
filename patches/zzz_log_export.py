#!/usr/bin/env python3
"""Make a crash diagnosable: copy the previous session's log out to DCIM, and clear stuck pending files.

A Rust panic (or a kill) leaves nothing the file manager can see: the session log lives under
`Android/data/<package>/files/config/Logs`, which scoped storage hides, and the Rust side cannot
write to DCIM without broad storage access. So on the next launch the shell reads the previous
log, and when it contains `panic:` it publishes it through MediaStore — that is what the export
path already uses, so it always works. Files a killed publish left behind (`.pending-*.mp4`) are
removed after a day: they are half-made copies nothing can see.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LOG_EXPORT_V1"
ANCHOR = "        installCrashLogger();\n"

CODE = "        oursExportLastLog();\n        oursCleanPendingRenders();\n"

METHODS = '''
    // EFFECTCRAFT_OURS_LOG_EXPORT_V1
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

    /** The previous session's log, when it records a panic, published so a file manager can see it. */
    private void oursExportLastLog() {
        try {
            java.io.File ext = getExternalFilesDir(null);
            if (ext == null) return;
            java.io.File logs = new java.io.File(ext, "config/Logs");
            java.io.File previous = new java.io.File(logs, "effectcraft.1.log");
            if (!previous.isFile()) return;
            java.io.File stamp = new java.io.File(logs, ".exported");
            if (stamp.isFile() && stamp.lastModified() >= previous.lastModified()) return;
            String text = oursReadText(previous);
            if (!text.contains("panic:") && !text.contains("audio clock stalled")) return;
            android.content.ContentValues values = new android.content.ContentValues();
            values.put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, "effectcraft-log-" + System.currentTimeMillis() + ".txt");
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
    src = src.replace(helper, METHODS + "\n" + helper, 1)
    path.write_text(src, encoding="utf-8")
    print("previous-session log exported when it holds a panic")


if __name__ == "__main__":
    main()
