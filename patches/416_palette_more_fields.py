#!/usr/bin/env python3
"""配色再补一层字段，减少"骨架还是我们自己的"感觉。

之前只改了 app_bg/panel_bg/text/accent 等，标签栏文字、图标色、画布外围底色（pasteboard）、
时间线刻度文字这些仍是主题默认值。现在一并按品牌推导：
  pasteboard      = 背景与文字各半（浅色布局偏灰白，深色布局近黑）
  tab_text        = text_dim，tab_text_active = text
  icon / icon_active = text_dim / accent
  tl_ruler_text   = text_dim，tl_ruler_tick = separator
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PALETTE_FIELDS_V1"

OLD = '''                    t.cti = accent;
                    t.timecode = accent;
                    t.hot_text = accent;
                    t.keyframe_selected = accent;'''

NEW = '''                    t.cti = accent;
                    t.timecode = accent;
                    t.hot_text = accent;
                    t.keyframe_selected = accent;
                    // EFFECTCRAFT_OURS_PALETTE_FIELDS_V1 — 把"骨架"色也换成品牌推导值
                    t.pasteboard = bg.lerp_to_gamma(text, 0.10);
                    t.tab_text = dim;
                    t.tab_text_active = text;
                    t.icon = dim;
                    t.icon_active = accent;
                    t.tl_ruler_text = dim;
                    t.tl_ruler_tick = sep;
                    t.tl_nav_bar = panel;
                    t.tl_work_area_bar = accent.gamma_multiply(0.55);
                    t.fx_header = panel;
                    t.fx_header_active = accent.gamma_multiply(0.30);
                    t.text_faint = dim.gamma_multiply(0.72);'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("palette fields already extended")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("pasteboard / tabs / icons / ruler follow the brand palette")


if __name__ == "__main__":
    main()
