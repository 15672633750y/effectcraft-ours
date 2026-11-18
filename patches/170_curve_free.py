#!/usr/bin/env python3
"""The curve window gets two freely draggable control points (Motion-style easing graph).

What the old version did: it drew a single arch — a "summit" that could be moved left/right and up and
down, with both ends pinned at zero. Mathematically that shape can only ever be one hill, so no
amount of dragging produces an S-curve, a dip, a slow start that speeds up and slows again, or an
overshoot.

This replaces the shape with a full cubic segment between (0,0) and (1,1) whose two control points
can be dragged anywhere on the graph — including above the top and below the bottom, which is what
an overshoot looks like. Everything else in the window (presets, save/restore, apply-on-release) is
untouched: the values sent to `keys.velocity` are still read off the drawn curve.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CURVE_FREE_V1"

START = "            // Three points: the start, the summit, the end."
END = "            if canvas_resp.drag_stopped() {"

MIDDLE = '''            // EFFECTCRAFT_OURS_CURVE_FREE_V1 — 两个圆点随便拖：S 形、下凹、过冲都做得出来
            // 图上的纵轴比 0–1 更宽，所以曲线可以冲出顶部/底部（过冲、回弹）。
            let ymin = -0.35f32;
            let ymax = 1.35f32;
            let pyv = |v: f32| plot.bottom() - plot.height() * ((v - ymin) / (ymax - ymin)).clamp(0.0, 1.0);
            let mut sampled: Vec<(f32, f32)> = Vec::new();
            let mut curve: Vec<egui::Pos2> = Vec::new();
            for k in 0..=96 {
                let t = k as f32 / 96.0;
                let u = 1.0 - t;
                let x = 3.0 * u * u * t * pts[0] + 3.0 * u * t * t * pts[2] + t * t * t;
                let y = 3.0 * u * u * t * pts[1] + 3.0 * u * t * t * pts[3] + t * t * t;
                sampled.push((x, y));
                curve.push(pos2(px(x), pyv(y)));
            }
            ui.painter().add(egui::Shape::line(curve, egui::Stroke::new(2.4, t.accent)));
            // 两个可拖的圆点：左边管前段，右边管后段。
            let ends = [pos2(px(pts[0]), pyv(pts[1])), pos2(px(pts[2]), pyv(pts[3]))];
            for h in ends.iter() {
                ui.painter().circle_filled(*h, 5.0, t.accent);
                ui.painter().circle_stroke(*h, 5.0, egui::Stroke::new(1.2, t.panel_bg));
            }
            // The nine values the ease command takes, read off the drawn curve.
            let mut ys: [f32; 9] = [0.0; 9];
            for (i, slot) in ys.iter_mut().enumerate() {
                let want = i as f32 / 8.0;
                let mut v = 0.0;
                for pair in sampled.windows(2) {
                    let (a, b) = (pair[0], pair[1]);
                    if b.0 > a.0 && want >= a.0 && want <= b.0 {
                        v = a.1 + (b.1 - a.1) * ((want - a.0) / (b.0 - a.0));
                    }
                }
                *slot = v.clamp(0.0, 1.0);
            }
            let canvas_resp = ui.interact(canvas, egui::Id::unique("ours-curve-drag"), egui::Sense::drag());
            let pick_id = egui::Id::new("ours-curve-picked");
            let mut stopped = false;
            // 拖哪个点在手按下的那一刻决定一次，之后不换，免得线中途跳到另一个点。
            if canvas_resp.drag_started()
                && let Some(pos) = canvas_resp.interact_pointer_pos()
            {
                let which = u8::from(ends[1].distance_sq(pos) < ends[0].distance_sq(pos));
                ctx.data_mut(|d| d.insert_temp(pick_id, which));
            }
            if canvas_resp.dragged()
                && let Some(pos) = canvas_resp.interact_pointer_pos()
            {
                let gx = ((pos.x - plot.left()) / plot.width()).clamp(0.0, 1.0);
                let gy = ymin + (1.0 - ((pos.y - plot.top()) / plot.height()).clamp(0.0, 1.0)) * (ymax - ymin);
                let k = usize::from(ctx.data(|d| d.get_temp::<u8>(pick_id).unwrap_or(0))) * 2;
                pts[k] = gx;
                pts[k + 1] = gy;
            }
'''

LABEL_OLD = '            ui.label("速度曲线（拖山峰：左右=位置，上下=快慢）");'
LABEL_NEW = '            ui.label("速度曲线（拖两个圆点：上面=快，下面=慢）");'

INIT_OLD = 'let mut pts: [f32; 4] = ctx.data(|d| d.get_temp::<[f32; 4]>(pts_id)).unwrap_or([0.5, 1.0, 0.0, 0.0]);'
INIT_NEW = 'let mut pts: [f32; 4] = ctx.data(|d| d.get_temp::<[f32; 4]>(pts_id)).unwrap_or([0.34, 0.34, 0.66, 0.66]);'

RESET_OLD = 'd.insert_temp(pts_id, [0.5, 1.0, 0.0, 0.0]));'
RESET_NEW = 'd.insert_temp(pts_id, [0.34f32, 0.34, 0.66, 0.66]));'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    if not path.is_file():
        candidates = [p for p in (root / "crates/ui-egui/src").rglob("*.rs") if "速度曲线（拖山峰" in p.read_text(encoding="utf-8", errors="ignore")]
        if not candidates:
            raise SystemExit("curve window not found (105_keyframe_buttons must run first)")
        path = candidates[0]
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("free curve already installed")
        return
    start = src.find(START)
    end = src.find(END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f"region not found (start={start}, end={end})")
    src = src[:start] + MIDDLE + src[end:]
    for old, new in ((LABEL_OLD, LABEL_NEW), (INIT_OLD, INIT_NEW), (RESET_OLD, RESET_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("the curve has two freely draggable points")


if __name__ == "__main__":
    main()
