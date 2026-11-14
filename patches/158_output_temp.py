#!/usr/bin/env python3
"""A render always lands somewhere writable.

The default output folder is `$HOME/Movies` (or `$HOME`). Android usually has no `HOME`, so the
engine fell through to the current directory — which is not writable — and a render "finished" in
the queue without a file existing. When there is no home folder, the cache folder (`temp_dir()`,
always writable) is used instead, and the gallery watcher scans it too.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_OUTPUT_TEMP_V1"

OLD = '''pub(crate) fn default_output_base(home: Option<std::path::PathBuf>) -> Option<std::path::PathBuf> {
    let home = home.filter(|h| !h.as_os_str().is_empty())?;
    let movies = home.join("Movies");
    Some(if movies.is_dir() { movies } else { home })
}
'''
NEW = '''pub(crate) fn default_output_base(home: Option<std::path::PathBuf>) -> Option<std::path::PathBuf> {
    // EFFECTCRAFT_OURS_OUTPUT_TEMP_V1 — 没有 HOME（安卓常见）时用 cache 目录：一定可写，
    // 相册监听也会扫它。之前这里返回 None，导出"完成"却没有文件。
    let Some(home) = home.filter(|h| !h.as_os_str().is_empty()) else {
        return Some(std::env::temp_dir());
    };
    let movies = home.join("Movies");
    Some(if movies.is_dir() { movies } else { home })
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("output fallback already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("renders fall back to the cache folder")


if __name__ == "__main__":
    main()
