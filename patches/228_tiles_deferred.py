#!/usr/bin/env python3
"""面板方块的命令延到下一帧开头执行：绝不在绘制途中改动文档。

Clicking a tile queued nothing before — it called `menus::invoke` while the frame was still drawing,
which is how a command can mutate the comp under the panels painting it. The click now stores the
command and the next frame runs it before any panel is drawn (one frame later, imperceptible).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TILES_DEFERRED_V1"

FRAME_OLD = "    fn frame(&mut self, ui: &mut egui::Ui) {\n        let ctx = ui.ctx().clone();\n"
FRAME_NEW = """    fn frame(&mut self, ui: &mut egui::Ui) {
        let ctx = ui.ctx().clone();
        // EFFECTCRAFT_OURS_TILES_DEFERRED_V1 — 上一帧点的面板方块，现在执行（绘制前）
        if let Some((cmd, payload)) = ui.ctx().data_mut(|d| d.remove_temp::<(String, serde_json::Value)>(egui::Id::unique("ours-pending-cmd"))) {
            if let Err(e) = crate::menus::invoke(self, &ctx, &cmd, payload) {
                self.ui.status = format!("{e}");
            }
        }
"""

RUN_OLD = """    if let Some(cmd) = run {
        // EFFECTCRAFT_OURS_TILES_VIA_INVOKE_V1 — 走菜单同一个入口，避免在绘制途中改文档
        match crate::menus::invoke(app, ui.ctx(), cmd, payload) {
            Ok(_) => {}
            Err(e) => {
                app.ui.status = format!("{e}");
            }
        }
    }
"""
RUN_NEW = """    if let Some(cmd) = run {
        // EFFECTCRAFT_OURS_TILES_DEFERRED_V1 — 记下来，下一帧开头再执行
        ui.ctx().data_mut(|d| d.insert_temp(egui::Id::unique("ours-pending-cmd"), (cmd.to_string(), payload)));
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tiles already deferred")
        return
    for old, new in ((FRAME_OLD, FRAME_NEW), (RUN_OLD, RUN_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("tile commands run at the start of the next frame")


if __name__ == "__main__":
    main()
