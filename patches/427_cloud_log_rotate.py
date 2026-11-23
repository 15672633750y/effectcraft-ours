#!/usr/bin/env python3
"""云端日志别无限长大：超过 512 KB 就截断重开。

`DCIM/EffectCraft/cloud.log` 每次上传/删除都追加一行，长期使用会变成几 MB 的无用文件。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_LOG_ROTATE_V1"

OLD = '''fn log_line(line: &str) {
    let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
    let _ = std::fs::create_dir_all(dir);
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(dir.join("cloud.log"))
    {'''

NEW = '''fn log_line(line: &str) {
    let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
    let _ = std::fs::create_dir_all(dir);
    let log_path = dir.join("cloud.log");
    // EFFECTCRAFT_OURS_CLOUD_LOG_ROTATE_V1 — 超过 512 KB 截断，避免日志无限增长
    if let Ok(meta) = std::fs::metadata(&log_path) {
        if meta.len() > 512 * 1024 {
            let _ = std::fs::write(&log_path, b"");
        }
    }
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
    {'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/cloud.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("log rotation already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("cloud.log rotates at 512 KB")


if __name__ == "__main__":
    main()
