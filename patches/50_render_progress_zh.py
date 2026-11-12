#!/usr/bin/env python3
"""Chinese for the render progress lines and the queue labels."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RENDER_PROGRESS_ZH_V1"
EDITS = [
    ('format!("Elapsed: {}     Est. Remain: {rem}", hms(elapsed))',
     'format!("已用 {}    预计剩余 {rem}", hms(elapsed))'),
    ('format!("Renders Started: {started}     Total Time Elapsed: {}", hms(progress.as_ref().filter(|_| rendering).map(|p| p.elapsed).unwrap_or(total)))',
     'format!("已开始渲染 {started} 个    总耗时 {}", hms(progress.as_ref().filter(|_| rendering).map(|p| p.elapsed).unwrap_or(total)))'),
    ('format!("Rendering “{n}”   {} / {} frames", pr.done, pr.total)',
     'format!("正在渲染「{n}」  {} / {} 帧", pr.done, pr.total)'),
    ('format!("Message: Rendering {} of {}", (pr.items_done + 1).min(pr.items_total), pr.items_total)',
     'format!("进度：第 {} / {} 个", (pr.items_done + 1).min(pr.items_total), pr.items_total)'),
    ('format!("Rendering {:.0}%", if pr.total > 0 { pr.done as f64 * 100.0 / pr.total as f64 } else { 0.0 })',
     'format!("渲染中 {:.0}%", if pr.total > 0 { pr.done as f64 * 100.0 / pr.total as f64 } else { 0.0 })'),
    ('"Current Render"', '"当前渲染"'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("render progress already translated")
        return
    changed = 0
    for old, new in EDITS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
    if changed == 0:
        raise SystemExit("no render progress strings matched")
    src = src.replace("use crate::", "// " + MARKER + "\nuse crate::", 1)
    path.write_text(src, encoding="utf-8")
    print(f"{changed} render progress strings translated")


if __name__ == "__main__":
    main()
