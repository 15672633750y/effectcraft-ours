#!/usr/bin/env python3
"""Android ignores the saved "window graphics" preference.

The crash happens while the Android splash (the big “Ae” icon) is still up — i.e. inside native
start-up, before the interface exists. Once the app is in, nothing crashes it. And it only starts
after the preferences have been written once: `Launch::begin` reads `startup.window_graphics` and,
when it says "gl", asks eframe for the OpenGL backend — a different graphics path, on a phone where
that path is what dies.

So on Android the saved preference no longer selects a backend: the app launches the way it did the
first time, which is the way that works. The setting stays in the UI (it is a desktop feature) but
does not steer the phone's graphics stack.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NO_SAVED_BACKEND_V1"
OLD = '        let backends = (prefs.startup.window_graphics == "gl").then_some(Backends::GL);\n'
NEW = '''        // EFFECTCRAFT_OURS_NO_SAVED_BACKEND_V1 — 安卓上不让“窗口图形”偏好切换后端：
        // 走 OpenGL 这条路径正是启动时闪退的原因，手机上始终用默认后端。
        #[cfg(target_os = "android")]
        let backends = None;
        #[cfg(not(target_os = "android"))]
        let backends = (prefs.startup.window_graphics == "gl").then_some(Backends::GL);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "apps/effectcraft/src/launch_guard.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("saved backend preference already ignored on Android")
        return
    n = src.count(OLD)
    if n != 2:
        raise SystemExit(f"anchor: expected 2, found {n}")
    src = src.replace(OLD, NEW)
    path.write_text(src, encoding="utf-8")
    print("Android always uses the default graphics backend")


if __name__ == "__main__":
    main()
