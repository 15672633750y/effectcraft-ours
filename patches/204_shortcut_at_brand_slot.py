#!/usr/bin/env python3
"""「快捷」按钮放在工具栏最左边（原来蓝色 A 的位置），点开下方的空面板。

That slot is the first thing in the row, which is where the user asked for it from the start. Same
plain pattern as B/N (`ui.interact` + painted box + text), so the click is known to work.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_AT_START_V1"

ANCHOR = "    // EFFECTCRAFT_OURS_NO_BRAND_LOGO_V1 — 去掉左边的品牌图标（关于仍在 帮助 ▸ 关于）\n"
NEW = ANCHOR + '''    // EFFECTCRAFT_OURS_SHORTCUT_AT_START_V1 — 工具栏第一个按钮：快捷
    {
        let r = Rect::from_min_size(pos2(x, cy - 13.0), vec2(44.0, 26.0));
        let resp = ui.interact(r, egui::Id::unique("ours-shortcut"), Sense::click()).on_hover_text("快捷键面板");
        p.rect_filled(r, 5.0, t.switch_well);
        p.text(r.center(), Align2::CENTER_CENTER, "快捷", Tokens::ui(12.0), t.text);
        if resp.clicked() {
            let id = egui::Id::unique("ours-shortcut-open");
            let open: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
            ui.ctx().data_mut(|d| d.insert_temp(id, !open));
        }
        x += 48.0;
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("快捷 already at the start")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, NEW, 1), encoding="utf-8")
    print("快捷 button is the first in the toolbar")


if __name__ == "__main__":
    main()
