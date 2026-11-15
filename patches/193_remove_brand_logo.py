#!/usr/bin/env python3
"""工具栏左边的蓝色 A 标志（“关于”按钮）去掉。

It was a 24 px brand mark left of Home that opened the About dialog — the user asked for it to go.
About is still reachable from 帮助 ▸ 关于.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NO_BRAND_LOGO_V1"

OLD = '''    let brand = Rect::from_min_size(pos2(x, cy - 12.0), vec2(24.0, 24.0));
    paint_logo(p, brand);
    let bresp = ui.interact(brand, egui::Id::unique("brand"), Sense::click());
    app.auto.add_response("header.about", &bresp, "About EffectCraft");
    widgets::focus_outline(ui, &bresp, &t);
    // EFFECTCRAFT_OURS_ABOUT_DOUBLE_TAP_V1
    if bresp.on_hover_text(tr("About EffectCraft (double-tap)")).double_clicked() {
        app.dialog = Some(Dialog::About);
    }
    x += 32.0;
'''
NEW = '''    // EFFECTCRAFT_OURS_NO_BRAND_LOGO_V1 — 去掉左边的品牌图标（关于仍在 帮助 ▸ 关于）
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("brand logo already removed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("brand logo removed from the toolbar")


if __name__ == "__main__":
    main()
