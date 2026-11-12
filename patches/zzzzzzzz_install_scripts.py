#!/usr/bin/env python3
"""Pick up scripts and plug-ins dropped in Downloads and copy them into the app's config folder."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_INSTALL_SCRIPTS_V1"
ANCHOR = "        startGalleryWatcher();\n"

CODE = '''        installDroppedExtensions();
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("dropped extension import already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    method = '''
    // EFFECTCRAFT_OURS_INSTALL_SCRIPTS_V1
    /** Copies scripts/plug-ins the user dropped in Downloads into the config folder the app reads. */
    private void installDroppedExtensions() {
        java.io.File ext = getExternalFilesDir(null);
        if (ext == null) {
            return;
        }
        java.io.File config = new java.io.File(ext, "config");
        copyDropped(new java.io.File("/storage/emulated/0/Download/EffectCraftScripts"), new java.io.File(config, "Scripts"));
        copyDropped(new java.io.File("/storage/emulated/0/Download/EffectCraftPlugins"), new java.io.File(config, "Plug-ins"));
    }

    private void copyDropped(java.io.File from, java.io.File to) {
        if (from == null || !from.isDirectory()) {
            return;
        }
        if (!to.exists() && !to.mkdirs()) {
            return;
        }
        java.io.File[] files = from.listFiles();
        if (files == null) {
            return;
        }
        for (java.io.File f : files) {
            String n = f.getName().toLowerCase(java.util.Locale.ROOT);
            if (!f.isFile() || !(n.endsWith(".jsx") || n.endsWith(".js") || n.endsWith(".wasm") || n.endsWith(".wat") || n.endsWith(".zip"))) {
                continue;
            }
            java.io.File dst = new java.io.File(to, f.getName());
            try (java.io.InputStream in = new java.io.FileInputStream(f);
                 java.io.OutputStream out = new java.io.FileOutputStream(dst)) {
                byte[] buf = new byte[64 * 1024];
                int n2;
                while ((n2 = in.read(buf)) != -1) {
                    out.write(buf, 0, n2);
                }
                out.flush();
            } catch (Exception error) {
                Log.e(TAG, "could not install " + f.getName(), error);
            }
        }
    }
'''
    src = src.replace(ANCHOR, ANCHOR + CODE, 1)
    anchor2 = "    protected void onCreate(Bundle savedInstanceState) {\n"
    if src.count(anchor2) != 1:
        raise SystemExit("onCreate anchor missing")
    src = src.replace(anchor2, method + "\n" + anchor2, 1)
    path.write_text(src, encoding="utf-8")
    print("Downloads/EffectCraftScripts and Downloads/EffectCraftPlugins are installed at launch")


if __name__ == "__main__":
    main()
