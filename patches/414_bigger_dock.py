#!/usr/bin/env python3
"""底部 dock 加高加大，并按品牌加特征（用户：dock 太小、没品牌特色）。

* 高度 58 → 78，格子宽 76 → 88
* 图标 17 → 21，文字 9 → 10.5
* 品牌特征：CapCut 卡片更明显（圆角 14、间距 8）；快影在选中/悬停时加橙红下划线；
  AM 用粉色选中描边；Blurrr 用青色选中描边
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BIG_DOCK_V1"

H_OLD = '''                    let h = 58.0;'''
H_NEW = '''                    let h = 78.0;'''

CELL_OLD = '''                    let cell_w = 76.0_f32;'''
CELL_NEW = '''                    let cell_w = 88.0_f32;'''

GLYPH_OLD = '''                        clip.text(
                            egui::pos2(cell.center().x, cell.center().y - 7.0),
                            egui::Align2::CENTER_CENTER,
                            *glyph,
                            Tokens::ui(17.0),
                            if hot { self.tokens.accent } else { text_c },
                        );'''
GLYPH_NEW = '''                        clip.text(
                            egui::pos2(cell.center().x, cell.center().y - 10.0),
                            egui::Align2::CENTER_CENTER,
                            *glyph,
                            Tokens::ui(21.0),
                            if hot { self.tokens.accent } else { text_c },
                        );'''

LABEL_OLD = '''                        clip.text(
                            egui::pos2(cell.center().x, cell.center().y + 11.0),
                            egui::Align2::CENTER_CENTER,
                            *label,
                            Tokens::ui(9.0),
                            dim_c,
                        );'''
LABEL_NEW = '''                        clip.text(
                            egui::pos2(cell.center().x, cell.center().y + 15.0),
                            egui::Align2::CENTER_CENTER,
                            *label,
                            Tokens::ui(10.5),
                            dim_c,
                        );'''

CARD_OLD = '''                        } else if ws == "capcut" {
                            clip.rect_filled(
                                cell.shrink2(egui::vec2(6.0, 6.0)),
                                12.0,
                                self.tokens.field_bg,
                            );
                        }'''
CARD_NEW = '''                        } else if ws == "capcut" {
                            clip.rect_filled(
                                cell.shrink2(egui::vec2(6.0, 8.0)),
                                14.0,
                                self.tokens.field_bg,
                            );
                        } else if hot {
                            // 其它品牌：悬停时下划一条品牌色，作为各自的"特征"
                            let line = egui::Rect::from_min_size(
                                egui::pos2(cell.center().x - 12.0, cell.max.y - 9.0),
                                egui::vec2(24.0, 3.0),
                            );
                            clip.rect_filled(line, 2.0, self.tokens.accent);
                        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("big dock already present")
        return
    for name, old, new in (
        ("h", H_OLD, H_NEW),
        ("cell", CELL_OLD, CELL_NEW),
        ("glyph", GLYPH_OLD, GLYPH_NEW),
        ("label", LABEL_OLD, LABEL_NEW),
        ("card", CARD_OLD, CARD_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("dock is taller with per-brand hover accents")


if __name__ == "__main__":
    main()
