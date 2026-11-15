#!/usr/bin/env python3
"""提示画在最上层：不会被对话框/窗口盖住，但仍然不接收点击。

It was painted in the frame's own painter, so any window drawn afterwards (the 导入 dialog) covered
it. It now lives in an `Area` on the foreground layer with `interactable(false)`: above every panel
and window, and still click-through.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TOAST_TOPMOST_V1"

START = "            // EFFECTCRAFT_OURS_GLASS_TOAST_V1"
END = '            self.auto.add("toast", r, &m);\n'

NEW = '''            // EFFECTCRAFT_OURS_GLASS_TOAST_V1 + _TOPMOST_V1 — 最上层的玻璃胶囊，不接收点击
            let wrap = (full.width() * 0.82).max(220.0);
            let galley = ui.painter().layout(m.clone(), Tokens::ui(15.5), egui::Color32::from_rgb(246, 247, 250), wrap);
            let pad = egui::vec2(20.0, 13.0);
            let size = galley.size() + pad * 2.0;
            let center = egui::pos2(full.center().x, full.max.y - 96.0 - lift);
            egui::Area::new(egui::Id::new("ours-toast-area"))
                .order(egui::Order::Foreground)
                .interactable(false)
                .fixed_pos(center - size * 0.5)
                .show(ui.ctx(), |ui| {
                    ui.set_min_size(size);
                    let r = egui::Rect::from_min_size(ui.min_rect().min, size);
                    let p = ui.painter();
                    for (grow, a) in [(7.0, 16.0), (4.0, 22.0), (2.0, 30.0)] {
                        p.rect_filled(r.expand(grow), 22.0, egui::Color32::from_black_alpha(a as u8));
                    }
                    p.rect_filled(r, 20.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 96));
                    p.rect_filled(r, 20.0, egui::Color32::from_rgba_unmultiplied(246, 247, 250, 96));
                    let hi = egui::Rect::from_min_max(r.min, egui::pos2(r.max.x, r.min.y + r.height() * 0.45));
                    p.rect_filled(hi, 20.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 18));
                    p.rect_stroke(r, 20.0, egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 120)), egui::StrokeKind::Inside);
                    p.galley(r.min + pad, galley, egui::Color32::from_rgb(246, 247, 250));
                });
            let r = egui::Rect::from_center_size(center, size);
            self.auto.add("toast", r, &m);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("toast already topmost")
        return
    start = src.find(START)
    end = src.find(END, start if start != -1 else 0)
    if start == -1 or end == -1:
        raise SystemExit(f"toast block not found (start={start}, end={end})")
    end += len(END)
    src = src[:start] + NEW + src[end:]
    path.write_text(src, encoding="utf-8")
    print("toast is drawn above windows and stays click-through")


if __name__ == "__main__":
    main()
