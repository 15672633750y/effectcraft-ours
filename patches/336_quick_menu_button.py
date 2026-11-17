#!/usr/bin/env python3
"""工具栏改版第一版：把「快捷」从工具栏最左边的图片按钮挪到顶部菜单栏。

- 菜单栏最后一个标题是「帮助」，在它后面加一个普通文字按钮「快捷」：
  和前面几个菜单标题**同一个 `egui::Button`、同一条 `egui::MenuBar` 行**，所以字号/高度/左右间距天然一致
- 点击仍走原来的开关：`ours-shortcut-open`（快捷面板的 data 开关），展开/收起行为不变
- 工具栏最左边不再画图片：`204_shortcut_at_brand_slot.py` 已改成空操作（保留文件名，远端残留不影响）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_QUICK_MENU_BUTTON_V1"

ANCHOR = '''                app.auto.add(&format!("menu.{label}"), response.rect, label);
                drawn += 1;
            }
'''

INSERT = '''            // EFFECTCRAFT_OURS_QUICK_MENU_BUTTON_V1 — 菜单栏末尾的「快捷」，和「文件/编辑/…/帮助」同一行同一套按钮样式
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


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/menus/bar.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("quick menu button already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + INSERT, 1), encoding="utf-8")
    print("快捷 button added after 帮助 in the menu bar")


if __name__ == "__main__":
    main()
