#!/usr/bin/env python3
"""Chinese for the render queue table headers, statuses and the queue hint."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_QUEUE_HEADERS_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"
ROWS = '''    // EFFECTCRAFT_OURS_QUEUE_HEADERS_V1
    ("Render", "渲染"),
    ("Comp Name", "合成名称"),
    ("Status", "状态"),
    ("Started", "开始时间"),
    ("Render Time", "渲染耗时"),
    ("User Stopped", "已停止"),
    ("Queued", "排队中"),
    ("Done", "完成"),
    ("Failed", "失败"),
    ("Stopped", "已停止"),
'''
HINTS = [
    ('"Composition ▸ Add to Render Queue (Ctrl/⌘ M) to queue a render"',
     '"合成 ▸ 添加到渲染队列（Ctrl/⌘ M）即可加入渲染"'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    i18n = root / "crates/ui-egui/src/i18n/ui.rs"
    src = i18n.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(ANCHOR) != 1:
            raise SystemExit("catalog anchor missing")
        i18n.write_text(src.replace(ANCHOR, ANCHOR + ROWS, 1), encoding="utf-8")
    queue = root / "crates/ui-egui/src/panels/render_queue.rs"
    qsrc = queue.read_text(encoding="utf-8")
    changed = 0
    for old, new in HINTS:
        if old in qsrc:
            qsrc = qsrc.replace(old, new)
            changed += 1
    queue.write_text(qsrc, encoding="utf-8")
    print(f"queue headers translated, {changed} hints replaced")


if __name__ == "__main__":
    main()
