#!/usr/bin/env python3
"""模态对话框的遮罩调淡（120 → 45），别把后面的界面压成另一种颜色。

用户实测（2026-11-18）：打开「恢复工程」时，顶栏头像发蓝、工具栏控件颜色也不对。
不是头像坏了，是 `egui::Modal` 背后那层 `Color32::from_black_alpha(120)`：深黑压在浅色
头像上就是暗蓝灰，压在所有控件上就整体偏移。

对话框自己的 frame 是**不透明**的 `t.panel_bg`（`modal_fit_placed` 里 `.fill(t.panel_bg)`），
所以遮罩降到 45 也不会让对话框糊在背景里；输入拦截由 Modal 自己的层负责，与遮罩无关。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MODAL_DIM_V1"

OLD = ".backdrop_color(Color32::from_black_alpha(if place.dim { 120 } else { 0 }))"
NEW = ".backdrop_color(Color32::from_black_alpha(if place.dim { 45 } else { 0 }))"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/dialogs.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("modal dim already softened")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"backdrop anchor: {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    # 记个标记，避免以后重复改
    src = src.replace(
        "fn modal_fit_placed(",
        f"// {MARKER} — 对话框遮罩用 45 而不是 120：120 会把背后的头像/控件压偏色。\nfn modal_fit_placed(",
        1,
    )
    path.write_text(src, encoding="utf-8")
    print("modal backdrop 120 -> 45")


if __name__ == "__main__":
    main()
