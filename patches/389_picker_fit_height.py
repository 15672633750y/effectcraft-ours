#!/usr/bin/env python3
"""布局选择面板按屏幕高度自适应，小屏不越界。

5 张卡 × 108 + 4×12 间距 ≈ 588px；在矮屏（横屏或小手机）会顶出上下边界。
这里按可用高度压缩卡片高度与间距（最低 72px），保证整组始终在面板内。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PICKER_FIT_V1"

OLD = '''            let card_w = 372.0_f32.min(full.width() - 24.0);
            let card_h = 108.0;
            let gap = 12.0;'''

NEW = '''            let card_w = 372.0_f32.min(full.width() - 24.0);
            // EFFECTCRAFT_OURS_PICKER_FIT_V1 — 小屏/横屏时压缩卡片高度与间距，别顶出上下边界
            let avail_h = (full.height() - 88.0).max(240.0);
            let n_cards = entries.len() as f32;
            let mut gap = 12.0_f32;
            let mut card_h = 108.0_f32;
            let want = card_h * n_cards + gap * (n_cards - 1.0);
            if want > avail_h {
                gap = 8.0;
                card_h = ((avail_h - gap * (n_cards - 1.0)) / n_cards).clamp(72.0, 108.0);
            }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("picker fit already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("layout picker adapts to screen height")


if __name__ == "__main__":
    main()
