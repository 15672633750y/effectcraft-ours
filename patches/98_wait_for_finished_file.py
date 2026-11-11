#!/usr/bin/env python3
"""Do not commit a document before the render has actually been flushed to disk.

The saves that produced 0-byte files happened because the staged file was still empty when the
save dialog's document was written. Wait briefly for the file to reach its final size, and fail
loudly instead of silently creating an empty document.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_WAIT_FOR_RENDER_V1"
ANCHOR = "        try {\n            String uriText = getSharedPreferences(PREFS, MODE_PRIVATE).getString(\"uri:\" + path, null);"
WAIT = '''        try {
            // Wait for the renderer to finish writing before handing the file to SAF.
            java.io.File staged = new java.io.File(path);
            long lastSize = -1;
            for (int i = 0; i < 40; i++) {
                long size = staged.isFile() ? staged.length() : 0;
                if (size > 0 && size == lastSize) break;
                lastSize = size;
                try { Thread.sleep(50); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); break; }
            }
            if (!staged.isFile() || staged.length() <= 0) {
                return "ERROR: the render has not been written yet (" + path + ")";
            }
            String uriText = getSharedPreferences(PREFS, MODE_PRIVATE).getString("uri:" + path, null);'''


def main() -> None:
    root = os.environ.get("ARTCRAFT_DIR") or ""
    if not root:
        print("ARTCRAFT_DIR not set; skipping the wait patch")
        return
    path = Path(root) / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("wait-for-render already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"safCommit anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, "        // " + MARKER + "\n" + WAIT, 1)
    path.write_text(src, encoding="utf-8")
    print("safCommit now waits for the render and refuses to create empty documents")


if __name__ == "__main__":
    main()
