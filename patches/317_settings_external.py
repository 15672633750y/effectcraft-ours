#!/usr/bin/env python3
"""设置真正在外部私有目录：`Android/data/<pkg>/files/config/prefs.json`（实测 7950B）。

`getFilesDir()` 下面根本没有 prefs.json，所以之前的备份一次都没成功。改成先看外部私有目录的
`config/`，再退回内部目录。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SETTINGS_EXTERNAL_V1"

OLD_START = "    /// EFFECTCRAFT_OURS_SETTINGS_PATH_V1"
NEW_FN = r'''    /// EFFECTCRAFT_OURS_SETTINGS_EXTERNAL_V1 — 设置实际在外部私有目录的 config/ 下。
    private java.io.File prefsDir() {
        java.io.File ext = getExternalFilesDir(null);
        if (ext != null) {
            java.io.File cfg = new java.io.File(ext, "config");
            if (new java.io.File(cfg, "prefs.json").isFile()) {
                return cfg;
            }
            java.io.File root = ext;
            if (new java.io.File(root, "prefs.json").isFile()) {
                return root;
            }
        }
        java.io.File flat = getFilesDir();
        if (new java.io.File(flat, "prefs.json").isFile()) {
            return flat;
        }
        java.io.File nested = new java.io.File(flat, "settings");
        if (new java.io.File(nested, "prefs.json").isFile()) {
            return nested;
        }
        return ext != null ? new java.io.File(ext, "config") : flat;
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("external settings path already present")
        return
    start = src.find(OLD_START)
    if start < 0:
        raise SystemExit("prefsDir block not found (patch 313 must run first)")
    end = src.find("\n    }\n", src.find("private java.io.File prefsDir()", start))
    if end < 0:
        raise SystemExit("prefsDir body end not found")
    end += len("\n    }\n")
    src = src[:start] + NEW_FN + src[end:]
    path.write_text(src, encoding="utf-8")
    print("settings now read from the external private config dir")


if __name__ == "__main__":
    main()
