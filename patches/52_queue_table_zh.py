#!/usr/bin/env python3
"""Render queue table: Chinese headers and status text, engine labels left untouched."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_QUEUE_TABLE_V1"

HEADERS_OLD = 'for (x, l) in [(cx_render, "Render"), (cx_num, "#"), (cx_name, "Comp Name"), (cx_status, "Status"), (cx_started, "Started"), (cx_time, "Render Time")] {'
HEADERS_NEW = 'for (x, l) in [(cx_render, "渲染"), (cx_num, "#"), (cx_name, "合成"), (cx_status, "状态"), (cx_started, "开始"), (cx_time, "耗时")] {'

STATUS_OLD = "        None => it.status.label().to_string(),"
STATUS_NEW = """        None => match it.status {
            RenderStatus::Unqueued => "未排队".to_string(),
            RenderStatus::Queued => "排队中".to_string(),
            RenderStatus::NeedsOutput => "缺少输出".to_string(),
            RenderStatus::Rendering => "渲染中".to_string(),
            RenderStatus::Done => "完成".to_string(),
            RenderStatus::UserStopped => "已停止".to_string(),
            RenderStatus::Failed(_) => "失败".to_string(),
        },"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("queue table already translated")
        return
    for old, new in ((HEADERS_OLD, HEADERS_NEW), (STATUS_OLD, STATUS_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}: {old[:40]}")
        src = src.replace(old, new, 1)
    src = src.replace("//! checkbox, label, #, Comp Name", "// " + MARKER + "\n//! checkbox, label, #, Comp Name", 1)
    path.write_text(src, encoding="utf-8")
    print("queue headers and statuses are Chinese")


if __name__ == "__main__":
    main()
