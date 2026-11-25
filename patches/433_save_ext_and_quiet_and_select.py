#!/usr/bin/env python3
"""再修三处：

1) **保存出来仍是 .bin**：只改 mime 依赖 DocumentsUI 的行为，不可靠。这里在保存回调里
   **主动把文档重命名**成建议的名字（含 .ecproj）：`DocumentsContract.renameDocument`，
   失败也不影响后续（staged 文件名仍按建议扩展名）。

2) **「Auto-saved to …」气泡**：`file.autoSave` 命令里 `s.toast(...)` 每次都弹。
   现在完全静默；切后台那次由界面自己写状态栏一行。

3) **全选效果**：除了每个效果的 uid，也把 `effects` 组本身放进选中集合，
   这样效果控件里整块会被高亮（只选子项时某些视图不显示选中）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SAVE_EXT_V1"

# ---- 1) Java：保存后强制重命名
JAVA_ANCHOR = "                name = keepSuggestedExtension(name, suggestedNames.get(id));"
JAVA_INSERT = '''                // EFFECTCRAFT_OURS_SAVE_EXT_V1 — DocumentsUI 可能把扩展名换成 .bin；
                // 这里用 renameDocument 把它改回建议的名字（含 .ecproj），失败则退回原逻辑。
                String suggested = suggestedNames.get(id);
                if (suggested != null && !suggested.isEmpty()) {
                    String lowerName = name == null ? "" : name.toLowerCase(java.util.Locale.ROOT);
                    String lowerSuggested = suggested.toLowerCase(java.util.Locale.ROOT);
                    int sd = lowerSuggested.lastIndexOf('.');
                    if (sd > 0 && !lowerName.endsWith(lowerSuggested.substring(sd))) {
                        try {
                            Uri renamed = android.provider.DocumentsContract.renameDocument(
                                getContentResolver(), uri, suggested);
                            if (renamed != null) {
                                uri = renamed;
                                String after = displayName(renamed);
                                if (after != null && !after.trim().isEmpty()) name = after;
                            }
                        } catch (Throwable ignored) {
                        }
                    }
                }
                name = keepSuggestedExtension(name, suggestedNames.get(id));'''

# ---- 2) 静默 file.autoSave
TOAST_OLD = '''    s.toast(format!("Auto-saved to {path}"));'''
TOAST_NEW = '''    // EFFECTCRAFT_OURS_SAVE_EXT_V1 — 自动保存不再弹气泡（切后台那次由界面提示）
    let _ = &path;'''

# ---- 3) 全选效果时也选中 effects 组
SEL_OLD = '''        for group in fx.groups() {
            picked.push((lid, group.uid));
        }'''
SEL_NEW = '''        // EFFECTCRAFT_OURS_SAVE_EXT_V1 — 先选 effects 组本身，再选每个效果，视图才会整块高亮
        picked.push((lid, fx.uid));
        for group in fx.groups() {
            picked.push((lid, group.uid));
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    # Java 模板（构建器）
    java = None
    for cand in (
        root.parents[0] / "templates/android/SafActivity.java",
        root.parents[1] / "templates/android/SafActivity.java" if len(root.parents) > 1 else None,
        root.parents[2] / "templates/android/SafActivity.java" if len(root.parents) > 2 else None,
        root.parents[0] / "builder/templates/android/SafActivity.java",
    ):
        if cand and cand.exists() and any(p in ("artcraft", "builder") for p in cand.parts):
            java = cand
            break
    if java is not None:
        src = java.read_text(encoding="utf-8")
        if MARKER not in src and JAVA_ANCHOR in src:
            src = src.replace(JAVA_ANCHOR, JAVA_INSERT, 1)
            java.write_text(src, encoding="utf-8")
            print("SafActivity: rename the saved document back to the suggested extension")

    # 静默自动保存 toast
    settings = root / "crates/engine/src/cmd/settings.rs"
    src = settings.read_text(encoding="utf-8")
    if TOAST_OLD in src:
        settings.write_text(src.replace(TOAST_OLD, TOAST_NEW, 1), encoding="utf-8")
        print("file.autoSave is silent")

    # 全选效果也选组
    ours = root / "crates/engine/src/cmd/ours_export.rs"
    src = ours.read_text(encoding="utf-8")
    if SEL_OLD in src:
        ours.write_text(src.replace(SEL_OLD, SEL_NEW, 1), encoding="utf-8")
        print("select-all effects also selects the group")


if __name__ == "__main__":
    main()
