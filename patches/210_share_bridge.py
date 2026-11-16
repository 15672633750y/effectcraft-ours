#!/usr/bin/env python3
"""系统分享桥：把文件交给任意 App（QQ、微信、邮件…），走系统的分享面板。

Rust cannot start an Intent itself, and the app already talks to Java through files (the gallery
publisher works that way), so sharing uses the same seam: the engine writes the path it wants shared
to `DCIM/EffectCraft/.share-request`, and a Java thread picks it up and shows
`Intent.createChooser(ACTION_SEND)`.

The content Uri comes from MediaStore (the file is already scanned for the gallery), so no
FileProvider entry is needed in the generated manifest — one less thing that can break at build time.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHARE_BRIDGE_V1"

JAVA = '''
    // EFFECTCRAFT_OURS_SHARE_BRIDGE_V1 — 系统分享面板（任意 App）
    private volatile boolean oursShareRunning = false;

    private void startShareWatcher() {
        if (oursShareRunning) return;
        oursShareRunning = true;
        Thread thread = new Thread(() -> {
            while (oursShareRunning) {
                try {
                    oursSharePass();
                    Thread.sleep(1200L);
                } catch (InterruptedException e) {
                    return;
                } catch (Throwable ignored) {
                }
            }
        }, "share-watcher");
        thread.setDaemon(true);
        thread.start();
    }

    private void oursSharePass() {
        java.io.File req = new java.io.File("/storage/emulated/0/DCIM/EffectCraft/.share-request");
        if (!req.isFile()) return;
        String path = null;
        try {
            byte[] raw = java.nio.file.Files.readAllBytes(req.toPath());
            path = new String(raw, "UTF-8").trim();
        } catch (Throwable ignored) {
            return;
        }
        if (path == null || path.isEmpty()) {
            req.delete();
            return;
        }
        java.io.File f = new java.io.File(path);
        if (!f.isFile()) return;
        android.net.Uri uri = oursMediaUri(f);
        if (uri == null) {
            // Not in the media database yet: ask the scanner and try again on the next pass.
            android.media.MediaScannerConnection.scanFile(this, new String[]{f.getAbsolutePath()}, null, null);
            return;
        }
        req.delete();
        try {
            String name = f.getName().toLowerCase(java.util.Locale.ROOT);
            String type = name.endsWith(".mp4") ? "video/mp4"
                : name.endsWith(".mov") ? "video/quicktime"
                : name.endsWith(".zip") ? "application/zip"
                : name.endsWith(".xml") ? "application/xml"
                : name.endsWith(".ecproj") ? "application/octet-stream"
                : "application/octet-stream";
            android.content.Intent send = new android.content.Intent(android.content.Intent.ACTION_SEND);
            send.setType(type);
            send.putExtra(android.content.Intent.EXTRA_STREAM, uri);
            send.putExtra(android.content.Intent.EXTRA_SUBJECT, f.getName());
            send.addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
            android.content.Intent chooser = android.content.Intent.createChooser(send, "分享 " + f.getName());
            chooser.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(chooser);
        } catch (Throwable ignored) {
        }
    }

    private android.net.Uri oursMediaUri(java.io.File f) {
        try {
            android.net.Uri files = android.provider.MediaStore.Files.getContentUri("external");
            String[] proj = {android.provider.MediaStore.MediaColumns._ID};
            String sel = android.provider.MediaStore.MediaColumns.DATA + "=?";
            try (android.database.Cursor c = getContentResolver().query(files, proj, sel, new String[]{f.getAbsolutePath()}, null)) {
                if (c != null && c.moveToFirst()) {
                    long id = c.getLong(0);
                    return android.content.ContentUris.withAppendedId(files, id);
                }
            }
        } catch (Throwable ignored) {
        }
        return null;
    }
'''

HOOK_OLD = "    @Override\n    protected void onCreate(Bundle savedInstanceState) {\n        super.onCreate(savedInstanceState);\n"
HOOK_NEW = JAVA + "\n" + HOOK_OLD

START_OLD = "        super.onCreate(savedInstanceState);\n"
START_NEW = "        super.onCreate(savedInstanceState);\n        try { startShareWatcher(); } catch (Throwable ignored) { }\n"


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("share bridge already installed")
        return
    if src.count(HOOK_OLD) != 1:
        raise SystemExit(f"hook: {src.count(HOOK_OLD)}")
    src = src.replace(HOOK_OLD, HOOK_NEW, 1)
    if src.count(START_OLD) != 1:
        raise SystemExit(f"start hook: {src.count(START_OLD)}")
    src = src.replace(START_OLD, START_NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("share watcher installed in the activity")


if __name__ == "__main__":
    main()
