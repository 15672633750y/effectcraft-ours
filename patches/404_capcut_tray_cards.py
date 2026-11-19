#!/usr/bin/env python3
"""CapCut（图 1）底部那一排是**大圆角卡片按钮**（浅灰底、图标+文字），不是纯图标。

给 capcut 的工具条换成卡片样式：每格内画一个圆角矩形（field_bg，悬停 accent 20%），
图标与文字仍在上层。其他布局保持原样式。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TRAY_CARDS_V1"

OLD = '''                        let hot = resp.hovered();
                        if hot {
                            clip.rect_filled(
                                cell.shrink(3.0),
                                10.0,
                                self.tokens.accent.gamma_multiply(0.16),
                            );
                        }'''

NEW = '''                        let hot = resp.hovered();
                        // EFFECTCRAFT_OURS_TRAY_CARDS_V1 — CapCut 用大圆角卡片按钮
                        if hot {
                            clip.rect_filled(
                                cell.shrink(3.0),
                                10.0,
                                self.tokens.accent.gamma_multiply(0.16),
                            );
                        } else if ws == "capcut" {
                            clip.rect_filled(
                                cell.shrink2(egui::vec2(6.0, 6.0)),
                                12.0,
                                self.tokens.field_bg,
                            );
                        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tray cards already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("capcut tray uses rounded cards")


if __name__ == "__main__":
    main()
