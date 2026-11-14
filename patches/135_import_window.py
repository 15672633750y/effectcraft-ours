#!/usr/bin/env python3
"""The import window: plug-ins and the project formats the app can read, in one place.

The Import File entry only opened the system picker, which silently accepted anything. This adds
"导入插件与工程…" to the same menu (the import tab the user asked for, not the scrolling tool row):
a window that says what each extension brings in, offers the picker, and has a button that rescans
the folder plug-ins are dropped in.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_IMPORT_WINDOW_V1"

MENU_OLD = '''            [("newComp", "New Composition…", "comp.new"), ("newFolder", "New Folder", "project.newFolder"), ("import", "Import File…", "file.import")]
'''
MENU_NEW = '''            [
                ("newComp", "New Composition…", "comp.new"),
                ("newFolder", "New Folder", "project.newFolder"),
                ("import", "Import File…", "file.import"),
                // EFFECTCRAFT_OURS_IMPORT_WINDOW_V1 — 插件与工程格式都从这里进
                ("importAll", "导入插件与工程…", "ours.import"),
            ]
'''

LOOP_OLD = '''    for (id, params) in actions {
        if let Err(e) = crate::menus::invoke(app, &ctx, &id, params) {
            app.ui.status = e;
        }
'''
LOOP_NEW = '''    for (id, params) in actions {
        if id == "ours.import" {
            ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-import-open"), true));
            continue;
        }
        if let Err(e) = crate::menus::invoke(app, &ctx, &id, params) {
            app.ui.status = e;
        }
'''

CALL = '''    import_window(app, ui.ctx());
'''

WINDOW = r'''

/// 导入：插件与工程格式，各带一句说明。
fn import_window(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let open_id = egui::Id::new("ours-import-open");
    let mut open = ctx.data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    let t = app.tokens;
    let rows: [(&str, &str); 6] = [
        ("After Effects 工程", "`.aep` / `.aepx` → 合成、图层、关键帧、效果、音频（多数可还原）"),
        ("EffectCraft 工程", "`.ecproj` → 整个工程，原样打开"),
        ("剪映 / CapCut 工程", "工程文件夹里的 `draft_content.json` → 媒体与时间线（实验）"),
        ("Nuke 工程", "`.nk` → 只导入 Read 节点的素材路径（实验）"),
        ("快影工程", "`.zip` → 只导入里面的媒体文件（实验）"),
        ("媒体", "mp4 / mov / png / jpg / wav / mp3 … → 作为素材导入"),
    ];
    egui::Window::new("导入")
        .open(&mut open)
        .collapsible(false)
        .resizable(false)
        .default_width(460.0)
        .show(ctx, |ui| {
            ui.heading("插件");
            ui.label("把 .wasm（效果）/ .jsx（脚本）/ .zip 放进 Download 或 Download/EffectCraftPlugins，");
            ui.label("重启 App 会自动安装；也可以点下面这个按钮现在扫一遍。");
            ui.horizontal(|ui| {
                if ui.button("扫描并安装插件").clicked() {
                    match crate::menus::invoke(app, ctx, "effect.plugins.load", serde_json::json!({
                        "path": "/storage/emulated/0/Download/EffectCraftPlugins"
                    })) {
                        Ok(_) => app.ui.status = "插件已扫描".into(),
                        Err(e) => app.ui.status = format!("扫描失败：{}", crate::i18n::tr(&e)),
                    }
                }
                if ui.button("插件说明").clicked() {
                    ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-plugin-open"), true));
                }
            });
            ui.separator();
            ui.heading("工程与素材");
            for (name, hint) in rows {
                ui.horizontal(|ui| {
                    ui.add_sized(vec2(150.0, 16.0), egui::Label::new(egui::RichText::new(name).strong()).truncate());
                    ui.label(egui::RichText::new(hint).weak());
                });
            }
            ui.add_space(6.0);
            if ui.button("导入文件…").clicked() {
                if let Err(e) = crate::menus::invoke(app, ctx, "file.import", serde_json::json!({})) {
                    app.ui.status = e;
                }
            }
            ui.label(egui::RichText::new("提示：`.ffx` 预设是 After Effects 的效果预设，不是工程；用「效果」菜单里的同名效果代替。").weak());
        });
    let _ = t;
    ctx.data_mut(|d| d.insert_temp(open_id, open));
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/project.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("import window already installed")
        return
    for old, new in ((MENU_OLD, MENU_NEW), (LOOP_OLD, LOOP_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:50]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    # Draw the window once per frame from the panel.
    anchor = "    marquee_select(app, &ctx, &lp, list, &empty, &rows);\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"call anchor: {src.count(anchor)}")
    src = src.replace(anchor, CALL + anchor, 1)
    src += WINDOW
    path.write_text(src, encoding="utf-8")
    print("import window (plug-ins + formats) installed")


if __name__ == "__main__":
    main()
