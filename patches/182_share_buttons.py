#!/usr/bin/env python3
"""The 工程分享 row in the export dialog, with the four exports that exist today.

Placed above 开始导出, as in the reference dialog: package the project with its media, package it for
sharing, export just the `.ecproj`, or export Final Cut Pro 7 XML. The two formats whose writer needs
a sample from the other app (NodeVideo `.nv`, CapCut `draft_content.json`) are shown as buttons that
say so instead of pretending to work.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHARE_BUTTONS_V1"

ANCHOR = '''            ui.add_space(8.0);
            ui.horizontal(|ui| {
                if ui.button("开始导出").clicked() {
'''
NEW = '''            ui.add_space(8.0);
            ui.separator();
            ui.label(egui::RichText::new("工程分享").strong());
            ui.label(
                egui::RichText::new("打包后保存在 DCIM/EffectCraft；分享到 QQ 请在文件管理器里发送那个 zip。").weak(),
            );
            let base = "/storage/emulated/0/DCIM/EffectCraft";
            if ui.button("完整导出工程（包含素材）").clicked() {
                match crate::menus::invoke(app, ui.ctx(), "ours.exportProjectZip", serde_json::json!({"media": true})) {
                    Ok(_) => app.ui.status = "已打包工程（含素材）".into(),
                    Err(e) => app.ui.status = format!("打包失败：{e}"),
                }
            }
            if ui.button("完整打包并分享到 QQ").clicked() {
                match crate::menus::invoke(app, ui.ctx(), "ours.exportProjectZip", serde_json::json!({"media": true})) {
                    Ok(r) => {
                        let zip = r.get("zip").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        app.ui.status = format!("已打包：{zip}（用文件管理器发送到 QQ）");
                    }
                    Err(e) => app.ui.status = format!("打包失败：{e}"),
                }
            }
            if ui.button("只导出工程文件（.ecproj）").clicked() {
                let path = format!("{base}/工程分享.ecproj");
                match crate::menus::invoke(app, ui.ctx(), "file.saveCopy", serde_json::json!({"path": path})) {
                    Ok(_) => app.ui.status = format!("已导出：{path}"),
                    Err(e) => app.ui.status = format!("导出失败：{e}"),
                }
            }
            if ui.button("导出 AM 工程（.xml）").clicked() {
                let path = format!("{base}/工程分享.xml");
                match crate::menus::invoke(app, ui.ctx(), "file.exportTimeline", serde_json::json!({"path": path, "format": "xml"})) {
                    Ok(_) => app.ui.status = format!("已导出：{path}"),
                    Err(e) => app.ui.status = format!("导出失败：{e}"),
                }
            }
            if ui.button("导出 NodeVideo 工程包（.zip）").clicked() {
                app.ui.status = "暂不支持：需要 NodeVideo 工程样本才能写出可打开的 .nv".into();
            }
            if ui.button("导出 CapCut 桌面工程包（.zip）").clicked() {
                app.ui.status = "暂不支持：需要 CapCut 草稿样本才能写出可打开的 draft_content.json".into();
            }
            ui.add_space(8.0);
            ui.horizontal(|ui| {
                if ui.button("开始导出").clicked() {
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    candidates = [p for p in (root / "crates/ui-egui/src").rglob("*.rs") if 'if ui.button("开始导出").clicked()' in p.read_text(encoding="utf-8", errors="ignore")]
    if not candidates:
        raise SystemExit("export dialog not found (100_export_dialog must run first)")
    path = candidates[0]
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("share buttons already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, NEW, 1), encoding="utf-8")
    print("工程分享 buttons added")


if __name__ == "__main__":
    main()
