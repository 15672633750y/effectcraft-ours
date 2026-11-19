#!/usr/bin/env python3
"""布局选择面板本身也做成「重构界面」的样子，而不是一个普通弹层：

* 背景不是纯黑，而是与切换过场同一套 **26px 网格线**（极淡），视觉上连成一体
* 左上角 HUD 标题 `LAYOUT // 布局` + 一条细分隔线
* 底部提示 `Esc 关闭 · 点击卡片切换`
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PICKER_HUD_V1"

ANCHOR = '''            ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha((196.0 * dim) as u8));
'''

INSERT = '''            ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha((196.0 * dim) as u8));
            // EFFECTCRAFT_OURS_PICKER_HUD_V1 — 与过场同一套网格 + HUD 标题
            {
                let p = ui.painter();
                let mut gx = full.min.x;
                while gx < full.max.x {
                    p.line_segment(
                        [Pos2::new(gx, full.min.y), Pos2::new(gx, full.max.y)],
                        Stroke::new(1.0, t.accent.gamma_multiply(0.035 * dim)),
                    );
                    gx += 26.0;
                }
                let mut gy = full.min.y;
                while gy < full.max.y {
                    p.line_segment(
                        [Pos2::new(full.min.x, gy), Pos2::new(full.max.x, gy)],
                        Stroke::new(1.0, t.accent.gamma_multiply(0.035 * dim)),
                    );
                    gy += 26.0;
                }
                let title_g = p.layout_no_wrap(
                    "LAYOUT  //  布局".to_string(),
                    Tokens::semibold(13.0),
                    t.accent,
                );
                p.galley(
                    Pos2::new(full.min.x + 16.0, full.min.y + 14.0),
                    title_g.clone(),
                    t.accent.gamma_multiply(0.9 * dim),
                );
                p.line_segment(
                    [
                        Pos2::new(full.min.x + 16.0, full.min.y + 34.0),
                        Pos2::new(full.min.x + 16.0 + title_g.size().x, full.min.y + 34.0),
                    ],
                    Stroke::new(1.0, t.accent.gamma_multiply(0.5 * dim)),
                );
                let hint = p.layout_no_wrap(
                    "Esc 关闭 · 点击卡片切换".to_string(),
                    Tokens::ui(10.5),
                    t.text_dim,
                );
                p.galley(
                    Pos2::new(
                        full.center().x - hint.size().x / 2.0,
                        full.max.y - 26.0,
                    ),
                    hint,
                    t.text_dim.gamma_multiply(0.9 * dim),
                );
            }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("picker HUD already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    frame.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("picker gets grid backdrop, HUD title and hint")


if __name__ == "__main__":
    main()
