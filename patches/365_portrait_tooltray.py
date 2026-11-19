#!/usr/bin/env python3
"""竖屏布局的底部工具条：切换后不只是面板位置变，界面本身也换成"手机剪辑软件"的形态。

只在 capcut / blurrr / kuaishou / jianying 这几套竖屏布局下出现，横屏（ae）不出现。
按钮走的是现有命令，不新增绘制逻辑：
  导入   → 打开导入面板（ours-import-open）
  文字   → layer.new {text:"文字"}
  形状   → layer.newShape {kind:"rect"}
  预设   → 打开预设库（ours-preset-open）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PORTRAIT_TRAY_V1"

ANCHOR = '''        // EFFECTCRAFT_OURS_IMPORT_REPORT_V1 — 导入结果不再一闪而过，留一块可关闭的显示区。'''

TRAY = '''        // EFFECTCRAFT_OURS_PORTRAIT_TRAY_V1 — 竖屏布局专属的底部工具条。
        {
            let ws = self.ui.workspace.as_str();
            let portrait = matches!(ws, "capcut" | "blurrr" | "kuaishou" | "jianying");
            if portrait {
                let screen = ui.ctx().content_rect();
                let h = 58.0;
                let bar = egui::Rect::from_min_size(
                    egui::pos2(screen.min.x + 10.0, screen.max.y - h - 8.0),
                    egui::vec2(screen.width() - 20.0, h),
                );
                let p = ui.painter();
                p.rect_filled(bar, 14.0, egui::Color32::from_rgba_unmultiplied(12, 12, 14, 200));
                p.rect_stroke(
                    bar,
                    14.0,
                    egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(255, 255, 255, 60)),
                    egui::StrokeKind::Inside,
                );
                let items: [(&str, &str); 4] = [
                    ("\\u{ff0b}", "导入"),
                    ("T", "文字"),
                    ("\\u{25c7}", "形状"),
                    ("\\u{2605}", "预设"),
                ];
                let n = items.len() as f32;
                let cw = bar.width() / n;
                for (i, (glyph, label)) in items.iter().enumerate() {
                    let cell = egui::Rect::from_min_size(
                        egui::pos2(bar.min.x + cw * i as f32, bar.min.y),
                        egui::vec2(cw, bar.height()),
                    );
                    let resp = ui.interact(
                        cell,
                        egui::Id::unique(("ours-tray", i as u64)),
                        egui::Sense::click(),
                    );
                    let hot = resp.hovered();
                    if hot {
                        p.rect_filled(cell.shrink(4.0), 10.0, self.tokens.accent.gamma_multiply(0.16));
                    }
                    p.text(
                        egui::pos2(cell.center().x, cell.center().y - 8.0),
                        egui::Align2::CENTER_CENTER,
                        *glyph,
                        Tokens::ui(18.0),
                        if hot { self.tokens.accent } else { self.tokens.text },
                    );
                    p.text(
                        egui::pos2(cell.center().x, cell.center().y + 12.0),
                        egui::Align2::CENTER_CENTER,
                        *label,
                        Tokens::ui(9.5),
                        self.tokens.text_dim,
                    );
                    if resp.clicked() {
                        match i {
                            0 => {
                                ui.ctx().data_mut(|d| {
                                    d.insert_temp(egui::Id::new("ours-import-open"), true)
                                });
                            }
                            1 => {
                                let _ = crate::menus::invoke(
                                    self,
                                    ui.ctx(),
                                    "layer.new",
                                    serde_json::json!({ "text": "文字", "edit": false }),
                                );
                            }
                            2 => {
                                let _ = crate::menus::invoke(
                                    self,
                                    ui.ctx(),
                                    "layer.newShape",
                                    serde_json::json!({ "kind": "rect" }),
                                );
                            }
                            _ => {
                                ui.ctx().data_mut(|d| {
                                    d.insert_temp(egui::Id::new("ours-preset-open"), true)
                                });
                            }
                        }
                    }
                }
            }
        }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("portrait tray already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"tray anchor: {src.count(ANCHOR)}")
    frame.write_text(src.replace(ANCHOR, TRAY + ANCHOR, 1), encoding="utf-8")
    print("portrait layouts get a bottom tool tray")


if __name__ == "__main__":
    main()
