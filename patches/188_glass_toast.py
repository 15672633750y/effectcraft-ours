#!/usr/bin/env python3
"""提示改成底部居中的玻璃胶囊：醒目、有质感、点得穿。

Every message (undo, "select a keyframe first", export results, plug-in errors) goes through
`draw_toast`, so restyling it there restyles them all, including messages added later.

* bottom centre, 96 px above the bottom edge — clear of the viewer's control bar
* a light frosted capsule: translucent white over a darker layer, a bright hairline, an inner
  highlight and soft layered shadows. No backdrop blur (egui cannot blur what is behind), but the
  layering reads as glass
* 15.5 pt dark text, wrapped at 82 % of the window width, so long messages take two lines
* **it takes no input**: no `interact`, so a tap goes through to the layers and buttons underneath;
  it disappears on its own timer
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GLASS_TOAST_V1"

OLD = '''            let galley = ui.painter().layout_no_wrap(m.clone(), Tokens::ui(12.0), t.text);
            let r = egui::Rect::from_min_size(egui::pos2(full.min.x + 16.0, full.max.y - 44.0 - lift), galley.size() + egui::vec2(24.0, 14.0));
            ui.painter().rect_filled(r, 6.0, t.panel_bg);
            ui.painter().rect_stroke(r, 6.0, egui::Stroke::new(1.0, t.field_border), egui::StrokeKind::Inside);
            ui.painter().galley(r.min + egui::vec2(12.0, 7.0), galley, t.text);
            self.auto.add("toast", r, &m);
            let resp = ui.interact(r, egui::Id::unique("toast"), egui::Sense::click());
            if resp.clicked() {
                self.ui.status.clear();
                self.toast = None;
            }
'''

NEW = '''            // EFFECTCRAFT_OURS_GLASS_TOAST_V1 — 底部居中的玻璃胶囊：只显示，不接收点击
            let wrap = (full.width() * 0.82).max(220.0);
            let galley = ui.painter().layout(m.clone(), Tokens::ui(15.5), egui::Color32::from_rgb(24, 24, 26), wrap);
            let pad = egui::vec2(20.0, 13.0);
            let size = galley.size() + pad * 2.0;
            let r = egui::Rect::from_center_size(
                egui::pos2(full.center().x, full.max.y - 96.0 - lift),
                size,
            );
            let p = ui.painter();
            // 影子：三层渐淡，浮起来
            for (grow, a) in [(7.0, 16.0), (4.0, 22.0), (2.0, 30.0)] {
                p.rect_filled(r.expand(grow), 22.0, egui::Color32::from_black_alpha(a as u8));
            }
            // 玻璃底：浅色磨砂（白 30% 压在深色 12% 上）
            p.rect_filled(r, 20.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 96));
            p.rect_filled(r, 20.0, egui::Color32::from_rgba_unmultiplied(246, 247, 250, 96));
            // 顶部内高光 + 亮边
            let hi = egui::Rect::from_min_max(r.min, egui::pos2(r.max.x, r.min.y + r.height() * 0.45));
            p.rect_filled(hi, 20.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 18));
            p.rect_stroke(r, 20.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 120)), egui::StrokeKind::Inside);
            p.galley(r.min + pad, galley, egui::Color32::from_rgb(246, 247, 250));
            self.auto.add("toast", r, &m);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("glass toast already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"toast anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("toast is a glass capsule that lets clicks through")


if __name__ == "__main__":
    main()
