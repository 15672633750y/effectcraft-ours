#!/usr/bin/env python3
"""Chinese for the render queue: table headers, statuses and output modules."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RQ_ZH_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"

ROWS = '''    // EFFECTCRAFT_OURS_RQ_ZH_V1
    ("Render", "渲染"),
    ("Comp Name", "合成名称"),
    ("Status", "状态"),
    ("Started", "开始时间"),
    ("Render Time", "渲染耗时"),
    ("Render Settings", "渲染设置"),
    ("Output Module", "输出模块"),
    ("Notifications", "通知"),
    ("Queued", "排队中"),
    ("Rendering", "渲染中"),
    ("Done", "完成"),
    ("Failed", "失败"),
    ("Stopped", "已停止"),
    ("Best Settings", "最佳设置"),
    ("Draft Settings", "草稿设置"),
    ("High Quality", "高质量"),
    ("High Quality with Alpha", "高质量（含透明）"),
    ("Lossless", "无损"),
    ("Lossless with Alpha", "无损（含透明）"),
    ("PNG Sequence", "PNG 序列"),
    ("PNG Sequence with Alpha", "PNG 序列（含透明）"),
    ("TIFF Sequence with Alpha", "TIFF 序列（含透明）"),
    ("JPEG Sequence", "JPEG 序列"),
    ("OpenEXR Sequence with Alpha", "OpenEXR 序列（含透明）"),
    ("Animated GIF", "动图 GIF"),
    ("Alpha Only", "仅透明通道"),
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("render queue strings already translated")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"catalog anchor: expected 1, found {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + ROWS, 1), encoding="utf-8")
    print("render queue table and output modules are Chinese now")


if __name__ == "__main__":
    main()
