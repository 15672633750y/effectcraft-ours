#!/usr/bin/env python3
"""三处修正：

1) **保存成 .bin 的根因**：SAF 的 `mimeFor()` 不认 `.ecproj`，落回 `application/octet-stream`，
   Android 的 DocumentsUI 会把这种 mime 的默认扩展补成 **.bin**，于是「哦哦哦哦」变成
   「哦哦哦哦.bin」。给工程文件一个专属 mime，DocumentsUI 就不会再改扩展名。

2) **全选效果没有反馈**：`ours.selectAllEffects` 其实选中了，但界面没提示，看起来像没反应。
   分派成功后把数量写到状态栏。

3) **上一次是异常退出时，不还原工作区布局**：坏掉的 dock JSON 是启动即崩的常见原因；
   计数文件里已有崩溃记录时，这一轮直接用默认布局，避免"第一次打开闪退"。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ECPROJ_MIME_V1"

# ---- 1) Java mime
JAVA_OLD = '''        if (lower.endsWith(".psd")) return "image/vnd.adobe.photoshop";
        return "application/octet-stream";'''
JAVA_NEW = '''        if (lower.endsWith(".psd")) return "image/vnd.adobe.photoshop";
        // EFFECTCRAFT_OURS_ECPROJ_MIME_V1 — 工程文件用专属 mime：否则 DocumentsUI 会把
        // application/octet-stream 的默认扩展补成 .bin，保存出来就成了「名字.bin」。
        if (lower.endsWith(".ecproj") || lower.endsWith(".ecprojx")
            || lower.endsWith(".ecprj") || lower.endsWith(".aep")) {
            return "application/x-effectcraft-project";
        }
        return "application/octet-stream";'''

# ---- 2) 全选反馈
SEL_OLD = '''            return invoke(app, ctx, "ours.selectAllEffects", json!({}));'''
SEL_NEW = '''            let r = invoke(app, ctx, "ours.selectAllEffects", json!({}))?;
            let n = r.get("effects").and_then(|v| v.as_u64()).unwrap_or(0);
            app.ui.status = if n == 0 {
                "这个图层没有效果可选".to_string()
            } else {
                format!("已全选 {n} 个效果")
            };
            return Ok(r);'''

# ---- 3) 崩溃后不还原布局
CRASH_ANCHOR = '''        // EFFECTCRAFT_OURS_SELECT_ALL_AE_V1 — 记住最后一个"内容面板"'''

CRASH_INSERT = '''        // EFFECTCRAFT_OURS_ECPROJ_MIME_V1 — 上次异常退出过：这一轮不还原保存的布局，直接默认
        {
            let id = egui::Id::new("ours-layout-safe");
            if ui.ctx().data(|d| d.get_temp::<bool>(id)).is_none() {
                let crashed = std::fs::read_to_string(
                    "/storage/emulated/0/DCIM/EffectCraft/.recovery-count",
                )
                .ok()
                .and_then(|s| s.trim().parse::<u32>().ok())
                .unwrap_or(0)
                    > 0;
                ui.ctx().data_mut(|d| d.insert_temp(id, true));
                if crashed {
                    let ws = self.ui.workspace.clone();
                    self.set_workspace(&ws);
                }
            }
        }
        // EFFECTCRAFT_OURS_SELECT_ALL_AE_V1 — 记住最后一个"内容面板"'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    # Java 模板在构建器里：EFFECTCRAFT_DIR=<artcraft>/source/effectcraft → <artcraft>/templates/android
    java = root.parents[2] / "templates/android/SafActivity.java" if len(root.parents) > 2 else root / "nope"
    if not java.exists():
        java = root.parents[1] / "templates/android/SafActivity.java" if len(root.parents) > 1 else root / "nope"
    if not java.exists():
        java = root.parent / "builder/templates/android/SafActivity.java"
    if java.exists():
        src = java.read_text(encoding="utf-8")
        if MARKER not in src:
            if src.count(JAVA_OLD) != 1:
                raise SystemExit(f"java anchor: {src.count(JAVA_OLD)}")
            java.write_text(src.replace(JAVA_OLD, JAVA_NEW, 1), encoding="utf-8")
            print("SafActivity: .ecproj gets its own mime")

    inv = root / "crates/ui-egui/src/menus/invoke.rs"
    src = inv.read_text(encoding="utf-8")
    if SEL_OLD in src:
        inv.write_text(src.replace(SEL_OLD, SEL_NEW, 1), encoding="utf-8")
        print("select all effects reports the count")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("layout safe guard already present")
        return
    if src.count(CRASH_ANCHOR) != 1:
        raise SystemExit(f"frame anchor: {src.count(CRASH_ANCHOR)}")
    frame.write_text(src.replace(CRASH_ANCHOR, CRASH_INSERT, 1), encoding="utf-8")
    print("layout is not restored after an abnormal exit")


if __name__ == "__main__":
    main()
