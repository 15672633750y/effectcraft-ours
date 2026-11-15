#!/usr/bin/env python3
"""所有弹窗改成「快捷」面板那种玻璃样式：半透明深底、细亮边、大圆角、柔和阴影。

Every modal goes through `modal_fit_placed`, so restyling its frame restyles the whole app: the same
look as the new shortcut panel, with the text colours left alone so it stays easy to read.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GLASS_DIALOGS_V1"

OLD = "        .frame(egui::Frame::window(&ctx.style_of(ctx.theme())).fill(t.panel_bg).inner_margin(egui::Margin::same(18)))\n"
NEW = '''        // EFFECTCRAFT_OURS_GLASS_DIALOGS_V1 — 玻璃弹窗：半透明深底 + 细亮边 + 大圆角 + 柔和阴影
        .frame(
            egui::Frame::window(&ctx.style_of(ctx.theme()))
                .fill(Color32::from_rgba_unmultiplied(12, 12, 14, 200))
                .stroke(egui::Stroke::new(1.0, Color32::from_rgba_unmultiplied(255, 255, 255, 90)))
                .corner_radius(14.0)
                .shadow(egui::epaint::Shadow {
                    offset: [0, 6],
                    blur: 24,
                    spread: 0,
                    color: Color32::from_black_alpha(120),
                })
                .inner_margin(egui::Margin::same(18)),
        )
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/dialogs.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("dialogs already glass")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("dialogs use the glass frame")


if __name__ == "__main__":
    main()
