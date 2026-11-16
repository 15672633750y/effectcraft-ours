#!/usr/bin/env python3
"""把原样画到 painter 上的界面文字改成查翻译表（第七批的配套补丁）。

这批控件（panel_kit / anim_tools / fx_widgets / tracker / widgets::text_button / misc::check_row /
paint_panels / dock::placeholder）直接把 `&str` 交给 painter，从不查 `i18n` 表，所以表里就算有中文
也显示英文。这里只翻「画出来的字」，不翻无障碍/自动化标签，英文界面下 tr() 原样返回，行为不变。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_DRAW_ROUTES_V1"

# (相对路径, 原文, 替换后, 期望出现次数)
EDITS: list[tuple[str, str, str, int]] = [
    # panel_kit：复选框 + 暗标签（Lumetri 示波器、素材浏览器、内容识别填充、元数据面板用）
    (
        "crates/ui-egui/src/panels/panel_kit.rs",
        "    ui.painter().text(pos2(r.max.x + 6.0, r.center().y), Align2::LEFT_CENTER, text, Tokens::ui(12.0), t.text);\n",
        "    // EFFECTCRAFT_OURS_ZH_DRAW_ROUTES_V1\n"
        "    ui.painter().text(pos2(r.max.x + 6.0, r.center().y), Align2::LEFT_CENTER, crate::i18n::tr(text), Tokens::ui(12.0), t.text);\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/panel_kit.rs",
        "    ui.painter().text(pos2(at.x, at.y + 9.0), Align2::LEFT_CENTER, text, Tokens::ui(12.0), t.text_dim);\n",
        "    ui.painter().text(pos2(at.x, at.y + 9.0), Align2::LEFT_CENTER, crate::i18n::tr(text), Tokens::ui(12.0), t.text_dim);\n",
        1,
    ),
    # anim_tools：标签 + 复选框（变形/摆动/运动草图/蒙版插值面板用）
    (
        "crates/ui-egui/src/panels/anim_tools.rs",
        "    p.text(pos2(x, y + 9.0), Align2::LEFT_CENTER, s, Tokens::ui(12.0), t.text_dim);\n",
        "    p.text(pos2(x, y + 9.0), Align2::LEFT_CENTER, crate::i18n::tr(s), Tokens::ui(12.0), t.text_dim);\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/anim_tools.rs",
        "    ui.painter().text(pos2(r.max.x + 6.0, r.center().y), Align2::LEFT_CENTER, text, Tokens::ui(12.0), t.text);\n",
        "    ui.painter().text(pos2(r.max.x + 6.0, r.center().y), Align2::LEFT_CENTER, crate::i18n::tr(text), Tokens::ui(12.0), t.text);\n",
        1,
    ),
    # fx_widgets：效果控件里的暗标签
    (
        "crates/ui-egui/src/panels/fx_widgets.rs",
        "    p.text(pos, Align2::LEFT_CENTER, text, Tokens::ui(11.0), t.text_dim);\n",
        "    p.text(pos, Align2::LEFT_CENTER, crate::i18n::tr(text), Tokens::ui(11.0), t.text_dim);\n",
        1,
    ),
    # tracker：标签 + 按钮（自动化/跟踪面板用）
    (
        "crates/ui-egui/src/panels/tracker.rs",
        "    p.text(pos, Align2::LEFT_CENTER, s, Tokens::ui(12.0), t.text_dim);\n",
        "    p.text(pos, Align2::LEFT_CENTER, crate::i18n::tr(s), Tokens::ui(12.0), t.text_dim);\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/tracker.rs",
        "    app.auto.add(id, r, text);\n    if !enabled {\n",
        "    app.auto.add(id, r, text);\n    let text = crate::i18n::tr(text);\n    if !enabled {\n",
        1,
    ),
    # widgets::text_button：按钮上的字（无障碍标签保持英文）
    (
        "crates/ui-egui/src/widgets.rs",
        "    ui.painter().text(rect.center(), Align2::CENTER_CENTER, text, Tokens::medium(12.0), if primary { Color32::WHITE } else { t.text });\n",
        "    ui.painter().text(rect.center(), Align2::CENTER_CENTER, crate::i18n::tr(text), Tokens::medium(12.0), if primary { Color32::WHITE } else { t.text });\n",
        1,
    ),
    # misc::check_row：预览选项复选框右侧的字
    (
        "crates/ui-egui/src/panels/misc.rs",
        "    p.text(pos2(r.max.x + 5.0, at.y), Align2::LEFT_CENTER, text, Tokens::ui(12.0), t.text);\n",
        "    p.text(pos2(r.max.x + 5.0, at.y), Align2::LEFT_CENTER, crate::i18n::tr(text), Tokens::ui(12.0), t.text);\n",
        1,
    ),
    # paint_panels：画笔面板的行标签
    (
        "crates/ui-egui/src/panels/paint_panels.rs",
        "    p.text(pos2(x, y + 9.0), Align2::LEFT_CENTER, label, Tokens::ui(11.5), if enabled { t.text_dim } else { t.text_faint });\n",
        "    p.text(pos2(x, y + 9.0), Align2::LEFT_CENTER, crate::i18n::tr(label), Tokens::ui(11.5), if enabled { t.text_dim } else { t.text_faint });\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/paint_panels.rs",
        "    p.text(pos2(x, y + 10.0), Align2::LEFT_CENTER, label, Tokens::ui(11.5), if enabled { t.text_dim } else { t.text_faint });\n",
        "    p.text(pos2(x, y + 10.0), Align2::LEFT_CENTER, crate::i18n::tr(label), Tokens::ui(11.5), if enabled { t.text_dim } else { t.text_faint });\n",
        1,
    ),
    # dock：未实现面板的占位文字
    (
        "crates/ui-egui/src/dock.rs",
        "    ui.painter().text(rect.center(), Align2::CENTER_CENTER, text, Tokens::ui(12.0), t.text_faint);\n",
        "    ui.painter().text(rect.center(), Align2::CENTER_CENTER, crate::i18n::tr(text), Tokens::ui(12.0), t.text_faint);\n",
        1,
    ),
    # 关键帧速度对话框：「进入速度 / 离开速度」
    (
        "crates/ui-egui/src/panels/key_dialogs.rs",
        "            ui.label(egui::RichText::new(label).font(Tokens::medium(12.5)));\n",
        "            ui.label(egui::RichText::new(crate::i18n::tr(label)).font(Tokens::medium(12.5)));\n",
        1,
    ),
    # 基本图形面板：「字体控制 / 等比缩放」
    (
        "crates/ui-egui/src/panels/essential.rs",
        "                    if ui.button(label).clicked() {\n",
        "                    if ui.button(crate::i18n::tr(label)).clicked() {\n",
        1,
    ),
    # 路径/VR 面板：三个建空对象按钮、查看角度滑块
    (
        "crates/ui-egui/src/panels/path_vr_panels.rs",
        "        let r = ui.add_enabled(ready, egui::Button::new(label).min_size(egui::vec2(170.0, 24.0))).on_hover_text(tip);\n",
        "        let r = ui.add_enabled(ready, egui::Button::new(crate::i18n::tr(label)).min_size(egui::vec2(170.0, 24.0))).on_hover_text(crate::i18n::tr(tip));\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/path_vr_panels.rs",
        "            ui.label(label);\n",
        "            ui.label(crate::i18n::tr(label));\n",
        1,
    ),
    # 摄像机求解：批量建层与摄像机
    (
        "crates/ui-egui/src/panels/camera_tracker_ui.rs",
        "            if ui.add_enabled(many, egui::Button::new(label)).clicked() {\n",
        "            if ui.add_enabled(many, egui::Button::new(crate::i18n::tr(label))).clicked() {\n",
        1,
    ),
    (
        "crates/ui-egui/src/panels/camera_tracker_ui.rs",
        "            if ui.add_enabled(some, egui::Button::new(label)).clicked() {\n",
        "            if ui.add_enabled(some, egui::Button::new(crate::i18n::tr(label))).clicked() {\n",
        1,
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    done = 0
    for rel, old, new, want in EDITS:
        path = root / rel
        src = path.read_text(encoding="utf-8")
        if new in src:
            continue
        got = src.count(old)
        if got != want:
            raise SystemExit(f"{rel}: anchor count {got} != {want}")
        path.write_text(src.replace(old, new, want), encoding="utf-8")
        done += 1
    print(f"draw routes: {done} edits")


if __name__ == "__main__":
    main()
