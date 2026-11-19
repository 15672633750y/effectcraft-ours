#!/usr/bin/env python3
"""导入面板在 AM / Blurrr 布局里点了没反应：它只在「项目」面板里被绘制。

`import_window()` 原来只在 `panels/project.rs` 的项目面板里调用，而 AM / Blurrr 布局
（预览 / 时间线 / 效果控件）没有项目面板 → 点「导入」只是把标志设成 true，没人画。

改成：函数 pub(crate)，由 frame.rs 每帧无条件调用一次；同时删掉项目面板里的那次调用，
避免同一窗口一帧画两遍。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_IMPORT_WINDOW_ALWAYS_V1"

DECL_OLD = "fn import_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"
DECL_NEW = "pub(crate) fn import_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"

CALL_OLD = "    import_window(app, ui.ctx());\n"
CALL_NEW = ""

FRAME_ANCHOR = '''        } else {
            header::show(self, ui, header);
        }'''

FRAME_INSERT = '''        } else {
            header::show(self, ui, header);
        }
        // EFFECTCRAFT_OURS_IMPORT_WINDOW_ALWAYS_V1 — 导入面板不属于某个面板，任何布局都要能弹出来
        crate::panels::project::import_window(self, ui.ctx());'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    proj = root / "crates/ui-egui/src/panels/project.rs"
    src = proj.read_text(encoding="utf-8")
    if DECL_OLD in src:
        src = src.replace(DECL_OLD, DECL_NEW, 1)
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"project call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    proj.write_text(src, encoding="utf-8")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("import window already global")
        return
    if src.count(FRAME_ANCHOR) != 1:
        raise SystemExit(f"frame anchor: {src.count(FRAME_ANCHOR)}")
    frame.write_text(src.replace(FRAME_ANCHOR, FRAME_INSERT, 1), encoding="utf-8")
    print("import window is drawn in every layout")


if __name__ == "__main__":
    main()
