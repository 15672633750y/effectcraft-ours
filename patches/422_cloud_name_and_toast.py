#!/usr/bin/env python3
"""云端两个小修：

【1】工程名恒为「我的工程」—— 上一版 `cloud_project_name()` 一看到文件名里带 "auto-save"
     就直接回退，而崩溃恢复后 `session.path` **本来就是自动保存文件**
     （`<原名> auto-save N.ecproj`），于是所有上传都成了「我的工程」。
     现在：先剥掉全部 " auto-save N" 再判断，只有剥完为空 / 仍是 Untitled 才回退。

【2】下载完成后底部的「正在下载…」不消失 —— `Event::Downloaded` 只设了 `app.ui.status`，
     没清 `MESSAGE` 与 loading 标志。补上。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_NAME_TOAST_V1"

NAME_OLD = '''fn cloud_project_name(path: &str) -> String {
    let stem = std::path::Path::new(path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let lower = stem.to_ascii_lowercase();
    if lower.contains("auto-save") || lower.contains("untitled") || stem.trim().is_empty() {
        return "我的工程".to_string();
    }
    let mut out = String::new();
    for part in stem.split(" auto-save") {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        if !out.is_empty() {
            out.push(' ');
        }
        out.push_str(part);
    }
    if out.trim().is_empty() { "我的工程".to_string() } else { out.trim().to_string() }
}'''

NAME_NEW = '''fn cloud_project_name(path: &str) -> String {
    let stem = std::path::Path::new(path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    // 崩溃恢复后 session.path 本身就是自动保存文件：`<原名> auto-save N.ecproj`。
    // 所以**先剥**掉所有 " auto-save N"，再判断是否需要回退——不能一看到 auto-save 就退回默认名。
    let mut out = String::new();
    for part in stem.split(" auto-save") {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        if !out.is_empty() {
            out.push(' ');
        }
        out.push_str(part);
    }
    let cleaned = out.trim().to_string();
    let lower = cleaned.to_ascii_lowercase();
    if cleaned.is_empty() || lower.starts_with("untitled") || cleaned == "无标题" {
        return "我的工程".to_string();
    }
    cleaned
}'''

DL_OLD = '''            Event::Downloaded(path) => {
                app.ui.status = "已下载，正在打开…".to_string();'''
DL_NEW = '''            Event::Downloaded(path) => {
                // EFFECTCRAFT_OURS_CLOUD_NAME_TOAST_V1 — 清掉「正在下载…」与 loading 标志
                set(ui, MESSAGE, String::new());
                set(ui, CLOUD_LOADING, false);
                app.ui.status = "已下载，正在打开…".to_string();'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/account_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("cloud name/toast already fixed")
        return
    for name, old, new in (("name", NAME_OLD, NAME_NEW), ("download", DL_OLD, DL_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("cloud: stable name from autosave stem, download toast cleared")


if __name__ == "__main__":
    main()
