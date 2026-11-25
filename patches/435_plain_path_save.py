#!/usr/bin/env python3
"""「保存」不再走系统 SAF 对话框：直接写到可见目录，彻底避开 .bin。

SAF 的 create-document 由系统决定扩展名，几轮都改不动（对话框里就是 `.bin`）。
工具条上的「保存」改成直接写 `/storage/emulated/0/DCIM/EffectCraft/Projects/<名字>.ecproj`：
* 名字取「最近真实工程名 → 当前合成名 → 我的工程」
* 用普通路径 `file.saveAs`，不经过 DocumentsUI，扩展名 100% 正确
* 目录不存在会自动创建，状态栏给出完整路径

菜单里的「另存为」仍走系统对话框（用户可能想存到云盘），但工具条这条路保证有一个对的 .ecproj。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PLAIN_SAVE_V1"

OLD = '''                        None => {
                            if let Some(spawn) = self.hooks.file_dialog_async.as_ref() {
                                let dialog = crate::FileDialog::Save {
                                    default: "我的工程.ecproj".to_string(),
                                    ext: "ecproj".to_string(),
                                    project: true,
                                };
                                let done: crate::DialogDone = Box::new(|paths| {
                                    if let Some(p) = paths.into_iter().next() {
                                        if let Ok(mut slot) = ours_save_target().lock() {
                                            *slot = Some(p);
                                        }
                                    }
                                });
                                spawn(dialog, done);
                                self.ui.status = "选择保存位置…".to_string();
                            } else {
                                self.ui.status = "这个平台没有文件选择器".to_string();
                            }
                        }'''

NEW = '''                        None => {
                            // EFFECTCRAFT_OURS_PLAIN_SAVE_V1 — 直接写可见目录，不经 SAF（系统会把扩展名改成 .bin）
                            let dir = std::path::Path::new(
                                "/storage/emulated/0/DCIM/EffectCraft/Projects",
                            );
                            if std::fs::create_dir_all(dir).is_ok() {
                                let mut stem = crate::panels::project::ours_project_display_name(self);
                                let lower = stem.to_ascii_lowercase();
                                if stem.trim().is_empty() || lower.starts_with("untitled") {
                                    stem = "我的工程".to_string();
                                }
                                let path = dir.join(format!("{stem}.ecproj"));
                                let path_str = path.to_string_lossy().to_string();
                                let r = crate::menus::invoke(
                                    self,
                                    ui.ctx(),
                                    "file.saveAs",
                                    serde_json::json!({ "path": path_str }),
                                );
                                self.ui.status = if r.is_ok() {
                                    format!("已保存到 {path_str}")
                                } else {
                                    "保存失败".to_string()
                                };
                            } else {
                                self.ui.status = "无法创建 Projects 目录".to_string();
                            }
                        }'''



def add_name_helper(root: Path) -> None:
    proj = root / "crates/ui-egui/src/panels/project.rs"
    src = proj.read_text(encoding="utf-8")
    if "OURS_PROJECT_DISPLAY_NAME_V1" in src:
        return
    fn = """
/// OURS_PROJECT_DISPLAY_NAME_V1 — 给"保存"用的工程名：最近真实工程 → 当前合成 → 我的工程。
pub(crate) fn ours_project_display_name(app: &EffectcraftApp) -> String {
    if let Some(p) = app.session.path.as_ref().filter(|p| !p.contains("EffectCraft Auto-Save")) {
        if let Some(s) = std::path::Path::new(p).file_stem() {
            let n = s.to_string_lossy().to_string();
            if !n.trim().is_empty() {
                return n;
            }
        }
    }
    if let Some(real) = app.session.prefs.recent_projects.iter().find(|p| !p.contains("EffectCraft Auto-Save")) {
        if let Some(s) = std::path::Path::new(real).file_stem() {
            let n = s.to_string_lossy().to_string();
            if !n.trim().is_empty() && !n.to_ascii_lowercase().starts_with("untitled") {
                return n;
            }
        }
    }
    if let Some(id) = app.session.active_comp_id() {
        if let Some(item) = app.session.project.item(id) {
            if !item.name.trim().is_empty() {
                return item.name.clone();
            }
        }
    }
    "我的工程".to_string()
}
"""
    proj.write_text(src + fn, encoding="utf-8")
    print("project.rs: display-name helper added")


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("plain-path save already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("tray 保存 writes straight to DCIM/EffectCraft/Projects")
    add_name_helper(root)


if __name__ == "__main__":
    main()
