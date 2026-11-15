#!/usr/bin/env python3
"""The plug-in window can install one named file, not only rescan the folder.

The window explained where to drop `.wasm` / `.jsx`, but on a phone that means a file manager round
trip. It now has a path field and an install button that runs the same `effect.plugins.load` command
the folder scan uses, so a file downloaded anywhere can be installed from here.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PLUGIN_PATH_V1"

OLD = '''            if ui.button("知道了").clicked() {
                close = true;
            }
'''
NEW = '''            // EFFECTCRAFT_OURS_PLUGIN_PATH_V1 — 直接装一个文件：路径写上去，点安装
            ui.separator();
            ui.heading("直接安装一个文件");
            let path_id = egui::Id::new("ours-plugin-path");
            let mut path: String = ctx.data(|d| d.get_temp::<String>(path_id)).unwrap_or_default();
            ui.add(egui::TextEdit::singleline(&mut path).hint_text("/storage/emulated/0/Download/xxx.wasm"));
            ui.horizontal(|ui| {
                if ui.button("安装这个文件").clicked() {
                    let target = path.trim().to_string();
                    if target.is_empty() {
                        app.ui.status = "先填一个文件路径".into();
                    } else {
                        match crate::menus::invoke(app, ctx, "effect.plugins.load", serde_json::json!({"path": target})) {
                            Ok(_) => app.ui.status = "已安装".into(),
                            Err(e) => app.ui.status = format!("安装失败：{}", crate::i18n::tr(&e)),
                        }
                    }
                }
            });
            ctx.data_mut(|d| d.insert_temp(path_id, path));
            ui.separator();
            if ui.button("知道了").clicked() {
                close = true;
            }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    candidates = [p for p in (root / "crates/ui-egui/src").rglob("*.rs") if "导入插件" in p.read_text(encoding="utf-8", errors="ignore")]
    if not candidates:
        raise SystemExit("plug-in window not found (105_keyframe_buttons must run first)")
    path = candidates[0]
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("plug-in path install already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("plug-in window installs a named file")


if __name__ == "__main__":
    main()
