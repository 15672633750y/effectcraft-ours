#!/usr/bin/env python3
"""Watch the app's output folder and publish every finished render to the gallery."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GALLERY_WATCHER_V1"
ANCHOR = "        installCrashLogger();\n"

CODE = '''        startGalleryWatcher();
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("gallery watcher already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"onCreate anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + CODE, 1)
    method = '''
    // EFFECTCRAFT_OURS_GALLERY_WATCHER_V1
    /** Poll the app's own output folder and push finished videos into DCIM/EffectCraft. */
    private void startGalleryWatcher() {
        Thread thread = new Thread(() -> {
            final java.util.Set<String> seen = new java.util.HashSet<>();
            while (true) {
                try {
                    java.io.File root = getExternalFilesDir(null);
                    if (root != null) {
                        scanForVideos(root, seen, 0);
                    }
                } catch (Throwable ignored) {
                    // keep watching
                }
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException stop) {
                    return;
                }
            }
        }, "gallery-watcher");
        thread.setDaemon(true);
        thread.start();
    }


    private boolean publishFile(java.io.File src) {
        try {
            if (android.os.Build.VERSION.SDK_INT < 29) {
                return false;
            }
            String name = src.getName();
            String lower = name.toLowerCase(java.util.Locale.ROOT);
            String mime = lower.endsWith(".mov") ? "video/quicktime" : "video/mp4";
            android.content.ContentValues values = new android.content.ContentValues();
            values.put(android.provider.MediaStore.Video.Media.DISPLAY_NAME, name);
            values.put(android.provider.MediaStore.Video.Media.MIME_TYPE, mime);
            values.put(android.provider.MediaStore.Video.Media.RELATIVE_PATH, "DCIM/EffectCraft");
            values.put(android.provider.MediaStore.Video.Media.IS_PENDING, 1);
            android.net.Uri target = getContentResolver().insert(
                android.provider.MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
            if (target == null) {
                return false;
            }
            try (java.io.InputStream in = new java.io.FileInputStream(src);
                 java.io.OutputStream out = getContentResolver().openOutputStream(target, "w")) {
                if (out == null) {
                    return false;
                }
                byte[] buffer = new byte[256 * 1024];
                int count;
                while ((count = in.read(buffer)) != -1) {
                    out.write(buffer, 0, count);
                }
                out.flush();
            }
            android.content.ContentValues done = new android.content.ContentValues();
            done.put(android.provider.MediaStore.Video.Media.IS_PENDING, 0);
            getContentResolver().update(target, done, null, null);
            return true;
        } catch (Exception error) {
            Log.e(TAG, "gallery publish failed", error);
            return false;
        }
    }

    private void scanForVideos(java.io.File dir, java.util.Set<String> seen, int depth) {
        if (depth > 4) {
            return;
        }
        java.io.File[] entries = dir.listFiles();
        if (entries == null) {
            return;
        }
        for (java.io.File entry : entries) {
            if (entry.isDirectory()) {
                scanForVideos(entry, seen, depth + 1);
                continue;
            }
            String name = entry.getName().toLowerCase(java.util.Locale.ROOT);
            boolean video = name.endsWith(".mp4") || name.endsWith(".mov") || name.endsWith(".m4v");
            if (!video || entry.length() <= 0) {
                continue;
            }
            String key = entry.getAbsolutePath() + ":" + entry.length();
            if (seen.contains(key)) {
                continue;
            }
            seen.add(key);
            if (publishFile(entry)) {
                Log.i(TAG, "Gallery watcher published " + entry.getName());
            }
        }
    }
'''
    anchor2 = "    protected void onCreate(Bundle savedInstanceState) {\n"
    if src.count(anchor2) != 1:
        raise SystemExit(f"method anchor: expected 1, found {src.count(anchor2)}")
    src = src.replace(anchor2, method + "\n" + anchor2, 1)
    path.write_text(src, encoding="utf-8")
    print("gallery watcher installed (publishes finished renders to DCIM/EffectCraft)")


if __name__ == "__main__":
    main()
