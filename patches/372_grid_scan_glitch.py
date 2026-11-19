#!/usr/bin/env python3
"""把「一束光带扫过」换成**网格逐格扫描 + 乱码方块**过场。

用户反馈：别人家是「一小格一小格扫」，我们是一条大光带从上压下来，"一坨"。
这里换成：
* 26px 网格，扫描线经过的格子逐个点亮（奇偶格交错，像扫描仪）
* 同一时刻混入少量随机方块（乱码感），位置/大小由时间做伪随机
* 只保留极淡的整体提亮，不再有竖直大光带
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GRID_SCAN_V1"

OLD = '''                // EFFECTCRAFT_OURS_LAYOUT_SWEEP_V2 — 点击后**整个界面**扫一遍：一条竖直的强调色光带
                // 从左扫到右（不再是沿边框跑的小点）。
                let sweep = (e / 0.85).clamp(0.0, 1.0);
                let band = full.width() * 0.22;
                let sx = full.min.x - band + (full.width() + band) * sweep;
                for (k, a) in [(1.0f32, 0.10f32), (0.55, 0.18), (0.22, 0.34)] {
                    let hw = band * k * 0.5;
                    let g = Rect::from_min_max(Pos2::new(sx - hw, full.min.y), Pos2::new(sx + hw, full.max.y));
                    ui.painter().rect_filled(g, 0.0, t.accent.gamma_multiply(a * fade));
                }'''

NEW = '''                // EFFECTCRAFT_OURS_GRID_SCAN_V1 — 网格逐格扫描 + 乱码方块（不是一条大光带）
                {
                    let cell = 26.0_f32;
                    let cols = (full.width() / cell).ceil() as i32;
                    let rows = (full.height() / cell).ceil() as i32;
                    let sweep = (e / 0.85).clamp(0.0, 1.0);
                    let sx = full.min.x + full.width() * sweep;
                    let p = ui.painter();
                    for gy in 0..rows {
                        for gx in 0..cols {
                            let cx = full.min.x + (gx as f32 + 0.5) * cell;
                            let d = (cx - sx).abs() / (cell * 2.6);
                            if d >= 1.0 {
                                continue;
                            }
                            // 奇偶交错，像扫描仪的逐格点亮
                            if (gx + gy) % 2 != 0 {
                                continue;
                            }
                            let a = (1.0 - d) * 0.34 * fade;
                            let r = Rect::from_min_size(
                                Pos2::new(cx - cell * 0.32, full.min.y + gy as f32 * cell + 3.0),
                                Vec2::splat(cell * 0.64),
                            );
                            p.rect_filled(r, 2.0, t.accent.gamma_multiply(a));
                        }
                    }
                    // 乱码方块：时间做伪随机，前 0.35s 密集、之后淡出
                    let mut seed = ((e * 240.0) as u64).wrapping_mul(6364136223846793005).wrapping_add(1);
                    let mut next = || {
                        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                        ((seed >> 33) as f32) / ((1u32 << 31) as f32)
                    };
                    let density = (1.0 - e / 0.35).clamp(0.0, 1.0);
                    let n = (28.0 * density) as i32;
                    for _ in 0..n {
                        let x = full.min.x + next() * full.width();
                        let y = full.min.y + next() * full.height();
                        let w = 10.0 + next() * 54.0;
                        let h = 6.0 + next() * 12.0;
                        let a = (0.10 + next() * 0.22) * fade;
                        let r = Rect::from_min_size(Pos2::new(x, y), Vec2::new(w, h));
                        p.rect_filled(r, 1.0, t.accent.gamma_multiply(a));
                    }
                }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("grid scan already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("layout switch now scans cell by cell with glitch blocks")


if __name__ == "__main__":
    main()
