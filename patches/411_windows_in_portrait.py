#!/usr/bin/env python3
"""修「导出点了没反应」：导出窗口原本只在 header::show 里被调用。

竖屏品牌布局换成了自绘顶栏（不走 header::show），于是 `export_window()` 整帧都没被调用——
点「导出」只是把 `ours-export-open` 设成 true，却没有任何代码把它画出来。

同样的问题也影响「插件」窗口。这里把两个函数改成 pub(crate)，并在竖屏分支里显式调用。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_WINDOWS_PORTRAIT_V1"

EXPORT_OLD = "fn export_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"
EXPORT_NEW = "pub(crate) fn export_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"

PLUGIN_OLD = "fn plugin_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"
PLUGIN_NEW = "pub(crate) fn plugin_window(app: &mut EffectcraftApp, ctx: &egui::Context) {"

CALL_OLD = '''        if ours_portrait {
            ours_shell_header(self, ui, header);
        } else {
            header::show(self, ui, header);
        }'''

CALL_NEW = '''        if ours_portrait {
            ours_shell_header(self, ui, header);
            // EFFECTCRAFT_OURS_WINDOWS_PORTRAIT_V1 — 这两个窗口原来只在 header::show 里被调用，
            // 竖屏自绘顶栏绕过了它，导致「导出」「插件」点了没反应。
            crate::header::export_window(self, ui.ctx());
            crate::header::plugin_window(self, ui.ctx());
        } else {
            header::show(self, ui, header);
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    hdr = root / "crates/ui-egui/src/header.rs"
    src = hdr.read_text(encoding="utf-8")
    if src.count(EXPORT_OLD) != 1 or src.count(PLUGIN_OLD) != 1:
        raise SystemExit(f"header anchors: {src.count(EXPORT_OLD)} {src.count(PLUGIN_OLD)}")
    src = src.replace(EXPORT_OLD, EXPORT_NEW, 1).replace(PLUGIN_OLD, PLUGIN_NEW, 1)
    hdr.write_text(src, encoding="utf-8")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("portrait windows already wired")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"frame anchor: {src.count(CALL_OLD)}")
    frame.write_text(src.replace(CALL_OLD, CALL_NEW, 1), encoding="utf-8")
    print("export/plugin windows are drawn in portrait layouts too")


if __name__ == "__main__":
    main()
