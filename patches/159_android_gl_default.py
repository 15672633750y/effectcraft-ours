#!/usr/bin/env python3
"""Android starts on OpenGL, so the first launch after an install cannot die in the graphics driver.

The launch guard already switches to OpenGL *after* a launch that never settled — which is why a
build "crashed on first open, then worked": the second launch found the marker. On a fresh install
there is no marker yet, so the first launch always tried the Vulkan path that some phone drivers
crash in. Android now starts on OpenGL; Settings ▸ Startup & Repair ▸ Window Graphics can still be
set to Automatic (that choice is honoured, this only changes the default).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ANDROID_GL_V1"

OLD = "    let mut launch = launch_guard::Launch::begin(effectcraft_host::config_dir().as_deref(), std::env::var_os(\"WGPU_BACKEND\").is_some());\n"
NEW = '''    let mut launch = launch_guard::Launch::begin(effectcraft_host::config_dir().as_deref(), std::env::var_os("WGPU_BACKEND").is_some());
    // EFFECTCRAFT_OURS_ANDROID_GL_V1 — 安卓默认 OpenGL：装完第一次打开不会再在驱动里崩。
    // 启动守卫的“上次没正常起来就切 OpenGL”仍然有效，用户也可以在设置里改回自动。
    #[cfg(target_os = "android")]
    if launch.backends.is_none() {
        launch.backends = Some(eframe::wgpu::Backends::GL);
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "apps/effectcraft/src/main.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("android already defaults to OpenGL")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("Android starts on OpenGL")


if __name__ == "__main__":
    main()
