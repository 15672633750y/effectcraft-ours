#!/usr/bin/env python3
"""布局切换的健壮性（HANDOFF 第 12 节的三条硬要求）。

1. 只负责「摆放」：`dock::ours_layout` 只返回布局树，复用现有面板（已满足）。
2. 读不到设置 → 回落「经典」：`ours_normalize_layout()` 在会话第一帧检查
   `ui.workspace`——是我们四个 id 就按 id 重建，是 dock 自带的命名工作区就保留，
   其它（缺失/未知/损坏/中文旧值）一律回落 classic。
3. 切换失败 → 保持原布局 + 写 `DCIM/EffectCraft/layout-error.txt`；
   4. 异常不冒泡：切换本身包在 `catch_unwind` 里，panic 只记日志。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_ROBUST_FN_V1"

ANCHOR = "    fn draw_toast(&mut self, ui: &mut egui::Ui, full: egui::Rect, lift: f32) {\n"

METHODS = r'''    // EFFECTCRAFT_OURS_LAYOUT_ROBUST_V1 — 「布局」只摆放面板；失败保持原布局，异常不冒泡。
    /// 我们自己的四个布局 id（顺序与切换器里的卡片一致）。
    pub(crate) const OURS_LAYOUT_IDS: [&'static str; 4] = ["classic", "simple", "pro", "minimal"];

    /// 切到布局 `id`：成功返回 true。布局树在 `catch_unwind` 里构建，panic 也算失败。
    /// 失败时**不动**当前布局，只记日志并把原因写到 `DCIM/EffectCraft/layout-error.txt`。
    pub(crate) fn ours_apply_layout(&mut self, id: &str) -> bool {
        let built = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| crate::dock::ours_layout(id)));
        match built {
            Ok(layout) => {
                self.ui.dock = crate::dock::Workspace::new(layout);
                self.ui.workspace = id.to_string();
                self.ui.maximized = None;
                true
            }
            Err(panic) => {
                let detail = panic
                    .downcast_ref::<&str>()
                    .map(|s| (*s).to_string())
                    .or_else(|| panic.downcast_ref::<String>().cloned())
                    .unwrap_or_else(|| "unknown panic".to_string());
                self.ours_layout_error(id, &detail);
                false
            }
        }
    }

    /// 启动归一化：布局 id 缺失/未知/损坏 → 经典；dock 自带的命名工作区保持不动。
    pub(crate) fn ours_normalize_layout(&mut self) {
        let id = self.ui.workspace.clone();
        let ours = Self::OURS_LAYOUT_IDS.contains(&id.as_str());
        let builtin = crate::dock::WORKSPACES.contains(&id.as_str());
        let target = if ours {
            id.clone()
        } else if builtin {
            return;
        } else {
            "classic".to_string()
        };
        if !self.ours_apply_layout(&target) && target != "classic" {
            // 连自己的 id 都建不出来：再退一步，回到经典，保证界面不会空
            let _ = self.ours_apply_layout("classic");
        }
    }

    /// 布局失败的证据：logcat 一行 + 公共目录里的文本，用户能直接发给我们。
    fn ours_layout_error(&self, id: &str, detail: &str) {
        let message = format!("layout {id} failed: {detail}");
        log::error!("{message}");
        let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
        let _ = std::fs::create_dir_all(dir);
        let line = format!("{} {message}\n", self.now);
        let _ = std::fs::OpenOptions::new().create(true).append(true).open(dir.join("layout-error.txt")).and_then(|mut f| {
            use std::io::Write;
            f.write_all(line.as_bytes())
        });
    }

'''

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if "fn ours_apply_layout(" in src:
        print("layout robustness already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, METHODS + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("layout robustness: apply + normalize + error file")


if __name__ == "__main__":
    main()
