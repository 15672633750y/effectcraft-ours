#!/usr/bin/env python3
"""布局名的「打字机 + 乱码」出现方式：

* 名字逐字出现（每 50ms 一个字），末尾有一个闪烁的光标块
* 同时叠加少量乱码字形（▚ ▞ ▓ ▒ < > / \\ 0 1 #），位置随时间伪随机
* 已有的一层灰底 + 网格扫描保留
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TYPEWRITER_GLITCH_V1"

LOOP_OLD = '''                let mut x = mid.center().x - total / 2.0;
                for (_, g) in &glyphs {
                    let y = cy - g.size().y / 2.0;'''

LOOP_NEW = '''                // EFFECTCRAFT_OURS_TYPEWRITER_GLITCH_V1 — 逐字出现 + 闪烁光标
                let shown = (((e - 0.06).max(0.0) / 0.05) as usize + 1).min(glyphs.len());
                let mut x = mid.center().x - total / 2.0;
                for (idx, (_, g)) in glyphs.iter().enumerate() {
                    if idx >= shown {
                        break;
                    }
                    let y = cy - g.size().y / 2.0;'''

CURSOR_ANCHOR = '''                // 下划线：两端各一段强调色短线，中间一条淡线'''

CURSOR_INSERT = '''                // 打字机光标：最后两个字之间的方块，按 3Hz 闪
                if shown < glyphs.len() || ((e * 6.0) as i32) % 2 == 0 {
                    let cw = ui
                        .painter()
                        .layout_no_wrap("M".to_string(), font.clone(), t.accent)
                        .size()
                        .x
                        * 0.55;
                    let cursor = Rect::from_min_size(
                        Pos2::new(x - spacing, cy - 22.0),
                        Vec2::new(cw, 44.0),
                    );
                    ui.painter()
                        .rect_filled(cursor, 2.0, t.accent.gamma_multiply(0.75 * fade));
                }
                // 乱码字形：前 0.4s 密集出现，随后淡出
                {
                    const GLITCH: [&str; 10] = ["▚", "▞", "▓", "▒", "<>", "/\\\\", "01", "#", "▘▝", "◤◢"];
                    let mut seed = ((e * 300.0) as u64).wrapping_mul(6364136223846793005).wrapping_add(7);
                    let mut next = || {
                        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                        ((seed >> 33) as f32) / ((1u32 << 31) as f32)
                    };
                    let density = (1.0 - e / 0.4).clamp(0.0, 1.0);
                    let n = (14.0 * density) as i32;
                    for i in 0..n {
                        let g = GLITCH[(i as usize) % GLITCH.len()];
                        let gp = ui.painter().layout_no_wrap(
                            g.to_string(),
                            Tokens::semibold(18.0 + next() * 22.0),
                            t.accent,
                        );
                        let px = mid.min.x + next() * mid.width();
                        let py = mid.min.y + next() * mid.height();
                        ui.painter()
                            .galley(Pos2::new(px, py), gp, t.accent.gamma_multiply(0.35 * density));
                    }
                }
''' + CURSOR_ANCHOR

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("typewriter already present")
        return
    if src.count(LOOP_OLD) != 1:
        raise SystemExit(f"loop anchor: {src.count(LOOP_OLD)}")
    src = src.replace(LOOP_OLD, LOOP_NEW, 1)
    if src.count(CURSOR_ANCHOR) != 1:
        raise SystemExit(f"cursor anchor: {src.count(CURSOR_ANCHOR)}")
    src = src.replace(CURSOR_ANCHOR, CURSOR_INSERT, 1)
    frame.write_text(src, encoding="utf-8")
    print("layout name types itself out with glitch glyphs")


if __name__ == "__main__":
    main()
