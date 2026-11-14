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
    /** 上一次扫描看到的文件大小：判断文件是否已经写完。 */
    private final java.util.Map<String, Long> oursSizes = new java.util.HashMap<>();
    /** Both places the app can write: its external folder (where most output lands) and its internal one. */
    private java.io.File[] oursRoots() {
        java.io.File external = getExternalFilesDir(null);
        java.io.File internal = getFilesDir();
        java.io.File cache = getCacheDir();
        java.util.ArrayList<java.io.File> list = new java.util.ArrayList<>();
        if (external != null) list.add(external);
        if (internal != null) list.add(internal);
        if (cache != null) list.add(cache);
        return list.toArray(new java.io.File[0]);
    }

    /** Folders under the app storage that are not render output. */
    private static boolean oursIsOutputDir(String name) {
        String n = name.toLowerCase(java.util.Locale.ROOT);
        return !(n.equals("media") || n.equals("config") || n.equals("logs") || n.equals("models")
                || n.equals("plug-ins") || n.equals("plugins") || n.equals("scripts")
                || n.startsWith("."));
    }

    /** Poll the app's output folders and push finished videos into DCIM/EffectCraft. */
    private void startGalleryWatcher() {
        Thread thread = new Thread(() -> {
            final java.util.Set<String> seen = new java.util.HashSet<>();
            // Everything already on disk was published by an earlier run: seed the set so a
            // restart never re-publishes a render that is already in the gallery.
            try {
                for (java.io.File root : oursRoots()) {
                    if (root != null) {
                        oursSeedSeen(root, seen, 0);
                    }
                }
            } catch (Throwable ignored) {
            }
            try {
                oursSweepIncompleteRenders();
            } catch (Throwable ignored) {
            }
            while (true) {
                try {
                    for (java.io.File root : oursRoots()) {
                        if (root != null) {
                            oursScanVideos(root, seen, 0);
                        }
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
            long size = entry.length();
            if (size <= 0) continue;
            // 只发布“已经写完”的文件：大小和上一次扫描完全一样才发布。
            // 否则会把正在写入的半截文件拷进相册（那种 00:00、打不开的条目）。
            Long before = oursSizes.get(entry.getAbsolutePath());
            oursSizes.put(entry.getAbsolutePath(), size);
            if (before == null || before.longValue() != size) continue;
            if (entry.getAbsolutePath().toLowerCase(java.util.Locale.ROOT).endsWith(".part")) continue;
            // 再确认 mp4 写完整（有 moov 索引）：中断的渲染留下的是半截文件，发布出去也是打不开的。
            if (!oursLooksComplete(entry)) continue;
            if (oursPublishVideo(entry)) {
                seen.add(key);
                oursSizes.remove(entry.getAbsolutePath());
            }
        }
    }

    /** 中断的渲染（没有 moov 的半截 mp4）在 Renders/ 里超过一天就删掉。 */
    private void oursSweepIncompleteRenders() {
        long cutoff = System.currentTimeMillis() - 24L * 60L * 60L * 1000L;
        for (java.io.File root : oursRoots()) {
            if (root == null) continue;
            java.io.File[] dirs = root.listFiles();
            if (dirs == null) continue;
            for (java.io.File dir : dirs) {
                String dn = dir.getName().toLowerCase(java.util.Locale.ROOT);
                if (!dir.isDirectory() || !(dn.equals("renders") || dn.equals("render"))) continue;
                java.io.File[] files = dir.listFiles();
                if (files == null) continue;
                for (java.io.File f : files) {
                    if (!f.isFile()) continue;
                    if (f.lastModified() > cutoff) continue;
                    String n = f.getName().toLowerCase(java.util.Locale.ROOT);
                    boolean video = n.endsWith(".mp4") || n.endsWith(".mov") || n.endsWith(".m4v");
                    if (!video) continue;
                    if (!oursLooksComplete(f)) f.delete();
                }
            }
        }
    }

    /** mp4 是否写完整：文件头或末尾能找到 moov 索引。 */
    private static boolean oursLooksComplete(java.io.File file) {
        try {
            long size = file.length();
            if (size < 1024) return false;
            String name = file.getName().toLowerCase(java.util.Locale.ROOT);
            if (!name.endsWith(".mp4") && !name.endsWith(".mov") && !name.endsWith(".m4v")) return true;
            int headLen = (int) Math.min(8192, size);
            byte[] head = new byte[headLen];
            try (java.io.RandomAccessFile raf = new java.io.RandomAccessFile(file, "r")) {
                raf.readFully(head, 0, headLen);
            }
            if (oursHasMoov(head)) return true;
            int tailLen = (int) Math.min(262144, size);
            byte[] tail = new byte[tailLen];
            try (java.io.RandomAccessFile raf = new java.io.RandomAccessFile(file, "r")) {
                raf.seek(size - tailLen);
                raf.readFully(tail, 0, tailLen);
            }
            return oursHasMoov(tail);
        } catch (Throwable e) {
            return false;
        }
    }

    private static boolean oursHasMoov(byte[] bytes) {
        for (int i = 0; i + 3 < bytes.length; i++) {
            if (bytes[i] == 'm' && bytes[i + 1] == 'o' && bytes[i + 2] == 'o' && bytes[i + 3] == 'v') return true;
        }
        return false;
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
