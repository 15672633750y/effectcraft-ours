#!/usr/bin/env python3
"""曲线窗口补两个姿势：过冲（上拱）与回弹（下凹），和 Motion 的那套摆法一致。

The two poses are stored as control points and applied through `keys.velocity` with speeds read off the
resulting cubic, so their angle and smoothness match what the graph shows.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVE_POSES_V1"

EDITS = [('            let presets: [(&str, &str, u8, usize); 5] = [\n                ("缓入缓出", "keys.easyEase", 0, 1),\n                ("缓入", "keys.easyEaseIn", 1, 1),\n                ("缓出", "keys.easyEaseOut", 2, 1),\n                ("平滑", "keys.smooth", 3, 3),\n                ("定格", "keys.toggleHold", 4, 1),\n            ];', '            let presets: [(&str, &str, u8, usize); 7] = [\n                ("缓入缓出", "keys.easyEase", 0, 1),\n                ("缓入", "keys.easyEaseIn", 1, 1),\n                ("缓出", "keys.easyEaseOut", 2, 1),\n                ("平滑", "keys.smooth", 3, 3),\n                ("定格", "keys.toggleHold", 4, 1),\n                // 这两个是「姿势」：直接改两个控制点，再按曲线算速度\n                ("过冲", "", 5, 1),\n                ("回弹", "", 6, 1),\n            ];'), ('                        } else {\n                            let _ = crate::menus::invoke(app, ctx, cmd, serde_json::json!({}));\n                            kind = k;\n                        }', '                        } else if cmd.is_empty() {\n                            // EFFECTCRAFT_OURS_CURVE_POSES_V1 — 过冲 / 回弹：摆好控制点再按曲线取速度\n                            let pose: [f32; 4] = if k == 5 {\n                                [0.35, 1.35, 0.62, 1.0]\n                            } else {\n                                [0.38, -0.35, 0.65, 1.0]\n                            };\n                            ctx.data_mut(|d| d.insert_temp(pts_id, pose));\n                            let mut ys: [f32; 9] = [0.0; 9];\n                            for (i, slot) in ys.iter_mut().enumerate() {\n                                let want = i as f32 / 8.0;\n                                let mut best = 0.0f32;\n                                let mut bestd = f32::MAX;\n                                for s in 0..=96 {\n                                    let t = s as f32 / 96.0;\n                                    let u = 1.0 - t;\n                                    let x = 3.0 * u * u * t * pose[0] + 3.0 * u * t * t * pose[2] + t * t * t;\n                                    let y = 3.0 * u * u * t * pose[1] + 3.0 * u * t * t * pose[3] + t * t * t;\n                                    let d2 = (x - want).abs();\n                                    if d2 < bestd {\n                                        bestd = d2;\n                                        best = y;\n                                    }\n                                }\n                                *slot = best;\n                            }\n                            let _ = crate::menus::invoke(\n                                app,\n                                ctx,\n                                "keys.velocity",\n                                serde_json::json!({\n                                    "outSpeed": (ys[1] - ys[0]) * 3.0,\n                                    "outInfluence": (0.5 + (ys[4].clamp(0.05, 1.0) - 0.5) * 1.4).clamp(0.02, 1.0),\n                                    "inSpeed": (ys[8] - ys[7]) * 3.0,\n                                    "inInfluence": (0.5 + (ys[4].clamp(0.05, 1.0) - 0.5) * 1.4).clamp(0.02, 1.0),\n                                    "continuous": true,\n                                }),\n                            );\n                            kind = k;\n                        } else {\n                            let _ = crate::menus::invoke(app, ctx, cmd, serde_json::json!({}));\n                            kind = k;\n                        }'), ('            3 => x,                                 // smooth/linear\n            _ => 0.0,                               // hold', '            3 => x,                                 // smooth/linear\n            5 => x + 0.35 * (x * (1.0 - x) * 4.0),   // overshoot\n            6 => x - 0.30 * (x * (1.0 - x) * 4.0),   // undershoot\n            _ => 0.0,                               // hold')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("curve poses already present")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("two extra curve poses added")


if __name__ == "__main__":
    main()
