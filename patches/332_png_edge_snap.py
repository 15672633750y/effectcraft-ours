#!/usr/bin/env python3
"""PNG 头像/贴图拖动贴边（HANDOFF 第 9 节）。

拖动图层时，只要图层的包围盒离画布边缘在 24px 内就吸附过去（0 间距）；
X、Y 各自独立判断，所以角上可以同时吸住两条边。吸附时画一条强调色参考线。
松手后把吸附状态写进图层批注（`layer.setComment`）：
`snap:left,top` 这样的形式；不再贴边就把批注清空（只清我们自己写的那种 `snap:` 前缀，
不动用户自己写的批注）。位置本身照旧写 `transform/position`，所以可撤销、可打关键帧。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PNG_EDGE_SNAP_V1"

DRAG_ANCHOR = "                for (lid, p0, ax, ay) in layers {\n"

DRAG_INSERT = r'''                // EFFECTCRAFT_OURS_PNG_EDGE_SNAP_V1 — 拖到画布边缘 24px 内就贴边（角上可同时吸两条边）
                let comp = v.comp;
                if let Some(lid) = layers.first().map(|x| x.0)
                    && let Some(layer) = comp.layer(lid)
                {
                    let feats = effectcraft_engine::viewer::layer_features(ectx, layer);
                    if !feats.is_empty() {
                        let (mut x0, mut y0, mut x1, mut y1) = (f64::MAX, f64::MAX, f64::MIN, f64::MIN);
                        for f in &feats {
                            x0 = x0.min(f[0]);
                            x1 = x1.max(f[0]);
                            y0 = y0.min(f[1]);
                            y1 = y1.max(f[1]);
                        }
                        let (cw, ch) = (comp.width as f64, comp.height as f64);
                        let (bx0, bx1) = (x0 + d[0], x1 + d[0]);
                        let (by0, by1) = (y0 + d[1], y1 + d[1]);
                        let th = 24.0;
                        let mut snap_x: Option<(f64, f64)> = None;
                        let mut snap_y: Option<(f64, f64)> = None;
                        if bx0.abs() <= th {
                            snap_x = Some((-bx0, 0.0));
                        } else if (bx1 - cw).abs() <= th {
                            snap_x = Some((cw - bx1, cw));
                        }
                        if by0.abs() <= th {
                            snap_y = Some((-by0, 0.0));
                        } else if (by1 - ch).abs() <= th {
                            snap_y = Some((ch - by1, ch));
                        }
                        if let Some((dx, gx)) = snap_x {
                            d[0] += dx;
                            painter.line_segment(
                                [map.to_screen([gx, 0.0]), map.to_screen([gx, ch])],
                                Stroke::new(1.0, t.accent.gamma_multiply(0.55)),
                            );
                        }
                        if let Some((dy, gy)) = snap_y {
                            d[1] += dy;
                            painter.line_segment(
                                [map.to_screen([0.0, gy]), map.to_screen([cw, gy])],
                                Stroke::new(1.0, t.accent.gamma_multiply(0.55)),
                            );
                        }
                    }
                }
'''

STOP_ANCHOR = '''                Gesture::Create { tool, start } => {
                    let end = map.to_comp(pos);
'''

STOP_INSERT = r'''                Gesture::Move { layers, .. } => {
                    // EFFECTCRAFT_OURS_PNG_EDGE_SNAP_V1 — 把贴边状态记进图层批注（不动用户自己的批注）
                    if let Some(lid) = layers.first().map(|x| x.0)
                        && let Some(layer) = comp.layer(lid)
                    {
                        let feats = effectcraft_engine::viewer::layer_features(ectx, layer);
                        if !feats.is_empty() {
                            let (mut x0, mut y0, mut x1, mut y1) = (f64::MAX, f64::MAX, f64::MIN, f64::MIN);
                            for f in &feats {
                                x0 = x0.min(f[0]);
                                x1 = x1.max(f[0]);
                                y0 = y0.min(f[1]);
                                y1 = y1.max(f[1]);
                            }
                            let (cw, ch) = (comp.width as f64, comp.height as f64);
                            let flush = 0.5;
                            let mut sides: Vec<&str> = Vec::new();
                            if x0.abs() <= flush {
                                sides.push("left");
                            }
                            if (x1 - cw).abs() <= flush {
                                sides.push("right");
                            }
                            if y0.abs() <= flush {
                                sides.push("top");
                            }
                            if (y1 - ch).abs() <= flush {
                                sides.push("bottom");
                            }
                            let current = layer.comment.as_str();
                            let text = if sides.is_empty() { String::new() } else { format!("snap:{}", sides.join(",")) };
                            if !sides.is_empty() || current.starts_with("snap:") {
                                let _ = app.session.execute("layer.setComment", json!({"layers": [lid.0], "comment": text}));
                            }
                        }
                    }
                }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/viewer.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("png edge snap already present")
        return
    if src.count(DRAG_ANCHOR) != 1:
        raise SystemExit(f"drag anchor: {src.count(DRAG_ANCHOR)}")
    src = src.replace(DRAG_ANCHOR, DRAG_INSERT + DRAG_ANCHOR, 1)
    if src.count(STOP_ANCHOR) != 1:
        raise SystemExit(f"stop anchor: {src.count(STOP_ANCHOR)}")
    src = src.replace(STOP_ANCHOR, STOP_INSERT + STOP_ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("png edge snap: 24px canvas-edge snap + snap: comment marker")


if __name__ == "__main__":
    main()
