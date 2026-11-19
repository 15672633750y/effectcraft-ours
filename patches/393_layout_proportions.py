#!/usr/bin/env python3
"""按参考截图量出来的分区比例调整四套布局（预览 ≈1/3，时间线 ≈1/3，工具/属性 ≈1/3）。

四张截图的结构其实一致：
  顶部标题栏 → 预览（约三成高）→ 播放/时间码/时间线（约三成）→ 属性或工具区（约三成）
之前我们是预览占 52~60%，所以看起来"全是预览"，和它们不像。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_PROPORTIONS_V1"

REPL = [
    (
        '''        // CapCut：竖屏。预览 52%，下面时间线 + 属性/项目并排。
        // CapCut：预览 / 时间线 / 素材库（没有效果控件那一栏）
        "capcut" => Layout {
            root: Some(vsplit(
                Ratio(0.52),
                tabs(&[Composition], 0),
                vsplit(Ratio(0.55), tabs(&[Timeline], 0), tabs(&[Project], 0)),
            )),
            floating: Vec::new(),
        },''',
        '''        // CapCut（图 1）：预览约 38% / 时间线 / 素材库
        "capcut" => Layout {
            root: Some(vsplit(
                Ratio(0.38),
                tabs(&[Composition], 0),
                vsplit(Ratio(0.52), tabs(&[Timeline], 0), tabs(&[Project], 0)),
            )),
            floating: Vec::new(),
        },''',
    ),
    (
        '''        // Blurrr：竖屏，预览占比更大，时间线更薄。
        "blurrr" => portrait(0.60, 0.34),''',
        '''        // Blurrr（图 2）：预览 40% / 时间线 / 效果控件
        "blurrr" => portrait(0.40, 0.50),''',
    ),
    (
        '''        // 快影：竖屏，属性栏更宽（右侧给参数留位置）。
        "kuaishou" => Layout {
            root: Some(vsplit(
                Ratio(0.50),''',
        '''        // 快影（图 4）：预览 40% / 时间线 / 属性与素材并排
        "kuaishou" => Layout {
            root: Some(vsplit(
                Ratio(0.40),''',
    ),
    (
        '''        // AM：预览 / 时间线 / 工具（参考截图里是"编组和蒙版"那种浅色界面）
        "am" | "jianying" => Layout {
            root: Some(vsplit(
                Ratio(0.44),''',
        '''        // AM（图 3）：预览 36% / 时间线 / 效果列表（深蓝面板）
        "am" | "jianying" => Layout {
            root: Some(vsplit(
                Ratio(0.36),''',
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("proportions already adjusted")
        return
    for old, new in REPL:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {old[:40]!r} -> {src.count(old)}")
        src = src.replace(old, new, 1)
    src = src.replace(
        "        match name {",
        "        // EFFECTCRAFT_OURS_LAYOUT_PROPORTIONS_V1 — 分区比例按参考截图（预览/时间线/工具各约三分之一）\n        match name {",
        1,
    )
    path.write_text(src, encoding="utf-8")
    print("four layouts re-balanced to the reference proportions")


if __name__ == "__main__":
    main()
