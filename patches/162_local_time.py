#!/usr/bin/env python3
"""Render-queue times in local time.

`utc_stamp` printed UTC, so a phone at 02:00 showed "18:00" — eight hours off in Asia/Shanghai.
chrono is built without its `clock` feature here, so the timezone was never consulted; enabling it
and formatting through `chrono::Local` fixes the column.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LOCAL_TIME_V1"

CARGO_OLD = 'chrono = { version = "0.4.45", default-features = false, features = ["std"] }'
CARGO_NEW = 'chrono = { version = "0.4.45", default-features = false, features = ["std", "clock"] } # EFFECTCRAFT_OURS_LOCAL_TIME_V1'

STAMP_OLD = '''pub fn utc_stamp(unix: u64) -> String {
    let (y, t) = utc_parts(unix);
'''
STAMP_NEW = '''pub fn utc_stamp(unix: u64) -> String {
    // EFFECTCRAFT_OURS_LOCAL_TIME_V1 — 用本地时区显示（之前是 UTC，差 8 小时）
    use chrono::TimeZone as _;
    if let Some(local) = chrono::Local.timestamp_opt(unix as i64, 0).single() {
        return local.format("%Y-%m-%d %H:%M:%S").to_string();
    }
    let (y, t) = utc_parts(unix);
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    cargo = root / "Cargo.toml"
    src = cargo.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(CARGO_OLD) != 1:
            raise SystemExit(f"chrono anchor: {src.count(CARGO_OLD)}")
        cargo.write_text(src.replace(CARGO_OLD, CARGO_NEW, 1), encoding="utf-8")
        print("chrono clock feature enabled")

    ui = root / "crates/ui-egui/src/panels/render_queue.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(STAMP_OLD) != 1:
            raise SystemExit(f"stamp anchor: {src.count(STAMP_OLD)}")
        ui.write_text(src.replace(STAMP_OLD, STAMP_NEW, 1), encoding="utf-8")
        print("queue times use the local timezone")


if __name__ == "__main__":
    main()
