#!/usr/bin/env python3
"""先把「快捷」做成工具栏里的真按钮（和 B/N 一模一样的写法），点开一个空面板。

The floating ball kept failing on input; the B/N buttons right next to it use the simplest possible
widget (`ui.interact` + a painted box + text) and work every time. This puts 快捷 in the toolbar the
same way, opening the panel. Floating/edge-snap comes after this is confirmed usable.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_BUTTON_V1"

ANCHOR = '''                app.ui.status = if set == "begin" { "工作区起点已设到当前帧".into() } else { "工作区终点已设到当前帧".into() };
            }
            x += 34.0;
        }
    }
'''
NEW = ANCHOR + '''
    // EFFECTCRAFT_OURS_SHORTCUT_BUTTON_V1 — 「快捷」按钮（与 B/N 同一套写法）
    {
        let r = Rect::from_min_size(pos2(x, cy - 13.0), vec2(44.0, 26.0));
        let resp = ui.interact(r, egui::Id::unique("ours-shortcut"), Sense::click()).on_hover_text("快捷键面板");
        p.rect_filled(r, 5.0, t.switch_well);
        p.text(r.center(), Align2::CENTER_CENTER, "快捷", Tokens::ui(12.0), t.text);
        if resp.clicked() {
            let id = egui::Id::unique("ours-shortcut-open");
            let open: bool = ui.ctx().data(|d| d.get_temp::<bool>(id).unwrap_or(false));
            ui.ctx().data_mut(|d| d.insert_temp(id, !open));
        }
        x += 48.0;
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("shortcut toolbar button already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, NEW, 1), encoding="utf-8")
    print("快捷 button added next to B/N")


if __name__ == "__main__":
    main()
