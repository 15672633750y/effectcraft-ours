#!/usr/bin/env python3
"""修一个性能与恢复问题：在 ae 布局下每帧都在重建一份 Tokens 做比较。

原来的 `None` 分支每帧调用 `Tokens::from_prefs(...)` 只为比较 app_bg，等于每帧多做一份主题计算。
回到 ae 时，只要"当前 tokens 还带着品牌色"或"明暗与用户设置不一致"就够了。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PALETTE_RESTORE_V1"

OLD = '''                None => {
                    if branded
                        || self.tokens.kind.is_light() != self.ui.theme.is_light()
                        || self.tokens.app_bg != Tokens::from_prefs(&self.session.prefs, self.ui.theme).app_bg
                    {
                        Some((self.ui.theme.is_light(), [egui::Color32::TRANSPARENT; 8]))
                    } else {
                        None
                    }
                }'''

NEW = '''                None => {
                    // EFFECTCRAFT_OURS_PALETTE_RESTORE_V1 — 不每帧重建 Tokens 只为了比较
                    if branded || self.tokens.kind.is_light() != self.ui.theme.is_light() {
                        Some((self.ui.theme.is_light(), [egui::Color32::TRANSPARENT; 8]))
                    } else {
                        None
                    }
                }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("palette restore already fixed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("ae layout no longer rebuilds tokens every frame")


if __name__ == "__main__":
    main()
