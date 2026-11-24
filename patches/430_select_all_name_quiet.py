#!/usr/bin/env python3
"""三处体验修正。

1) **全选真的全选**：原来「全选」只在焦点是效果控件时调 selectAllEffects（没选图层时什么都不发生）。
   现在先无条件 `edit.selectAll`（选中当前合成全部图层），焦点在效果控件时再附带全选效果。

2) **上传名字用真实工程名**：崩溃恢复会打开自动保存文件，`session.path` 指向 Auto-Save 目录，
   于是名字只能从快照推导。现在除了文件名与合成名，还会查 `prefs.recent_projects` 里
   最近一个**不在 Auto-Save 目录**的工程路径，用它的文件名——也就是用户真正保存的那个名字。

3) **自动保存不再弹提示**：定时自动保存完全静默（不弹 "Auto-saved …" 气泡）；
   只有切后台那一次（`ours-autosave-focus`）才在状态栏留一句。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SELECT_ALL_QUIET_V1"

# ---- 1) 全选
ALL_OLD = '''    if id == "ours.selectAllCtx" {
        let target = if app.ui.focused == crate::PanelKind::EffectControls {
            "ours.selectAllEffects"
        } else {
            "edit.selectAll"
        };
        return invoke(app, ctx, target, json!({}));
    }'''

ALL_NEW = '''    if id == "ours.selectAllCtx" {
        // EFFECTCRAFT_OURS_SELECT_ALL_QUIET_V1 — 先无条件全选图层（点击必须看得见效果）
        let layers = invoke(app, ctx, "edit.selectAll", json!({}));
        if app.ui.focused == crate::PanelKind::EffectControls {
            // 焦点在效果控件时，再把它这个图层上的效果也全选（失败不影响图层选择）
            let _ = invoke(app, ctx, "ours.selectAllEffects", json!({}));
        }
        return layers;
    }'''

# ---- 2) 名字：查最近工程
NAME_OLD = '''    let cleaned = out.trim().to_string();
    let lower = cleaned.to_ascii_lowercase();
    if cleaned.is_empty() || lower.starts_with("untitled") || cleaned == "无标题" {
        // EFFECTCRAFT_OURS_CLOUD_NAME_COMP_V1 — 用当前合成名，别固定成「我的工程」
        if let Some(id) = app.session.active_comp_id() {
            if let Some(item) = app.session.project.item(id) {
                let n = item.name.trim();
                if !n.is_empty() {
                    return n.to_string();
                }
            }
        }
        return "我的工程".to_string();
    }
    cleaned
}'''

NAME_NEW = '''    let cleaned = out.trim().to_string();
    let lower = cleaned.to_ascii_lowercase();
    if cleaned.is_empty() || lower.starts_with("untitled") || cleaned == "无标题" {
        // EFFECTCRAFT_OURS_SELECT_ALL_QUIET_V1 — 先找最近打开过的**真实**工程名
        if let Some(real) = app
            .session
            .prefs
            .recent_projects
            .iter()
            .find(|p| !p.contains("EffectCraft Auto-Save"))
        {
            if let Some(stem) = std::path::Path::new(real).file_stem() {
                let n = stem.to_string_lossy().to_string();
                let nl = n.to_ascii_lowercase();
                if !n.trim().is_empty() && !nl.starts_with("untitled") && n != "无标题" {
                    return n;
                }
            }
        }
        // 再退到当前合成名
        if let Some(id) = app.session.active_comp_id() {
            if let Some(item) = app.session.project.item(id) {
                let n = item.name.trim();
                if !n.is_empty() {
                    return n.to_string();
                }
            }
        }
        return "我的工程".to_string();
    }
    cleaned
}'''

# ---- 3) 静默自动保存
TOAST_OLD = '''        let r = self.autosave_now();
        if let Ok(p) = &r {
            self.toast(format!("Auto-saved {}", Path::new(p).file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default()));
        }
        Some(r)'''
TOAST_NEW = '''        let r = self.autosave_now();
        // EFFECTCRAFT_OURS_SELECT_ALL_QUIET_V1 — 定时自动保存静默，不弹气泡
        let _ = &r;
        Some(r)'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    inv = root / "crates/ui-egui/src/menus/invoke.rs"
    src = inv.read_text(encoding="utf-8")
    if ALL_OLD in src:
        inv.write_text(src.replace(ALL_OLD, ALL_NEW, 1), encoding="utf-8")
        print("select all: layers first, effects as a bonus")

    acct = root / "crates/ui-egui/src/account_ui.rs"
    src = acct.read_text(encoding="utf-8")
    if NAME_OLD in src:
        acct.write_text(src.replace(NAME_OLD, NAME_NEW, 1), encoding="utf-8")
        print("cloud name prefers the last real project file")

    sess = root / "crates/engine/src/settings/session_settings.rs"
    src = sess.read_text(encoding="utf-8")
    if TOAST_OLD in src:
        sess.write_text(src.replace(TOAST_OLD, TOAST_NEW, 1), encoding="utf-8")
        print("periodic auto-save is silent")


if __name__ == "__main__":
    main()
