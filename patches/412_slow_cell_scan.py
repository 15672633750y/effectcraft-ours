#!/usr/bin/env python3
"""扫光改成"小区块逐个慢速点亮"。

用户反馈：现在还是一束带子扫过去，太简单。改成 16px 小方块、斜向波前、2.4 秒走完一遍，
并且只画波前附近的格子（每行 ±4 格），避免上万次绘制。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GRID_SCAN_V2"

OLD = '                // EFFECTCRAFT_OURS_GRID_SCAN_V1 — 网格逐格扫描 + 乱码方块（不是一条大光带）\n                {\n                    let cell = 26.0_f32;\n                    let cols = (full.width() / cell).ceil() as i32;\n                    let rows = (full.height() / cell).ceil() as i32;\n                    let sweep = (e / 0.85).clamp(0.0, 1.0);\n                    let sx = full.min.x + full.width() * sweep;\n                    let p = ui.painter();\n                    for gy in 0..rows {\n                        for gx in 0..cols {\n                            let cx = full.min.x + (gx as f32 + 0.5) * cell;\n                            let d = (cx - sx).abs() / (cell * 2.6);\n                            if d >= 1.0 {\n                                continue;\n                            }\n                            // 奇偶交错，像扫描仪的逐格点亮\n                            if (gx + gy) % 2 != 0 {\n                                continue;\n                            }\n                            let a = (1.0 - d) * 0.34 * fade;\n                            let r = Rect::from_min_size(\n                                Pos2::new(cx - cell * 0.32, full.min.y + gy as f32 * cell + 3.0),\n                                Vec2::splat(cell * 0.64),\n                            );\n                            p.rect_filled(r, 2.0, t.accent.gamma_multiply(a));\n                        }\n                    }\n                    // 乱码方块：时间做伪随机，前 0.35s 密集、之后淡出\n                    let mut seed = ((e * 240.0) as u64).wrapping_mul(6364136223846793005).wrapping_add(1);\n                    let mut next = || {\n                        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);\n                        ((seed >> 33) as f32) / ((1u32 << 31) as f32)\n                    };\n                    let density = (1.0 - e / 0.35).clamp(0.0, 1.0);\n                    let n = (28.0 * density) as i32;\n                    for _ in 0..n {\n                        let x = full.min.x + next() * full.width();\n                        let y = full.min.y + next() * full.height();\n                        let w = 10.0 + next() * 54.0;\n                        let h = 6.0 + next() * 12.0;\n                        let a = (0.10 + next() * 0.22) * fade;\n                        let r = Rect::from_min_size(Pos2::new(x, y), Vec2::new(w, h));\n                        p.rect_filled(r, 1.0, t.accent.gamma_multiply(a));\n                    }\n                }'

NEW = '                // EFFECTCRAFT_OURS_GRID_SCAN_V2 — 小区块逐个慢速点亮（16px 方块，斜向波前推进）\n                {\n                    let cell = 16.0_f32;\n                    let cols = (full.width() / cell).ceil() as i32;\n                    let rows = (full.height() / cell).ceil() as i32;\n                    let p = ui.painter();\n                    // 2.4 秒走完一遍；斜向波前：每列 +0.7，每行 +0.45\n                    let wave = (e / 2.4).clamp(0.0, 1.0) * (cols as f32 * 0.7 + rows as f32 * 0.45);\n                    for gy in 0..rows {\n                        let row_off = gy as f32 * 0.45;\n                        let center = (wave - row_off) / 0.7;\n                        let base = center.round() as i32;\n                        for dgx in -4..=4 {\n                            let gx = base + dgx;\n                            if gx < 0 || gx >= cols {\n                                continue;\n                            }\n                            let d = (wave - (gx as f32 * 0.7 + row_off)).abs();\n                            let a = (1.0 - d / 4.0).clamp(0.0, 1.0) * 0.30 * fade;\n                            if a <= 0.015 {\n                                continue;\n                            }\n                            // 每格缩一点，读起来是"一块一块"而不是连续带\n                            let r = Rect::from_min_size(\n                                Pos2::new(\n                                    full.min.x + gx as f32 * cell + 2.0,\n                                    full.min.y + gy as f32 * cell + 2.0,\n                                ),\n                                Vec2::splat(cell - 4.0),\n                            );\n                            p.rect_filled(r, 3.0, t.accent.gamma_multiply(a));\n                        }\n                    }\n                }\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("slow cell wave already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {{src.count(OLD)}}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("scan light: slow 16px cells on a diagonal wavefront")


if __name__ == "__main__":
    main()
