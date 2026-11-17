#!/usr/bin/env python3
"""布局切换器（第一版）：画布右上角「布局」→ 遮罩 + 四张布局卡 → 点击立即切换 + 中央浮出名字。

按 HANDOFF 第 8 节：
- 入口「布局」两个字，小、低对比、常驻在画布右上角，没有下拉箭头
- 点击：先亮一下（120ms）再淡出，同时压一层暗色遮罩（egui 没有内建模糊，这里用暗遮罩近似）
- 四张卡依次插入（每条 60ms、从左侧 8px 滑入 + 渐显，smoothstep 220ms），
  每张卡：左上自绘缩略示意图（不用任何商标/logo）+ 名称 + 一行小字说明
- 选中态沿用「多选发光」：不填背景，只在卡片外画 3 圈强调色描边（1.5/1.2/1.0px，alpha 220/120/60）
- 点击任意一条：立即切换布局（无确认），中央浮出该布局名字约 900ms，然后整体淡出
- 取消：点空白处或 Esc，250ms 内反向消失；面板超过 8 秒没有任何操作也会自动关掉（绝不卡住）

四套布局直接复用 dock 的内置工作区（不新增 Workspace）：经典 = Default、简易 = Small Screen、
专业 = Standard、极简 = Minimal。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_SWITCHER_V1"

CALL_OLD = "        curves_editor(self, ui, full);\n    }\n"
CALL_NEW = "        curves_editor(self, ui, full);\n        self.draw_layout_switcher(ui, full);\n    }\n"

SIG = (
    "    /// The status message or the latest toast, bottom left (`lift` points higher while the\n"
    "    /// Importing card is there).\n"
)

METHOD = r'''    // EFFECTCRAFT_OURS_LAYOUT_SWITCHER_V1 — 画布右上角的「布局」与四套布局切换面板
    fn draw_layout_switcher(&mut self, ui: &mut egui::Ui, full: egui::Rect) {
        use egui::{Color32, Key, Pos2, Rect, Sense, Stroke, StrokeKind, Vec2};
        let t = self.tokens;
        let now = self.now;
        let open_id = egui::Id::new("layout-open-at");
        let chosen_id = egui::Id::new("layout-chosen");
        let open_at: Option<f64> = ui.data(|d| d.get_temp(open_id));
        let chosen: Option<(f64, String)> = ui.data(|d| d.get_temp(chosen_id));
        // 布局目录：ours = dock 里的内置工作区名，used only when a card is clicked.
        // EFFECTCRAFT_OURS_LAYOUT_REAL_V1 — 名字是我们自己的布局 id，切换时直接换 dock 布局树，
        // 不走 set_workspace（移动端没有这些工作区，换了也不重排）
        let entries: [(&str, &str, &str, usize); 4] = [
            ("classic", "经典", "多面板，功能全开", 0),
            ("simple", "简易", "上预览、下时间线", 1),
            ("pro", "专业", "项目 + 预览 + 时间线", 2),
            ("minimal", "极简", "只剩预览", 3),
        ];
        // 缩略示意图：四块小矩形，纯几何、不含任何 logo
        let diagram = |p: &egui::Painter, r: Rect, kind: usize, col: Color32| {
            let at = |x: f32, y: f32| Pos2::new(r.min.x + (r.width() - 6.0) * x + 3.0, r.min.y + (r.height() - 6.0) * y + 3.0);
            let boxes: &[(f32, f32, f32, f32)] = match kind {
                0 => &[(0.0, 0.0, 0.18, 1.0), (0.18, 0.0, 0.82, 0.62), (0.82, 0.0, 1.0, 0.62), (0.18, 0.62, 0.82, 1.0)],
                1 => &[(0.0, 0.0, 1.0, 0.58), (0.0, 0.64, 1.0, 1.0)],
                2 => &[(0.0, 0.0, 0.2, 0.55), (0.2, 0.0, 0.8, 0.55), (0.8, 0.0, 1.0, 0.55), (0.0, 0.6, 1.0, 1.0)],
                _ => &[(0.0, 0.0, 1.0, 1.0)],
            };
            for (x0, y0, x1, y1) in boxes {
                p.rect_filled(Rect::from_min_max(at(*x0, *y0), at(*x1, *y1)), 2.0, col);
            }
        };

        // —— 切换完成后的中央名字（约 900ms）——
        if let Some((at, name)) = chosen {
            let e = (now - at) as f32;
            if e < 0.95 {
                ui.ctx().request_repaint();
                let fade = if e < 0.18 { e / 0.18 } else { (1.0 - (e - 0.18) / 0.72).clamp(0.0, 1.0) };
                let galley = ui.painter().layout_no_wrap(name.clone(), Tokens::semibold(30.0), Color32::WHITE);
                let r = Rect::from_center_size(full.center(), galley.size() + Vec2::new(28.0, 16.0));
                let a = (fade * 235.0) as u8;
                ui.painter().rect_filled(r.expand(6.0), 12.0, Color32::from_rgba_unmultiplied(10, 12, 18, (a as f32 * 0.72) as u8));
                ui.painter().galley(r.min + Vec2::new(14.0, 8.0), galley, Color32::from_rgba_unmultiplied(255, 255, 255, a));
                // 扫光：一条强调色的细线从左扫到右
                let sx = r.min.x + r.width() * ((e / 0.6).clamp(0.0, 1.0));
                ui.painter().line_segment([Pos2::new(sx, r.min.y), Pos2::new(sx + 26.0, r.max.y)], Stroke::new(2.0, t.accent.gamma_multiply(fade)));
            } else {
                ui.data_mut(|d| d.remove::<(f64, String)>(chosen_id));
            }
        }

        // —— 展开状态 ——
        if let Some(at) = open_at {
            // 8 秒没动作自动收起，避免任何情况下卡住
            if now - at > 8.0 {
                ui.data_mut(|d| d.remove::<f64>(open_id));
                return;
            }
            ui.ctx().request_repaint();
            let e = (now - at) as f32;
            // 「布局」先亮一下再淡出（120ms 亮、180ms 淡）
            let entry_fade = if e < 0.12 { 0.0 } else { (1.0 - (e - 0.12) / 0.18).clamp(0.0, 1.0) };
            let dim = (e / 0.2).clamp(0.0, 1.0);
            ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha((196.0 * dim) as u8));

            // 附加效果：HUD 四角短线 + 沿边框跑的扫描光（1.6s 一圈）
            let accent = t.accent.gamma_multiply(dim * 0.75);
            let tick = 18.0;
            for (corner, dx, dy) in [
                (Pos2::new(full.min.x + 14.0, full.min.y + 14.0), 1.0, 1.0),
                (Pos2::new(full.max.x - 14.0, full.min.y + 14.0), -1.0, 1.0),
                (Pos2::new(full.min.x + 14.0, full.max.y - 14.0), 1.0, -1.0),
                (Pos2::new(full.max.x - 14.0, full.max.y - 14.0), -1.0, -1.0),
            ] {
                ui.painter().line_segment([corner, Pos2::new(corner.x + tick * dx, corner.y)], Stroke::new(1.5, accent));
                ui.painter().line_segment([corner, Pos2::new(corner.x, corner.y + tick * dy)], Stroke::new(1.5, accent));
            }
            let cycle = ((now - at) / 1.6).fract() as f32;
            let per = (full.width() * 2.0 + full.height() * 2.0) as f32;
            let mut dpos = cycle * per;
            let (ew, eh) = (full.width(), full.height());
            let (sx, sy);
            if dpos < ew {
                sx = full.min.x + dpos;
                sy = full.min.y;
            } else {
                dpos -= ew;
                if dpos < eh {
                    sx = full.max.x;
                    sy = full.min.y + dpos;
                } else {
                    dpos -= eh;
                    if dpos < ew {
                        sx = full.max.x - dpos;
                        sy = full.max.y;
                    } else {
                        dpos -= ew;
                        sx = full.min.x;
                        sy = full.max.y - dpos.min(eh);
                    }
                }
            }
            ui.painter().circle_filled(Pos2::new(sx, sy), 3.0, t.accent.gamma_multiply(dim));
            ui.painter().circle_filled(Pos2::new(sx, sy), 9.0, t.accent.gamma_multiply(dim * 0.22));
            let card_w = 330.0_f32.min(full.width() - 32.0);
            let card_h = 86.0;
            let gap = 12.0;
            let total = card_h * entries.len() as f32 + gap * (entries.len() as f32 - 1.0);
            let x0 = full.center().x - card_w / 2.0;
            let y0 = full.center().y - total / 2.0;
            let mut clicked: Option<(&'static str, &'static str)> = None;
            let mut hovered_any = false;
            for (i, entry) in entries.iter().enumerate() {
                let (workspace, name, note, kind) = *entry;
                let ti = (e - i as f32 * 0.06).clamp(0.0, 1.0) / 0.22;
                let ti = ti.clamp(0.0, 1.0);
                let ease = ti * ti * (3.0 - 2.0 * ti);
                let r = Rect::from_min_size(Pos2::new(x0 - 8.0 * (1.0 - ease), y0 + i as f32 * (card_h + gap)), Vec2::new(card_w, card_h));
                let resp = ui.interact(r, egui::Id::new(("layout-card", i)), Sense::click());
                hovered_any |= resp.hovered();
                let alpha = (ease * 240.0) as u8;
                let fill = if resp.hovered() {
                    Color32::from_rgba_unmultiplied(34, 37, 46, alpha)
                } else {
                    Color32::from_rgba_unmultiplied(22, 24, 30, alpha)
                };
                ui.painter().rect_filled(r, 12.0, fill);
                let line = if resp.hovered() { t.accent.gamma_multiply(ease) } else { Color32::from_rgba_unmultiplied(255, 255, 255, (alpha as f32 * 0.22) as u8) };
                ui.painter().rect_stroke(r, 12.0, Stroke::new(1.0, line), StrokeKind::Inside);
                // 当前布局：三圈强调色描边（跟快捷键面板的多选发光一致）
                if self.ui.workspace == workspace {
                    let base = r.expand(1.5);
                    ui.painter().rect_stroke(base, 12.0, Stroke::new(1.5, t.accent.gamma_multiply(0.86 * ease)), StrokeKind::Outside);
                    ui.painter().rect_stroke(base.expand(1.5), 12.0, Stroke::new(1.2, t.accent.gamma_multiply(0.47 * ease)), StrokeKind::Outside);
                    ui.painter().rect_stroke(base.expand(3.0), 12.0, Stroke::new(1.0, t.accent.gamma_multiply(0.24 * ease)), StrokeKind::Outside);
                }
                // 缩略示意图
                let th = Rect::from_min_size(Pos2::new(r.min.x + 12.0, r.min.y + 13.0), Vec2::new(60.0, 60.0));
                ui.painter().rect_filled(th, 6.0, Color32::from_rgba_unmultiplied(12, 14, 18, alpha));
                diagram(ui.painter(), th, kind, Color32::from_rgba_unmultiplied(150, 200, 230, (alpha as f32 * 0.85) as u8));
                // 名称 + 说明
                let np = Pos2::new(th.max.x + 12.0, r.min.y + 20.0);
                let ng = ui.painter().layout_no_wrap(name.to_string(), Tokens::semibold(16.0), Color32::WHITE);
                ui.painter().galley(np, ng, Color32::from_rgba_unmultiplied(255, 255, 255, alpha));
                let dg = ui.painter().layout_no_wrap(note.to_string(), Tokens::ui(11.5), t.text_dim);
                ui.painter().galley(Pos2::new(np.x, np.y + 24.0), dg, Color32::from_rgba_unmultiplied(180, 186, 198, alpha));
                if resp.clicked() {
                    clicked = Some((workspace, name));
                }
            }
            // 取消：Esc 或点空白处（点卡片之外）
            let esc = ui.input(|i| i.key_pressed(Key::Escape));
            let bg_click = ui.input(|i| i.pointer.primary_clicked())
                && ui.input(|i| i.pointer.interact_pos()).is_some_and(|p| {
                    let inside = full.center().x - card_w / 2.0 - 12.0 <= p.x
                        && p.x <= full.center().x + card_w / 2.0 + 12.0
                        && y0 - 12.0 <= p.y
                        && p.y <= y0 + total + 12.0;
                    !inside
                });
            if esc || (bg_click && !hovered_any) {
                ui.data_mut(|d| d.remove::<f64>(open_id));
                return;
            }
            if let Some((workspace, name)) = clicked {
                // 直接换 dock 布局树：面板显隐/比例都来自这棵树，手机上一定重排
                self.ui.dock = crate::dock::Workspace::new(crate::dock::ours_layout(workspace));
                self.ui.workspace = name.to_string();
                self.ui.maximized = None;
                ui.data_mut(|d| {
                    d.remove::<f64>(open_id);
                    d.insert_temp(chosen_id, (now, name.to_string()));
                });
            }
            // 「布局」还在淡出中时，补画一次余影
            if entry_fade > 0.01 {
                let galley = ui.painter().layout_no_wrap("布局".to_string(), Tokens::ui(15.0), t.text_dim);
                let r = Rect::from_min_size(Pos2::new(full.max.x - 10.0 - galley.size().x, full.min.y + 52.0), galley.size());
                ui.painter().galley(r.min, galley, Color32::from_rgba_unmultiplied(200, 205, 215, (entry_fade * 200.0) as u8));
            }
            return;
        }

        // 收起状态：入口由预览区自己画（`panels/viewer.rs` 的 phase_press），这里什么都不画
    }

'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("layout switcher already present")
        return
    if src.count(CALL_OLD) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_OLD)}")
    src = src.replace(CALL_OLD, CALL_NEW, 1)
    if src.count(SIG) != 1:
        raise SystemExit(f"method anchor: {src.count(SIG)}")
    src = src.replace(SIG, METHOD + SIG, 1)
    path.write_text(src, encoding="utf-8")
    print("layout switcher: entry + four cards + switch + centre name")


if __name__ == "__main__":
    main()
