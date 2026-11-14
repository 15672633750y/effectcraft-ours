#!/usr/bin/env python3
"""Android always draws with OpenGL.

The launch guard switches Window Graphics to OpenGL *after* a launch that never settled, and it
saves that choice. But that only helps when the settings file can be written and the guard runs
first; a fresh install has nothing saved, so a cold start goes straight at Vulkan — the driver path
that crashes on this phone. Every launch after "swipe it out of recents" therefore crashed once and
then worked, because the crashed launch had left the marker that makes the next one pick OpenGL.

Forcing GL on Android ends the loop: there is no Vulkan attempt left to crash.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ANDROID_FORCE_GL_V1"

OLD = '''        let backends = (prefs.startup.window_graphics == "gl").then_some(Backends::GL);
'''
NEW = '''        let backends = (prefs.startup.window_graphics == "gl").then_some(Backends::GL);
        // EFFECTCRAFT_OURS_ANDROID_FORCE_GL_V1 — 安卓固定 OpenGL：Vulkan 在这台机器上每次冷启动都崩一次。
        #[cfg(target_os = "android")]
        let backends = Some(Backends::GL);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "apps/effectcraft/src/launch_guard.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("android already forced to OpenGL")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("Android always uses OpenGL")


if __name__ == "__main__":
    main()
