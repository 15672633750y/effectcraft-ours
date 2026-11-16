#!/usr/bin/env python3
"""让效果参数名也查 `i18n/ui.rs` 的翻译表（汉化第十一批起的配套补丁）。

`i18n/prop.rs` 的 `name()` 是手写 match：表里没有的参数名原样返回英文。效果控件的参数名、
属性面板的行名、时间轴的属性行都读它，所以剩下的英文主要就卡在这儿。

这里只改兜底的一行：`other => other` 变成查表，于是参数名和界面文字共用同一个
`SIMPLIFIED_CHINESE` 表、同一条插入锚点，后续批次只加中文行，不再动 Rust。

英文界面下 `tr()` 原样返回，行为不变；存储名（表达式/脚本用的）也还是英文，只翻显示。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_PROP_FALLBACK_V1"

OLD = "        other => other,"
NEW = "        // EFFECTCRAFT_OURS_ZH_PROP_FALLBACK_V1 — 表里没有的名字再查 ui 表（参数名共用一张表）\n        other => crate::i18n::tr(other),"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/prop.rs"
    if not path.is_file():
        raise SystemExit("prop.rs is missing: 70_property_names_zh.py must run first")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("prop fallback already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"fallback anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("prop::name falls back to the ui table")


if __name__ == "__main__":
    main()
