#!/usr/bin/env python3
"""Publish finished renders to the gallery — without copying imported footage.

The render queue writes its file into the app's own storage, which the gallery never sees, so a
watcher polls that folder and pushes new videos into `DCIM/EffectCraft`. It used to scan
everything, and the working copies of imported media live there too (`media/`) — importing two
clips added two copies to the gallery. It now skips the folders that hold working copies and
settings, so only renders are published.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GALLERY_WATCHER_V2"
ANCHOR = "        installCrashLogger();\n"

CODE = "        startGalleryWatcher();\n"

METHODS = '''
    // EFFECTCRAFT_OURS_GALLERY_WATCHER_V2
    /** Folders under the app storage that are not render output. */
    private static boolean oursIsOutputDir(String name) {
        String n = name.toLowerCase(java.util.Locale.ROOT);
        return !(n.equals("media") || n.equals("config") || n.equals("logs") || n.equals("models")
                || n.equals("plug-ins") || n.equals("plugins") || n.equals("scripts")
                || n.equals("cache") || n.equals("tmp") || n.equals("temp") || n.startsWith("."));
    }

    /** Poll the app's output folders and push finished videos into DCIM/EffectCraft. */
    private void startGalleryWatcher() {
        Thread thread = new Thread(() -> {
            final java.util.Set<String> seen = new java.util.HashSet<>();
            // Everything already on disk was published by an earlier run: seed the set so a
            // restart never re-publishes a render that is already in the gallery.
            try {
                java.io.File root = getExternalFilesDir(null);
                if (root != null) {
                    oursSeedSeen(root, seen, 0);
                }
            } catch (Throwable ignored) {
            }
            while (true) {
                try {
                    java.io.File root = getExternalFilesDir(null);
                    if (root != null) {
                        oursScanVideos(root, seen, 0);
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

    private void oursSeedSeen(java.io.File dir, java.util.Set<String> seen, int depth) {
        if (depth > 4) return;
        java.io.File[] entries = dir.listFiles();
        if (entries == null) return;
        for (java.io.File entry : entries) {
            if (entry.isDirectory()) {
                if (oursIsOutputDir(entry.getName())) oursSeedSeen(entry, seen, depth + 1);
                continue;
            }
            String name = entry.getName().toLowerCase(java.util.Locale.ROOT);
            boolean video = name.endsWith(".mp4") || name.endsWith(".mov") || name.endsWith(".m4v");
            if (video && entry.length() > 0) {
                seen.add(entry.getAbsolutePath() + ":" + entry.length() + ":" + entry.lastModified());
            }
        }
    }

    private void oursScanVideos(java.io.File dir, java.util.Set<String> seen, int depth) {
        if (depth > 4) return;
        java.io.File[] entries = dir.listFiles();
        if (entries == null) return;
        for (java.io.File entry : entries) {
            if (entry.isDirectory()) {
                if (oursIsOutputDir(entry.getName())) oursScanVideos(entry, seen, depth + 1);
                continue;
            }
            String name = entry.getName().toLowerCase(java.util.Locale.ROOT);
            boolean video = name.endsWith(".mp4") || name.endsWith(".mov") || name.endsWith(".m4v");
            if (!video) continue;
            if (name.endsWith(".part") || name.endsWith(".tmp") || name.endsWith(".partial")) continue;
            String key = entry.getAbsolutePath() + ":" + entry.length() + ":" + entry.lastModified();
            if (seen.contains(key)) continue;
            if (entry.length() <= 0) continue;
            if (oursPublishVideo(entry)) seen.add(key);
        }
    }

    private boolean oursPublishVideo(java.io.File src) {
        try {
            if (android.os.Build.VERSION.SDK_INT < 29) return false;
            String name = src.getName();
            String lower = name.toLowerCase(java.util.Locale.ROOT);
            String mime = lower.endsWith(".mov") ? "video/quicktime" : "video/mp4";
            android.content.ContentValues values = new android.content.ContentValues();
            values.put(android.provider.MediaStore.Video.Media.DISPLAY_NAME, name);
            values.put(android.provider.MediaStore.Video.Media.MIME_TYPE, mime);
            values.put(android.provider.MediaStore.Video.Media.RELATIVE_PATH, "DCIM/EffectCraft");
            values.put(android.provider.MediaStore.Video.Media.IS_PENDING, 1);
            android.net.Uri target = getContentResolver().insert(android.provider.MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
            if (target == null) return false;
            try (java.io.InputStream in = new java.io.FileInputStream(src);
                 java.io.OutputStream out = getContentResolver().openOutputStream(target, "w")) {
                if (out == null) return false;
                byte[] buffer = new byte[256 * 1024];
                int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
                out.flush();
            }
            android.content.ContentValues done = new android.content.ContentValues();
            done.put(android.provider.MediaStore.Video.Media.IS_PENDING, 0);
            getContentResolver().update(target, done, null, null);
            Log.i(TAG, "published render to DCIM/EffectCraft: " + name);
            return true;
        } catch (Throwable error) {
            Log.e(TAG, "gallery publish failed", error);
            return false;
        }
    }
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
    anchor = "    private static String mimeFor(String fileName) {"
    if src.count(anchor) != 1:
        raise SystemExit(f"mimeFor anchor: {src.count(anchor)}")
    src = src.replace(anchor, METHODS + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("gallery watcher publishes renders and skips working copies")


if __name__ == "__main__":
    main()
