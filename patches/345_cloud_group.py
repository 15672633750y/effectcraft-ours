#!/usr/bin/env python3
"""「云端工程」从项目面板底部挪到顶部菜单栏（「快捷」后面）。

原来插在 `project::show` 的底部条上，结果压住了 8 位/通道 · 齿轮 · 文件夹 · + 那排按钮。
现在改成菜单栏的最后一个纯文字按钮，和「快捷」同一风格（无下拉箭头）：

- 未登录 → 打开登录面板（`ours-account-panel` = 1）
- 已登录 → 打开云端工程面板（= 4）

已登录时**不加**「（登录后可用）」后缀 —— 面板本身会说明。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_MENU_V1"

# 接在 336 的「快捷」按钮之后（336 先应用，它把整块插在了循环末尾）
ANCHOR = '''            // EFFECTCRAFT_OURS_QUICK_MENU_BUTTON_V1 — 菜单栏末尾的「快捷」，和「文件/编辑/…/帮助」同一行同一套按钮样式
            {
                let resp = ui.add(egui::Button::new("快捷"));
                nav.cover(resp.rect);
                app.auto.add("menu.quick", resp.rect, "快捷");
                if resp.clicked() {
                    let id = egui::Id::unique("ours-shortcut-open");
                    let open: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
                    ui.ctx().data_mut(|d| d.insert_temp(id, !open));
                }
            }
'''

INSERT = ANCHOR + '''            // EFFECTCRAFT_OURS_CLOUD_MENU_V1 — 「快捷」后面的「云端工程」：纯文字、无下拉，
            // 和菜单标题同一套按钮样式。未登录开登录面板，已登录开云端工程面板。
            {
                let logged = ui
                    .data(|d| d.get_temp::<String>(egui::Id::new("ours-account-token")))
                    .is_some_and(|token| !token.is_empty());
                let label = crate::i18n::label(app, "", "云端工程");
                let response = ui.add(egui::Button::new(label));
                app.auto.add("menu.cloud", response.rect, "云端工程");
                if response.clicked() {
                    let panel = if logged { 4_u8 } else { 1 };
                    ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-account-panel"), panel));
                    ui.ctx().request_repaint();
                }
            }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/menus/bar.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("cloud menu entry already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"menu bar anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("menu bar: 云端工程 after 快捷; project panel footer untouched")


if __name__ == "__main__":
    main()
