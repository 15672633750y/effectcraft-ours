#!/usr/bin/env python3
"""分享面板在 UI 线程里弹出（后台线程直接 startActivity 在部分机型会崩）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHARE_UI_THREAD_V1"
OLD = "            startActivity(chooser);\n"
NEW = "            // EFFECTCRAFT_OURS_SHARE_UI_THREAD_V1 — 必须回到 UI 线程再弹\n            final android.content.Intent finalChooser = chooser;\n            runOnUiThread(() -> {\n                try {\n                    startActivity(finalChooser);\n                } catch (Throwable ignored) {\n                }\n            });\n"


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("share already runs on the UI thread")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("share chooser starts on the UI thread")


if __name__ == "__main__":
    main()
