#!/usr/bin/env python3
"""把输出 APK 改成应用名开头：`ShimoveAex-0.24.1.apk`，而不是内部的 `effectcraft-…`。

$APP 是内部工程名，用户看到的文件名应该跟应用一致；没有 -appname 时退回原行为。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_APK_FILENAME_V1"

OLD_REL = '    FINAL_APK="$ROOT/output/$APP-$APP_VERSION.apk"\n'
NEW_REL = '    FINAL_APK="$ROOT/output/${APPNAME:-$APP}-$APP_VERSION.apk"\n'
OLD_DBG = '    FINAL_APK="$ROOT/output/$APP-$APP_VERSION-debug.apk"\n'
NEW_DBG = '    FINAL_APK="$ROOT/output/${APPNAME:-$APP}-$APP_VERSION-debug.apk"\n'


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/build-common.sh"
    src = path.read_text(encoding="utf-8")
    if MARKER in src or (NEW_REL in src and NEW_DBG in src):
        # 已经改过就是幂等的：这个补丁不写 MARKER（改的是 shell 变量行），所以按新文本判断
        print("apk filename already derived from the app name")
        return
    if src.count(OLD_REL) != 1 or src.count(OLD_DBG) != 1:
        raise SystemExit(f"anchors: {src.count(OLD_REL)} {src.count(OLD_DBG)}")
    src = src.replace(OLD_REL, NEW_REL, 1).replace(OLD_DBG, NEW_DBG, 1)
    path.write_text(src, encoding="utf-8")
    print("APK is named after the app")


if __name__ == "__main__":
    main()
