#!/usr/bin/env python3
"""The render queue's footer line in Chinese ("Message: 1 of 1 done", "Renders Started:…")."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_QUEUE_FOOTER_ZH_V1"

EDITS = [
    ('format!("Message: Rendering {} of {}", (pr.items_done + 1).min(pr.items_total), pr.items_total)',
     'format!("消息：正在渲染第 {} / {} 个", (pr.items_done + 1).min(pr.items_total), pr.items_total)'),
    ('format!("Message: {done} of {} done", queue.len())', 'format!("消息：已完成 {done} / {} 个", queue.len())'),
    ('format!("Renders Started: {started}     Total Time Elapsed: {}", hms(progress.as_ref().filter(|_| rendering).map(|p| p.elapsed).unwrap_or(total)))',
     'format!("已开始渲染 {started} 个     总耗时 {}", hms(progress.as_ref().filter(|_| rendering).map(|p| p.elapsed).unwrap_or(total)))'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("queue footer already Chinese")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:48]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    src = src.replace("/// The footer: the message line and the totals.", "/// The footer: the message line and the totals.\n// " + MARKER, 1)
    path.write_text(src, encoding="utf-8")
    print("render queue footer is Chinese")


if __name__ == "__main__":
    main()
