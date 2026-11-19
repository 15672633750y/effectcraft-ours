#!/usr/bin/env python3
"""把旧的四个布局 id 迁移到新的五套品牌布局，避免老用户升级后"当前布局一张卡都不亮"。

classic → ae      （横屏三栏，接近原来的经典）
simple  → capcut  （上预览下时间线）
pro     → ae      （项目|预览|属性 + 时间线）
minimal → blurrr  （大预览）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_LEGACY_V1"

NORM_ANCHOR = "        let ours = Self::OURS_LAYOUT_IDS.contains(&id.as_str());"

NORM_NEW = '''        // EFFECTCRAFT_OURS_LAYOUT_LEGACY_V1 — 旧 id 迁移到新的五套品牌布局
        let id = match id.as_str() {
            "classic" | "pro" => "ae".to_string(),
            "simple" => "capcut".to_string(),
            "minimal" => "blurrr".to_string(),
            other => other.to_string(),
        };
        let ours = Self::OURS_LAYOUT_IDS.contains(&id.as_str());'''

HILITE_OLD = '''                let current = if Self::OURS_LAYOUT_IDS.contains(&self.ui.workspace.as_str()) {
                    self.ui.workspace.clone()
                } else {
                    "classic".to_string()
                };'''

HILITE_NEW = '''                // 旧 id / 未知 id 都按 ae 高亮，避免五张卡全不亮看不出当前布局
                let current = match self.ui.workspace.as_str() {
                    id if Self::OURS_LAYOUT_IDS.contains(&id) => id.to_string(),
                    "simple" => "capcut".to_string(),
                    "minimal" => "blurrr".to_string(),
                    _ => "ae".to_string(),
                };'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(NORM_ANCHOR) != 1:
            raise SystemExit(f"normalize anchor: {src.count(NORM_ANCHOR)}")
        src = src.replace(NORM_ANCHOR, NORM_NEW, 1)
        if src.count(HILITE_OLD) != 1:
            raise SystemExit(f"highlight anchor: {src.count(HILITE_OLD)}")
        src = src.replace(HILITE_OLD, HILITE_NEW, 1)
        frame.write_text(src, encoding="utf-8")
        print("legacy layout ids migrate to the brand layouts")


if __name__ == "__main__":
    main()
