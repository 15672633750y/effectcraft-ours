#!/usr/bin/env python3
"""Write a crash stack trace to DCIM/EffectCraft so a first-launch crash can be diagnosed."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CRASH_LOG_V1"
ANCHOR = "    @Override\n    protected void onCreate(Bundle savedInstanceState) {\n        super.onCreate(savedInstanceState);\n"

HANDLER = '''    // EFFECTCRAFT_OURS_CRASH_LOG_V1
    private void installCrashLogger() {
        final Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
            try {
                java.io.StringWriter sw = new java.io.StringWriter();
                error.printStackTrace(new java.io.PrintWriter(sw));
                String text = sw.toString();
                try {
                    android.content.ContentValues v = new android.content.ContentValues();
                    String name = "crash-" + System.currentTimeMillis() + ".txt";
                    v.put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(android.provider.MediaStore.MediaColumns.MIME_TYPE, "text/plain");
                    v.put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, "DCIM/EffectCraft");
                    android.net.Uri uri = getContentResolver().insert(
                        android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    if (uri != null) {
                        try (java.io.OutputStream out = getContentResolver().openOutputStream(uri, "w")) {
                            if (out != null) out.write(text.getBytes("UTF-8"));
                        }
                    }
                } catch (Exception ignored) {
                    // Last resort: the app-private folder still keeps the trace for a later fix.
                    try (java.io.FileOutputStream out = new java.io.FileOutputStream(
                            new java.io.File(getExternalFilesDir(null), "crash.txt"))) {
                        out.write(text.getBytes("UTF-8"));
                    } catch (Exception ignored2) { }
                }
            } catch (Exception ignored) { }
            if (previous != null) previous.uncaughtException(thread, error);
        });
    }

'''


def main() -> None:
    root = os.environ.get("ARTCRAFT_DIR") or ""
    if not root:
        print("ARTCRAFT_DIR not set; skipping crash logger")
        return
    path = Path(root) / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("crash logger already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"onCreate anchor: expected 1, found {src.count(ANCHOR)}")
    combined = HANDLER + ANCHOR + "        installCrashLogger();\n"
    src = src.replace(ANCHOR, combined, 1)
    path.write_text(src, encoding="utf-8")
    print("crash logger installed (writes DCIM/EffectCraft/crash-*.txt)")


if __name__ == "__main__":
    main()
