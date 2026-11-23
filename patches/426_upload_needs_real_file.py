#!/usr/bin/env python3
"""上传前要求「真实工程文件」：自动保存文件不算数。

`cloud.log` 里的上传路径是 `.../EffectCraft Auto-Save/Untitled Project auto-save 3.ecproj`——
用户没保存过工程，上传的是自动保存快照，名字怎么推导都只能是 "Untitled Project"。

现在：如果当前 `session.path` 位于自动保存目录，就**先弹「另存为」**（默认名用当前合成名），
保存到用户自己的位置后再上传。这样工程名、去重、下载都建立在真实文件上。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_UPLOAD_REAL_FILE_V1"

OLD = '''    let Some(path) = app.session.path.clone().filter(|p| !p.is_empty()) else {
        // 新工程还没落盘：先让用户选个保存位置，回调下一帧再上传。
        if let Some(spawn) = app.hooks.file_dialog_async.as_ref() {
            let dialog = crate::FileDialog::Save { default: "我的工程.ecproj".to_string(), ext: "ecproj".to_string(), project: true };'''

NEW = '''    // EFFECTCRAFT_OURS_UPLOAD_REAL_FILE_V1 — 自动保存文件不算"已保存"：先另存为真实文件
    let autosave_path = app
        .session
        .path
        .clone()
        .filter(|p| p.contains("EffectCraft Auto-Save"));
    if autosave_path.is_some() {
        if let Some(spawn) = app.hooks.file_dialog_async.as_ref() {
            let default_name = format!("{}.ecproj", cloud_project_name(app, ""));
            let dialog = crate::FileDialog::Save {
                default: default_name,
                ext: "ecproj".to_string(),
                project: true,
            };
            let done: crate::DialogDone = Box::new(|paths| {
                if let Some(path) = paths.into_iter().next() {
                    if let Ok(mut slot) = pending_save().lock() {
                        *slot = Some(path);
                    }
                }
            });
            spawn(dialog, done);
            set(ui, MESSAGE, "这个工程还没保存到自己的位置，先选个位置保存再上传".to_string());
            ui.ctx().request_repaint();
        } else {
            set(ui, MESSAGE, "先把工程另存为一次再上传".to_string());
        }
        return;
    }
    let Some(path) = app.session.path.clone().filter(|p| !p.is_empty()) else {
        // 新工程还没落盘：先让用户选个保存位置，回调下一帧再上传。
        if let Some(spawn) = app.hooks.file_dialog_async.as_ref() {
            let default_name = format!("{}.ecproj", cloud_project_name(app, ""));
            let dialog = crate::FileDialog::Save { default: default_name, ext: "ecproj".to_string(), project: true };'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/account_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("upload real-file guard already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("upload demands a real project file, not an autosave")


if __name__ == "__main__":
    main()
