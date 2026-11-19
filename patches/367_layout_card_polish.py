#!/usr/bin/env python3
"""布局卡片的呈现再进一步：

* 卡片 92 → 108 高，缩略图 104×64 → 136×86（真实 dock 树的等比预览更大、更像"布局预览"）
* 名称/说明的位置跟着放大，避免挤在一起
* 缩略图按卡片高度垂直居中
* 竖屏工具条在打开对话框时不画，免得盖在弹窗上
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_CARD_POLISH_V1"

CARD_OLD = "            let card_h = 92.0;"
CARD_NEW = "            let card_h = 108.0;"

THUMB_OLD = '''                let th = Rect::from_min_size(Pos2::new(r.min.x + 12.0, r.min.y + 11.0), Vec2::new(104.0, 64.0));'''
THUMB_NEW = '''                let th = Rect::from_min_size(
                    Pos2::new(r.min.x + 12.0, r.center().y - 43.0),
                    Vec2::new(136.0, 86.0),
                );'''

NAME_OLD = '''                let np = Pos2::new(th.max.x + 12.0, r.min.y + 20.0);'''
NAME_NEW = '''                let np = Pos2::new(th.max.x + 14.0, r.center().y - 26.0);'''

DESC_OLD = '''                ui.painter().galley(Pos2::new(np.x, np.y + 24.0), dg, Color32::from_rgba_unmultiplied(180, 186, 198, alpha));'''
DESC_NEW = '''                ui.painter().galley(Pos2::new(np.x, np.y + 26.0), dg, Color32::from_rgba_unmultiplied(180, 186, 198, alpha));'''

CARDW_OLD = "            let card_w = 330.0_f32.min(full.width() - 32.0);"
CARDW_NEW = "            let card_w = 372.0_f32.min(full.width() - 24.0);"

TRAY_OLD = '''            let portrait = matches!(ws, "capcut" | "blurrr" | "kuaishou" | "jianying");'''
TRAY_NEW = '''            // 打开对话框时不画工具条，免得压住弹窗
            let portrait = matches!(ws, "capcut" | "blurrr" | "kuaishou" | "jianying")
                && self.dialog.is_none();'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("card polish already present")
        return
    for name, old, new in (
        ("card_h", CARD_OLD, CARD_NEW),
        ("thumb", THUMB_OLD, THUMB_NEW),
        ("name", NAME_OLD, NAME_NEW),
        ("desc", DESC_OLD, DESC_NEW),
        ("card_w", CARDW_OLD, CARDW_NEW),
        ("tray", TRAY_OLD, TRAY_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    frame.write_text(src, encoding="utf-8")
    print("layout cards: bigger previews, tray hidden behind dialogs")


if __name__ == "__main__":
    main()
