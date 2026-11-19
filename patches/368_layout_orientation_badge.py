#!/usr/bin/env python3
"""布局卡片加「横屏 / 竖屏」角标：一眼看出这套布局的朝向，而不是只看文字描述。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_ORIENT_BADGE_V1"

ANCHOR = '''                ui.painter().galley(Pos2::new(np.x, np.y + 26.0), dg, Color32::from_rgba_unmultiplied(180, 186, 198, alpha));'''

INSERT = '''                ui.painter().galley(Pos2::new(np.x, np.y + 26.0), dg, Color32::from_rgba_unmultiplied(180, 186, 198, alpha));
                // EFFECTCRAFT_OURS_LAYOUT_ORIENT_BADGE_V1 — 朝向角标
                {
                    let portrait_layout = matches!(workspace, "capcut" | "blurrr" | "kuaishou" | "jianying");
                    let label = if portrait_layout { "竖屏" } else { "横屏" };
                    let g = ui.painter().layout_no_wrap(label.to_string(), Tokens::ui(10.0), t.accent);
                    let bw = g.size().x + 14.0;
                    let br = Rect::from_min_size(
                        Pos2::new(r.max.x - bw - 10.0, r.min.y + 10.0),
                        Vec2::new(bw, 20.0),
                    );
                    ui.painter().rect_filled(br, 10.0, t.accent.gamma_multiply(0.15 * ease));
                    ui.painter().rect_stroke(
                        br,
                        10.0,
                        Stroke::new(1.0, t.accent.gamma_multiply(0.55 * ease)),
                        StrokeKind::Inside,
                    );
                    ui.painter().galley(
                        Pos2::new(br.center().x - g.size().x / 2.0, br.center().y - g.size().y / 2.0),
                        g,
                        t.accent.gamma_multiply(ease),
                    );
                }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("orientation badge already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    frame.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("layout cards show 横屏/竖屏 badges")


if __name__ == "__main__":
    main()
