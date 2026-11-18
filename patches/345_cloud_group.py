#!/usr/bin/env python3
"""项目面板底部的「云端」入口（点开 341 里的云端工程面板）。

用户要的是「项目面板加云端分组」。`project::show` 是整块自绘（header / 搜索 / 列头 / 行 /
marquee），把分组塞进列表中间风险很大，所以这里在面板**底部**加一条 24px 的入口条：

- 未登录：`☁ 云端工程（登录后可用）`，点了打开登录面板（PANEL=1）
- 已登录：`☁ 云端工程`，点了打开云端列表（PANEL=4）

状态键与 `341_account_ui.py` 共用：`ours-account-token` / `ours-account-panel`，所以两边
不需要互相知道对方的类型。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_GROUP_V1"

ANCHOR = '''    marquee_select(app, &ctx, &lp, list, &empty, &rows);
'''

INSERT = '''    // EFFECTCRAFT_OURS_CLOUD_GROUP_V1 — 项目面板底部的「云端」入口。
    {
        let bar = Rect::from_min_size(
            pos2(rect.min.x + 6.0, (rect.max.y - 24.0).max(rect.min.y + 40.0)),
            vec2((rect.width() - 12.0).max(40.0), 22.0),
        );
        let logged = ui
            .data(|d| d.get_temp::<String>(egui::Id::new("ours-account-token")))
            .is_some_and(|token| !token.is_empty());
        let label = if logged { "☁ 云端工程" } else { "☁ 云端工程（登录后可用）" };
        let resp = ui.interact(bar, egui::Id::unique("ours-cloud-entry"), Sense::click());
        p.rect_filled(bar, 4.0, if resp.hovered() { t.hover } else { t.switch_well });
        p.text(bar.center(), Align2::CENTER_CENTER, label, Tokens::ui(11.5), if logged { t.text } else { t.text_dim });
        app.auto.add("project.cloudGroup", bar, "云端工程");
        if resp.clicked() {
            let panel = if logged { 4_u8 } else { 1 };
            ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-account-panel"), panel));
            ui.ctx().request_repaint();
        }
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/project.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("cloud group already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"project anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT + ANCHOR, 1), encoding="utf-8")
    print("project panel: cloud entry bar at the bottom")


if __name__ == "__main__":
    main()
