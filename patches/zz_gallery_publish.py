#!/usr/bin/env python3
"""Finished renders show up in the phone's gallery again.

The app writes straight into `DCIM/EffectCraft`, but a plain file write does not tell the gallery
anything: on Android a video only appears once the media database knows it. A background thread
scans the output folder every few seconds and asks the media scanner about files it has not seen
yet, which is what makes them appear in 相册 (and in other apps' pickers).

Only finished files are announced: anything still growing is left for the next pass, and the
interrupted folder is ignored.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GALLERY_PUBLISH_V1"

CODE = '''
    // EFFECTCRAFT_OURS_GALLERY_PUBLISH_V1 — 让导出的视频出现在相册里
    private final java.util.HashMap<String, Long> oursPublished = new java.util.HashMap<>();
    private volatile boolean oursPublishRunning = false;

    private void startGalleryPublish() {
        if (oursPublishRunning) return;
        oursPublishRunning = true;
        Thread thread = new Thread(() -> {
            while (oursPublishRunning) {
                try {
                    oursPublishPass();
                    Thread.sleep(3000L);
                } catch (InterruptedException e) {
                    return;
                } catch (Throwable ignored) {
                }
            }
        }, "gallery-publish");
        thread.setDaemon(true);
        thread.start();
    }

    private void oursPublishPass() {
        java.io.File dir = new java.io.File("/storage/emulated/0/DCIM/EffectCraft");
        java.io.File[] files = dir.listFiles();
        if (files == null) return;
        for (java.io.File f : files) {
            if (!f.isFile()) continue;
            String name = f.getName();
            String lower = name.toLowerCase(java.util.Locale.ROOT);
            if (!lower.endsWith(".mp4") && !lower.endsWith(".mov")) continue;
            if (name.startsWith(".") || name.startsWith("未正常导出-")) continue;
            long size = f.length();
            if (size <= 0) continue;
            Long known = oursPublished.get(name);
            if (known != null && known == size) continue;
            // 还在写的文件（大小在变）不计，等下一次；给编码器 4 秒收尾。
            if (System.currentTimeMillis() - f.lastModified() < 4000L) continue;
            oursPublished.put(name, size);
            try {
                android.media.MediaScannerConnection.scanFile(this, new String[]{f.getAbsolutePath()}, null, null);
            } catch (Throwable ignored) {
            }
        }
    }
'''

CALL_OLD = '        installCrashLogger();\n'
CALL_NEW = '''        installCrashLogger();
        // 相册发布：后台线程，和首帧无关。
        try {
            startGalleryPublish();
        } catch (Throwable ignored) {
        }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("gallery publish already installed")
        return
    anchor = "    private void installCrashLogger() {"
    if src.count(anchor) != 1:
        raise SystemExit(f"method anchor: {src.count(anchor)}")
    src = src.replace(anchor, CODE + "\n" + anchor, 1)
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("finished renders are announced to the gallery")


if __name__ == "__main__":
    main()
