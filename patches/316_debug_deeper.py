#!/usr/bin/env python3
"""把目录导出的深度加到 6 层，并额外导出外部私有目录，直到找到 prefs.json 为止。

The 3-level dump showed no JSON at all, so settings must live deeper (or in the external files dir).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DEBUG_FILES_V2"


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("deeper dump already present")
        return
    old = '        if (depth > 3) {'
    if src.count(old) != 1:
        raise SystemExit(f"depth anchor: {src.count(old)}")
    src = src.replace(old, '        if (depth > 6) {', 1)
    old2 = '            sb.append("filesDir=").append(getFilesDir()).append(\'\\n\');'
    if src.count(old2) != 1:
        raise SystemExit(f"filesDir anchor: {src.count(old2)}")
    new2 = ('            sb.append("filesDir=").append(getFilesDir()).append(\'\\n\');\n'
            '            java.io.File ext = getExternalFilesDir(null);\n'
            '            sb.append("externalFilesDir=").append(ext).append(\'\\n\');\n'
            '            if (ext != null) {\n'
            '                walk(ext, "  ", 0, sb);\n'
            '            }')
    src = src.replace(old2, new2, 1)
    src = src.replace('/// EFFECTCRAFT_OURS_DEBUG_FILES_V1', '/// EFFECTCRAFT_OURS_DEBUG_FILES_V2', 1)
    path.write_text(src, encoding="utf-8")
    print("dump goes to depth 6 and includes the external dir")


if __name__ == "__main__":
    main()
