#!/usr/bin/env python3
"""启动防崩链：连续崩溃两次后进入**安全模式**，保证能进得去。

现在安卓上的恢复逻辑是"直接打开自动保存"（363）。如果那个自动保存本身就会把进程带崩
（缺字体/缺效果/布局 JSON 坏掉），用户就会连续闪退——正是"打开闪退两次才能进入"。

改法：
* 每次进入恢复流程时，把 `DCIM/EffectCraft/.recovery-count` 加一；
* 计数 >= 2 时**不再自动打开**自动保存，改为：重置当前工作区布局 + 提示"已进入安全模式"，然后正常进主界面；
* 下次**干净启动**（没有 recoverable 会话）时把计数清零。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SAFE_MODE_V1"

OLD = '''pub fn recovery(app: &mut EffectcraftApp, ctx: &egui::Context, t: &Tokens) {
    let Some(r) = app.recovery.clone() else {
        app.dialog = None;
        return;
    };
    // EFFECTCRAFT_OURS_MOBILE_STABILITY_V1 — 手机上后台被杀不是崩溃：不弹框，直接恢复自动保存。
    #[cfg(target_os = "android")]
    {
        let _ = t;
        app.dialog = None;
        app.recovery = None;
        if let Some(p) = r.autosave.clone() {
            if let Err(e) = crate::menus::invoke(app, ctx, "file.open", json!({"path": p})) {
                app.ui.status = format!("自动恢复失败：{e}");
            }
        }
        return;
    }'''

NEW = '''pub fn recovery(app: &mut EffectcraftApp, ctx: &egui::Context, t: &Tokens) {
    let Some(r) = app.recovery.clone() else {
        app.dialog = None;
        // EFFECTCRAFT_OURS_SAFE_MODE_V1 — 这次是干净启动：把"连续崩溃"计数清零
        #[cfg(target_os = "android")]
        {
            let _ = std::fs::write(
                "/storage/emulated/0/DCIM/EffectCraft/.recovery-count",
                b"0",
            );
        }
        return;
    };
    // EFFECTCRAFT_OURS_MOBILE_STABILITY_V1 — 手机上后台被杀不是崩溃：不弹框，直接恢复自动保存。
    #[cfg(target_os = "android")]
    {
        let _ = t;
        app.dialog = None;
        app.recovery = None;
        // EFFECTCRAFT_OURS_SAFE_MODE_V1 — 连续崩溃两次就不再自动打开，先进得来再说
        let count_path = "/storage/emulated/0/DCIM/EffectCraft/.recovery-count";
        let count: u32 = std::fs::read_to_string(count_path)
            .ok()
            .and_then(|s| s.trim().parse().ok())
            .unwrap_or(0);
        if count >= 2 {
            let _ = std::fs::write(count_path, b"0");
            // 重置布局：坏掉的 dock JSON 是最常见的启动崩溃源
            let ws = app.ui.workspace.clone();
            app.set_workspace(&ws);
            app.ui.status = "已进入安全模式：跳过自动恢复，布局已重置".to_string();
            return;
        }
        let _ = std::fs::write(count_path, (count + 1).to_string());
        if let Some(p) = r.autosave.clone() {
            if let Err(e) = crate::menus::invoke(app, ctx, "file.open", json!({"path": p})) {
                app.ui.status = format!("自动恢复失败：{e}");
            }
        }
        return;
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/settings.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("safe mode already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("safe mode: skip auto-recovery after two consecutive crashes")


if __name__ == "__main__":
    main()
