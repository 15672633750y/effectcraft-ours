#!/usr/bin/env python3
"""Publish a finished export to the Android gallery as well as the chosen document.

After the save dialog's document is written, the file is inserted into MediaStore.Video under
DCIM/EffectCraft, which is what makes it appear in the gallery immediately.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GALLERY_PUBLISH_V1"

PUBLISH = '''
    /** Copy a finished render into DCIM/EffectCraft and register it with MediaStore. */
    private void publishToGallery(String path) {
        try {
            if (android.os.Build.VERSION.SDK_INT < 29) return;
            java.io.File src = new java.io.File(path);
            if (!src.isFile() || src.length() <= 0) return;
            String name = src.getName();
            String lower = name.toLowerCase(java.util.Locale.ROOT);
            String mime = lower.endsWith(".mov") ? "video/quicktime"
                : lower.endsWith(".webm") ? "video/webm"
                : lower.endsWith(".mp4") || lower.endsWith(".m4v") ? "video/mp4"
                : "application/octet-stream";
            android.content.ContentValues values = new android.content.ContentValues();
            values.put(android.provider.MediaStore.Video.Media.DISPLAY_NAME, name);
            values.put(android.provider.MediaStore.Video.Media.MIME_TYPE, mime);
            values.put(android.provider.MediaStore.Video.Media.RELATIVE_PATH, "DCIM/EffectCraft");
            values.put(android.provider.MediaStore.Video.Media.IS_PENDING, 1);
            android.net.Uri target = getContentResolver().insert(
                android.provider.MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
            if (target == null) return;
            try (java.io.InputStream in = new java.io.FileInputStream(src);
                 java.io.OutputStream out = getContentResolver().openOutputStream(target, "w")) {
                if (out == null) return;
                byte[] buffer = new byte[256 * 1024];
                int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
                out.flush();
            }
            android.content.ContentValues done = new android.content.ContentValues();
            done.put(android.provider.MediaStore.Video.Media.IS_PENDING, 0);
            getContentResolver().update(target, done, null, null);
            Log.i(TAG, "Published render to DCIM/EffectCraft: " + name);
        } catch (Exception error) {
            Log.e(TAG, "Could not publish the render to the gallery", error);
        }
    }
'''


def main() -> None:
    root = os.environ.get("ARTCRAFT_DIR") or ""
    if not root:
        print("ARTCRAFT_DIR not set; skipping gallery publish")
        return
    path = Path(root) / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("gallery publish already installed")
        return
    # 1. call it right after a successful document commit
    old_call = "            return \"OK\";\n        } catch (Exception e) {\n            Log.e(TAG, \"Could not write a selected document\""
    if src.count(old_call) != 1:
        raise SystemExit(f"commit return anchor: expected 1, found {src.count(old_call)}")
    src = src.replace(
        old_call,
        "            // " + MARKER + "\n            publishToGallery(path);\n            return \"OK\";\n        } catch (Exception e) {\n            Log.e(TAG, \"Could not write a selected document\"",
        1,
    )
    # 2. add the method before the mime helper
    anchor = "    private static String mimeFor(String fileName) {"
    if src.count(anchor) != 1:
        raise SystemExit(f"mimeFor anchor: expected 1, found {src.count(anchor)}")
    src = src.replace(anchor, PUBLISH + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("exports now publish to DCIM/EffectCraft through MediaStore")


if __name__ == "__main__":
    main()
