#!/usr/bin/env python3
"""Teach the Android save dialog the video/audio extensions EffectCraft exports.

Without them every render is offered as application/octet-stream, which is why Android saves
"Comp 1.bin" instead of "Comp 1.mp4" and the gallery never indexes the result.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ANDROID_MIME_V1"
ANCHOR = '        return "application/octet-stream";\n'
EXTRA = '''        // Video and image-sequence formats EffectCraft exports.
        if (lower.endsWith(".mp4") || lower.endsWith(".m4v")) return "video/mp4";
        if (lower.endsWith(".mov")) return "video/quicktime";
        if (lower.endsWith(".mkv")) return "video/x-matroska";
        if (lower.endsWith(".webm")) return "video/webm";
        if (lower.endsWith(".avi")) return "video/x-msvideo";
        if (lower.endsWith(".wav")) return "audio/wav";
        if (lower.endsWith(".mp3")) return "audio/mpeg";
        if (lower.endsWith(".aac") || lower.endsWith(".m4a")) return "audio/mp4";
        if (lower.endsWith(".aif") || lower.endsWith(".aiff")) return "audio/aiff";
        if (lower.endsWith(".exr")) return "image/x-exr";
        if (lower.endsWith(".dpx")) return "image/x-dpx";
        if (lower.endsWith(".tga")) return "image/x-tga";
        if (lower.endsWith(".psd")) return "image/vnd.adobe.photoshop";
'''


def main() -> None:
    root = os.environ.get("ARTCRAFT_DIR") or ""
    if not root:
        print("ARTCRAFT_DIR not set; skipping the Android MIME patch")
        return
    path = Path(root) / "templates/android/SafActivity.java"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("Android MIME types already patched")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"mime anchor: expected 1 match, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, f"        // {MARKER}\n" + EXTRA + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("Android save dialog now knows the video/audio extensions")


if __name__ == "__main__":
    main()
