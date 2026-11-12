#!/usr/bin/env python3
"""Common interface words (Reset, About, Add, Remove…) in Chinese."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_COMMON_WORDS_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"

ROWS = '''    // EFFECTCRAFT_OURS_COMMON_WORDS_V1
    ("Reset", "重置"),
    ("About…", "关于…"),
    ("About", "关于"),
    ("Add", "添加"),
    ("Remove", "移除"),
    ("Duplicate", "复制"),
    ("Delete", "删除"),
    ("Rename", "重命名"),
    ("Enabled", "启用"),
    ("Disabled", "停用"),
    ("Settings", "设置"),
    ("Preferences", "首选项"),
    ("Cancel", "取消"),
    ("OK", "确定"),
    ("Apply", "应用"),
    ("Close", "关闭"),
    ("Save", "保存"),
    ("Open", "打开"),
    ("Import", "导入"),
    ("Export", "导出"),
    ("Play", "播放"),
    ("Stop", "停止"),
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("common words already translated")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"catalog anchor: expected 1, found {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + ROWS, 1), encoding="utf-8")
    print("common interface words are Chinese now")


if __name__ == "__main__":
    main()
