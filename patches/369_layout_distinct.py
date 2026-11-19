#!/usr/bin/env python3
"""让四套竖屏布局**彼此也不一样**，而不是同一个排法换比例。

- CapCut：预览 / 时间线 / 项目（时间线在中，下面是素材库，没有效果控件）
- Blurrr：预览 / 时间线 / 效果控件（大预览、薄时间线）
- 快影：预览 / 时间线 / 效果控件 + 项目并排（属性最宽）
- 剪映：预览 / 时间线，时间线占大半屏（没有底部那一行）
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_DISTINCT_V1"

CAPCUT_OLD = '''        "capcut" => portrait(0.52, 0.42),'''
CAPCUT_NEW = '''        // CapCut：预览 / 时间线 / 素材库（没有效果控件那一栏）
        "capcut" => Layout {
            root: Some(vsplit(
                Ratio(0.52),
                tabs(&[Composition], 0),
                vsplit(Ratio(0.55), tabs(&[Timeline], 0), tabs(&[Project], 0)),
            )),
            floating: Vec::new(),
        },'''

JY_OLD = '''        "jianying" => portrait(0.46, 0.58),'''
JY_NEW = '''        // 剪映：预览 + 很大的时间线（没有底部那一行）
        "jianying" => Layout {
            root: Some(vsplit(Ratio(0.42), tabs(&[Composition], 0), tabs(&[Timeline], 0))),
            floating: Vec::new(),
        },'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER in src:
        print("distinct portrait layouts already present")
        return
    for name, old, new in (("capcut", CAPCUT_OLD, CAPCUT_NEW), ("jianying", JY_OLD, JY_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    dock.write_text(src, encoding="utf-8")
    print("capcut and jianying now differ in structure, not just ratios")


if __name__ == "__main__":
    main()
