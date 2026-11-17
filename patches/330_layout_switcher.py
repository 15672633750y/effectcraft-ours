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
BODY_OLD = "        self.dock_area(ui, body);\n"
BODY_NEW = "        ui.data_mut(|d| d.insert_temp(egui::Id::new(\"ours-dock-body\"), body));\n        self.dock_area(ui, body);\n"

SIG = (
    "    /// The status message or the latest toast, bottom left (`lift` points higher while the\n"
    "    /// Importing card is there).\n"
)

METHOD = r'''    // EFFECTCRAFT_OURS_LAYOUT_SWITCHER_V1 — 画布右上角的「布局」与四套布局切换面板
    // EFFECTCRAFT_OURS_LAYOUT_PREVIEW_V1 — 用真实布局树画卡片里的缩略预览
    fn ours_layout_mini(p: &egui::Painter, r: egui::Rect, node: &crate::dock::Node<crate::dock::PanelKind>, tint: egui::Color32, base: egui::Color32) {
        use crate::dock::PanelKind::*;
        let gap = 2.0;
        match node {
            crate::dock::Node::Tabs { panels, active } => {
                let Some(kind) = panels.get(*active).or_else(|| panels.first()) else { return };
                p.rect_filled(r, 2.0, base);
                match kind {
                    Composition | Layer | Preview => {
                        p.rect_stroke(r.shrink(1.0), 2.0, egui::Stroke::new(1.0, tint), egui::StrokeKind::Inside);
                        let inner = r.shrink(r.width().min(r.height()) * 0.18);
                        p.rect_filled(inner, 1.0, egui::Color32::from_black_alpha(210));
                        let c = inner.center();
                        let s = inner.width().min(inner.height()) * 0.20;
                        p.add(egui::Shape::convex_polygon(
                            vec![c + egui::vec2(-s * 0.7, -s), c + egui::vec2(-s * 0.7, s), c + egui::vec2(s, 0.0)],
                            tint,
                            egui::Stroke::NONE,
                        ));
                    }
                    Timeline | RenderQueue => {
                        for i in 0..6 {
                            let x = r.min.x + 3.0 + (r.width() - 6.0) * (i as f32 / 5.0);
                            p.line_segment([egui::pos2(x, r.min.y + 2.0), egui::pos2(x, r.max.y - 2.0)], egui::Stroke::new(1.0, tint.gamma_multiply(0.25)));
                        }
                        let bar = egui::Rect::from_min_size(egui::pos2(r.min.x + 3.0, r.min.y + r.height() * 0.42), egui::vec2(r.width() - 6.0, r.height() * 0.34));
                        p.rect_filled(bar, 1.0, tint.gamma_multiply(0.65));
                    }
                    _ => {
                        for i in 0..3 {
                            let y = r.min.y + 4.0 + i as f32 * (r.height() - 8.0) / 3.0;
                            let w = (r.width() - 8.0) * (0.82 - 0.14 * i as f32);
                            p.rect_filled(egui::Rect::from_min_size(egui::pos2(r.min.x + 4.0, y), egui::vec2(w, 2.0)), 1.0, tint.gamma_multiply(0.45));
                        }
                    }
                }
            }
            crate::dock::Node::Split { axis, size, first, second } => {
                let frac = match size {
                    crate::dock::SplitSize::Ratio(f) => (*f).clamp(0.15, 0.85),
                    crate::dock::SplitSize::FixedFirst(n) => (n / (n + 420.0)).clamp(0.2, 0.6),
                    _ => 0.5,
                };
                match axis {
                    crate::dock::SplitAxis::Horizontal => {
                        let w = (r.width() - gap) * frac;
                        Self::ours_layout_mini(p, egui::Rect::from_min_size(r.min, egui::vec2(w, r.height())), first, tint, base);
                        Self::ours_layout_mini(p, egui::Rect::from_min_size(egui::pos2(r.min.x + w + gap, r.min.y), egui::vec2(r.width() - w - gap, r.height())), second, tint, base);
                    }
                    _ => {
                        let h = (r.height() - gap) * frac;
                        Self::ours_layout_mini(p, egui::Rect::from_min_size(r.min, egui::vec2(r.width(), h)), first, tint, base);
                        Self::ours_layout_mini(p, egui::Rect::from_min_size(egui::pos2(r.min.x, r.min.y + h + gap), egui::vec2(r.width(), r.height() - h - gap)), second, tint, base);
                    }
                }
            }
            _ => {}
        }
    }

    // EFFECTCRAFT_OURS_CANVAS_LAYOUT_ENTRY_V2 — 画布内部右上角的「布局」按钮。
    // 与工具栏的「曲线 / 插件」同款：44×26、4px 圆角、switch_well 底、12pt 字。
    // 展开后先发光 120ms 再淡出 220ms，然后完全不画；展开期间不接受点击
    // （所以打开它的那一次点击不可能再被它抢走）。
    fn ours_layout_entry(&mut self, ui: &mut egui::Ui, area: egui::Rect) {
        use egui::{Align2, Color32, Id, Rect, Sense, Stroke, StrokeKind, Vec2};
        if area.width() < 90.0 || area.height() < 52.0 {
            return;
        }
        let t = self.tokens;
        let now = self.now;
        let open_id = Id::new("layout-open-at");
        let open_at: Option<f64> = ui.data(|d| d.get_temp(open_id));
        let (fade, glow) = match open_at {
            None => (1.0_f32, false),
            Some(at) => {
                let e = (now - at) as f32;
                if e >= 0.34 {
                    return;
                }
                ui.ctx().request_repaint();
                let fade = if e < 0.12 { 1.0 } else { (1.0 - (e - 0.12) / 0.22).clamp(0.0, 1.0) };
                (fade, e < 0.12)
            }
        };
        let r = Rect::from_min_size(egui::pos2(area.max.x - 8.0 - 44.0, area.min.y + 8.0), Vec2::new(44.0, 26.0));
        // 手机上 44×26 偏小：视觉不变，热区外扩 4px（52×34），更好点中。
        let resp = ui.interact(r.expand(4.0), Id::unique("layout-entry-canvas"), Sense::click());
        let p = ui.painter().with_clip_rect(area);
        let base = if resp.hovered() { t.hover } else { t.switch_well };
        p.rect_filled(r, 4.0, Color32::from_rgba_unmultiplied(base.r(), base.g(), base.b(), (255.0 * fade) as u8));
        if glow {
            p.rect_stroke(r.expand(1.5), 5.0, Stroke::new(1.5, t.accent.gamma_multiply(0.80)), StrokeKind::Outside);
            p.rect_stroke(r.expand(3.0), 6.0, Stroke::new(1.0, t.accent.gamma_multiply(0.38)), StrokeKind::Outside);
        }
        p.text(r.center(), Align2::CENTER_CENTER, "布局", Tokens::ui(12.0), Color32::from_rgba_unmultiplied(t.text.r(), t.text.g(), t.text.b(), (255.0 * fade) as u8));
        self.auto.add("layout.switcher", r, "布局");
        if open_at.is_none() && resp.clicked() {
            ui.data_mut(|d| d.insert_temp(open_id, now));
            ui.data_mut(|d| d.insert_temp(Id::new("layout-last-activity"), now));
            ui.ctx().request_repaint();
        }
    }

    fn draw_layout_switcher(&mut self, ui: &mut egui::Ui, full: egui::Rect) {
        use egui::{Color32, Key, Pos2, Rect, Sense, Stroke, StrokeKind, Vec2};
        let t = self.tokens;
        let now = self.now;
        // 入口：刚被点开的那一帧只画发光就返回，遮罩和卡片下一帧再来——
        // “打开它的那一次点击”因此永远不会被同一帧的遮罩判成点空白。
        let was_open = ui.data(|d| d.get_temp::<f64>(egui::Id::new("layout-open-at")));
        if was_open.is_none() {
            let area = ui
                .data(|d| d.get_temp::<egui::Rect>(egui::Id::new("ours-canvas-rect")))
                .or_else(|| ui.data(|d| d.get_temp::<egui::Rect>(egui::Id::new("ours-dock-body"))))
                .unwrap_or(full);
            self.ours_layout_entry(ui, area);
            if ui.data(|d| d.get_temp::<f64>(egui::Id::new("layout-open-at"))).is_some() {
                return;
            }
        }
        let open_id = egui::Id::new("layout-open-at");
        let chosen_id = egui::Id::new("layout-chosen");
        // EFFECTCRAFT_OURS_LAYOUT_ROBUST_V1 — 每次会话第一次画「布局」时归一化一次：
        // 存的布局 id 缺失/未知/损坏 → 回落经典，绝不让界面停在空的布局上。
        let once = egui::Id::new("ours-layout-normalized");
        if ui.data(|d| d.get_temp::<bool>(once)).is_none() {
            ui.data_mut(|d| d.insert_temp(once, true));
            self.ours_normalize_layout();
        }
        let open_at: Option<f64> = ui.data(|d| d.get_temp(open_id));
        let chosen: Option<(f64, String)> = ui.data(|d| d.get_temp(chosen_id));
        // 布局目录：ours = dock 里的内置工作区名，used only when a card is clicked.
        // EFFECTCRAFT_OURS_LAYOUT_REAL_V1 — 名字是我们自己的布局 id，切换时直接换 dock 布局树，
        // 不走 set_workspace（移动端没有这些工作区，换了也不重排）
        let entries: [(&str, &str, &str, usize); 4] = [
            ("classic", "经典", "项目 | 合成 | 时间轴", 0),
            ("simple", "简易", "上预览、下时间轴", 1),
            ("pro", "专业", "左项目、右预览、下时间轴", 2),
            ("minimal", "极简", "只有合成预览", 3),
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
            if e < 1.05 {
                ui.ctx().request_repaint();
                let fade = if e < 0.16 { e / 0.16 } else { (1.0 - (e - 0.16) / 0.86).clamp(0.0, 1.0) };
                // EFFECTCRAFT_OURS_LAYOUT_SWEEP_V2 — 点击后**整个界面**扫一遍：一条竖直的强调色光带
                // 从左扫到右（不再是沿边框跑的小点）。
                let sweep = (e / 0.85).clamp(0.0, 1.0);
                let band = full.width() * 0.22;
                let sx = full.min.x - band + (full.width() + band) * sweep;
                for (k, a) in [(1.0f32, 0.10f32), (0.55, 0.18), (0.22, 0.34)] {
                    let hw = band * k * 0.5;
                    let g = Rect::from_min_max(Pos2::new(sx - hw, full.min.y), Pos2::new(sx + hw, full.max.y));
                    ui.painter().rect_filled(g, 0.0, t.accent.gamma_multiply(a * fade));
                }
                // 布局名：主题色、字号放大、加字距 + 三层辉光 + 下划线（赛博感）
                let font = Tokens::semibold(46.0);
                let chars: Vec<char> = name.chars().collect();
                let spacing = 10.0_f32;
                let mut glyphs: Vec<(char, std::sync::Arc<egui::Galley>)> = Vec::new();
                let mut total = 0.0_f32;
                for ch in &chars {
                    let g = ui.painter().layout_no_wrap(ch.to_string(), font.clone(), t.accent);
                    total += g.size().x + spacing;
                    glyphs.push((*ch, g));
                }
                total -= spacing;
                let cy = full.center().y;
                let mut x = full.center().x - total / 2.0;
                for (_, g) in &glyphs {
                    let y = cy - g.size().y / 2.0;
                    for (spread, alpha) in [(3.0f32, 0.16f32), (1.5, 0.30)] {
                        ui.painter().galley(Pos2::new(x + spread, y), g.clone(), t.accent.gamma_multiply(alpha * fade));
                        ui.painter().galley(Pos2::new(x - spread, y), g.clone(), t.accent.gamma_multiply(alpha * fade));
                    }
                    ui.painter().galley(Pos2::new(x, y), g.clone(), t.accent.gamma_multiply(fade));
                    x += g.size().x + spacing;
                }
                // 下划线：两端各一段强调色短线，中间一条淡线
                let under = Pos2::new(full.center().x - total / 2.0, cy + 46.0);
                let line_w = total;
                ui.painter().line_segment([under, Pos2::new(under.x + line_w, under.y)], Stroke::new(1.0, t.accent.gamma_multiply(0.45 * fade)));
                for (x0, w) in [(under.x, 26.0f32), (under.x + line_w - 26.0, 26.0)] {
                    ui.painter().line_segment([Pos2::new(x0, under.y), Pos2::new(x0 + w, under.y)], Stroke::new(2.0, t.accent.gamma_multiply(fade)));
                }
            } else {
                ui.data_mut(|d| d.remove::<(f64, String)>(chosen_id));
            }
        }

        // —— 展开状态 ——
        if let Some(at) = open_at {
            // 8 秒没有任何操作才自动收起（有操作就一直留着），避免任何情况下卡住
            let idle_id = egui::Id::new("layout-last-activity");
            if ui.input(|i| i.pointer.any_down() || i.pointer.delta() != egui::Vec2::ZERO) {
                ui.data_mut(|d| d.insert_temp(idle_id, now));
            }
            let last_activity: f64 = ui.data(|d| d.get_temp(idle_id)).unwrap_or(at);
            if now - last_activity > 8.0 {
                ui.data_mut(|d| d.remove::<f64>(open_id));
                return;
            }
            ui.ctx().request_repaint();
            let e = (now - at) as f32;
            let dim = (e / 0.2).clamp(0.0, 1.0);
            ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha((196.0 * dim) as u8));

            // HUD 四角短线（保留）
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
            let card_w = 330.0_f32.min(full.width() - 32.0);
            let card_h = 92.0;
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
                // 当前布局：三圈强调色描边（跟快捷键面板的多选发光一致）。
                // 从旧版本升上来时 workspace 还是 Default/未知：一律当作「经典」，别让四张卡
                // 全都不高亮、让用户看不出现在用的是哪套。
                let current = if Self::OURS_LAYOUT_IDS.contains(&self.ui.workspace.as_str()) {
                    self.ui.workspace.clone()
                } else {
                    "classic".to_string()
                };
                if current == workspace {
                    let base = r.expand(1.5);
                    ui.painter().rect_stroke(base, 12.0, Stroke::new(1.5, t.accent.gamma_multiply(0.86 * ease)), StrokeKind::Outside);
                    ui.painter().rect_stroke(base.expand(1.5), 12.0, Stroke::new(1.2, t.accent.gamma_multiply(0.47 * ease)), StrokeKind::Outside);
                    ui.painter().rect_stroke(base.expand(3.0), 12.0, Stroke::new(1.0, t.accent.gamma_multiply(0.24 * ease)), StrokeKind::Outside);
                }
                // 缩略图：真实布局预览（直接按 dock 布局树画，比例就是真实比例）
                let th = Rect::from_min_size(Pos2::new(r.min.x + 12.0, r.min.y + 11.0), Vec2::new(104.0, 64.0));
                ui.painter().rect_filled(th, 4.0, Color32::from_rgba_unmultiplied(10, 12, 16, alpha));
                let tint = Color32::from_rgba_unmultiplied(150, 205, 235, (alpha as f32 * 0.9) as u8);
                let base = Color32::from_rgba_unmultiplied(40, 46, 56, alpha);
                if let Some(root) = crate::dock::ours_layout(workspace).root.as_ref() {
                    Self::ours_layout_mini(ui.painter(), th, root, tint, base);
                }
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
            // 取消：Esc 或点空白处（点卡片之外）。
            // 三重保护，确保打开它的那一次点击绝不会立刻把它关掉：
            //   1) 打开后 250ms 内不认“点空白”；
            //   2) 这次点按的按下时刻必须晚于打开时刻（layout-last-press）；
            //   3) 指针还在卡片上时不算。
            let settling = (now - at) < 0.25;
            let press_id = egui::Id::new("layout-last-press");
            if ui.input(|i| i.pointer.any_pressed()) {
                ui.data_mut(|d| d.insert_temp(press_id, now));
            }
            let press_at: f64 = ui.data(|d| d.get_temp(press_id)).unwrap_or(0.0);
            let fresh_press = press_at > at + 0.10;
            let esc = ui.input(|i| i.key_pressed(Key::Escape));
            let bg_click = ui.input(|i| i.pointer.primary_clicked())
                && ui.input(|i| i.pointer.interact_pos()).is_some_and(|p| {
                    let inside = full.center().x - card_w / 2.0 - 12.0 <= p.x
                        && p.x <= full.center().x + card_w / 2.0 + 12.0
                        && y0 - 12.0 <= p.y
                        && p.y <= y0 + total + 12.0;
                    !inside
                });
            if esc || (bg_click && !hovered_any && fresh_press && !settling) {
                ui.data_mut(|d| d.remove::<f64>(open_id));
                return;
            }
            if let Some((workspace, name)) = clicked {
                // 直接换 dock 布局树（带 panic 捕获）：失败就保持当前布局，并写 layout-error.txt
                let applied = self.ours_apply_layout(workspace);
                ui.data_mut(|d| d.remove::<f64>(open_id));
                if applied {
                    ui.data_mut(|d| d.insert_temp(chosen_id, (now, name.to_string())));
                } else {
                    self.ui.status = "布局切换失败，已保持当前布局（详见 DCIM/EffectCraft/layout-error.txt）".into();
                }
            }
            return;
        }

        // 收起状态：入口已经在上面画过了（画布内部右上角 8px）
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
    if src.count(BODY_OLD) != 1:
        raise SystemExit(f"body anchor: {src.count(BODY_OLD)}")
    src = src.replace(BODY_OLD, BODY_NEW, 1)
    if src.count(SIG) != 1:
        raise SystemExit(f"method anchor: {src.count(SIG)}")
    src = src.replace(SIG, METHOD + SIG, 1)
    path.write_text(src, encoding="utf-8")
    print("layout switcher: entry + four cards + switch + centre name")


if __name__ == "__main__":
    main()
