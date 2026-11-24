#!/usr/bin/env python3
"""自动保存更适合手机：默认 20 分钟太久，且切后台不存。

两个改动：
1. **间隔封顶**：安卓上自动保存间隔最多 2 分钟（用户设得更小就按更小的来）。
   原来是 20 分钟——闪退一次就能丢 20 分钟的活。
2. **失焦即存**：应用被切到后台/失去焦点时立刻 `file.autoSave` 一次。
   安卓上进程经常在后台被直接杀掉，这是"来不及保存"的主要场景。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MOBILE_AUTOSAVE_V1"

INTERVAL_OLD = '''        let interval = a.interval_minutes.max(1) as f64 * 60.0;'''
INTERVAL_NEW = '''        // EFFECTCRAFT_OURS_MOBILE_AUTOSAVE_V1 — 手机上 20 分钟太长：最多 2 分钟存一次
        let interval = if cfg!(target_os = "android") {
            a.interval_minutes.clamp(1, 2) as f64 * 60.0
        } else {
            a.interval_minutes.max(1) as f64 * 60.0
        };'''

FOCUS_ANCHOR = '''        // EFFECTCRAFT_OURS_BRAND_PALETTE_V2 — 每套布局用**拆包得到的真实配色**，不再从我们自己的主题派生。'''

FOCUS_INSERT = '''        // EFFECTCRAFT_OURS_MOBILE_AUTOSAVE_V1 — 切后台/失焦立刻自动保存一次，防后台被杀丢活
        {
            let focused = ui.ctx().input(|i| i.focused);
            let id = egui::Id::new("ours-autosave-focus");
            let was = ui.ctx().data(|d| d.get_temp::<bool>(id));
            ui.ctx().data_mut(|d| d.insert_temp(id, focused));
            if was == Some(true) && !focused {
                let _ = crate::menus::invoke(self, ui.ctx(), "file.autoSave", serde_json::json!({}));
            }
        }
        // EFFECTCRAFT_OURS_BRAND_PALETTE_V2 — 每套布局用**拆包得到的真实配色**，不再从我们自己的主题派生。'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    sess = root / "crates/engine/src/settings/session_settings.rs"
    src = sess.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(INTERVAL_OLD) != 1:
            raise SystemExit(f"interval anchor: {src.count(INTERVAL_OLD)}")
        sess.write_text(src.replace(INTERVAL_OLD, INTERVAL_NEW, 1), encoding="utf-8")
        print("autosave interval capped at 2 min on android")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("focus autosave already present")
        return
    if src.count(FOCUS_ANCHOR) != 1:
        raise SystemExit(f"frame anchor: {src.count(FOCUS_ANCHOR)}")
    frame.write_text(src.replace(FOCUS_ANCHOR, FOCUS_INSERT, 1), encoding="utf-8")
    print("auto-save on focus loss")


if __name__ == "__main__":
    main()
