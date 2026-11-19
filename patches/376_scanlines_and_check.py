#!/usr/bin/env python3
"""切换过场补两笔，让它更像「重构」而不是「换皮」：

1. 切换后 1 秒内，整屏叠一层**水平扫描线**（每 3px 一条，极淡），像 CRT 刷新。
2. 布局卡片的「当前项」加一个勾号，省得靠三圈描边猜。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SCANLINES_V1"

NAME_ANCHOR = '''                // 布局名：主题色、字号放大、加字距 + 三层辉光 + 下划线（赛博感）'''

SCANLINES = '''                // EFFECTCRAFT_OURS_SCANLINES_V1 — 切换过场：水平扫描线（CRT 刷新感）
                {
                    let p = ui.painter();
                    let mut y = full.min.y;
                    while y < full.max.y {
                        p.line_segment(
                            [Pos2::new(full.min.x, y), Pos2::new(full.max.x, y)],
                            Stroke::new(1.0, t.accent.gamma_multiply(0.045 * fade)),
                        );
                        y += 3.0;
                    }
                }
'''

CHECK_ANCHOR = '''                if current == workspace {
                    let base = r.expand(1.5);'''

CHECK_INSERT = '''                if current == workspace {
                    // 当前项打个勾，别只靠三圈描边
                    ui.painter().text(
                        Pos2::new(r.max.x - 18.0, r.min.y + 22.0),
                        egui::Align2::RIGHT_CENTER,
                        "\\u{2713}",
                        Tokens::semibold(16.0),
                        t.accent.gamma_multiply(ease),
                    );
                    let base = r.expand(1.5);'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("scanlines already present")
        return
    if src.count(NAME_ANCHOR) != 1:
        raise SystemExit(f"name anchor: {src.count(NAME_ANCHOR)}")
    src = src.replace(NAME_ANCHOR, SCANLINES + NAME_ANCHOR, 1)
    if src.count(CHECK_ANCHOR) != 1:
        raise SystemExit(f"check anchor: {src.count(CHECK_ANCHOR)}")
    src = src.replace(CHECK_ANCHOR, CHECK_INSERT, 1)
    frame.write_text(src, encoding="utf-8")
    print("transition scanlines + current-layout check")


if __name__ == "__main__":
    main()
