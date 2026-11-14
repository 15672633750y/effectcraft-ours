#!/usr/bin/env python3
"""Render-queue toasts in Chinese: "Rendered 1 item(s) in 27.7 s" was the last English on screen."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_RENDER_MSGS_ZH_V1"

EDITS = [
    ('format!("Render finished with 1 failed item(s): {only}")', 'format!("渲染结束，1 个失败：{only}")'),
    ('format!("Render finished with {failed} failed item(s), first: {first}")', 'format!("渲染结束，{failed} 个失败，第一个：{first}")'),
    ('"Render stopped".to_string()', '"渲染已停止".to_string()'),
    ('format!("Rendered {} item(s) in {:.1} s", st.items_total, st.elapsed)', 'format!("已渲染 {} 个项目，用时 {:.1} 秒", st.items_total, st.elapsed)'),
    ('format!("Post-render action: {e}")', 'format!("渲染后动作失败：{e}")'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("render messages already Chinese")
        return
    changed = 0
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
        changed += 1
    src = src.replace("use crate::{Event, Session};", "// " + MARKER + "\nuse crate::{Event, Session};", 1)
    path.write_text(src, encoding="utf-8")
    print(f"{changed} render messages translated")


if __name__ == "__main__":
    main()
