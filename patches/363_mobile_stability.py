#!/usr/bin/env python3
"""手机上的稳定性：崩溃自动恢复 + 崩溃日志。

1. 安卓上「退出」就是被系统杀进程，不是崩溃；原来会弹「上次未正常退出」对话框打断用户。
   现在检测到未正常退出时**直接打开自动保存**，不弹框。
2. 启动/运行闪退没有痕迹可查：装一个 panic hook，把崩溃写进
   `DCIM/EffectCraft/crash.log`（带时间和 backtrace），下次能定位。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MOBILE_STABILITY_V1"

RECOVERY_OLD = '''pub fn recovery(app: &mut EffectcraftApp, ctx: &egui::Context, t: &Tokens) {
    let Some(r) = app.recovery.clone() else {
        app.dialog = None;
        return;
    };'''
RECOVERY_NEW = '''pub fn recovery(app: &mut EffectcraftApp, ctx: &egui::Context, t: &Tokens) {
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

MAIN_OLD = '''            if let Some(r) = recovery) {
                app.offer_recovery(r);
            }'''
MAIN_NEW = '''            if let Some(r) = recovery {
                // EFFECTCRAFT_OURS_MOBILE_STABILITY_V1 — 手机上直接恢复，不弹"未正常退出"。
                app.offer_recovery(r);
            }'''

HOOK_ANCHOR = '''fn main() -> eframe::Result {'''
HOOK_INSERT = '''fn main() -> eframe::Result {
    // EFFECTCRAFT_OURS_MOBILE_STABILITY_V1 — 闪退留痕：panic 写到 DCIM/EffectCraft/crash.log。
    // 手机上拿不到 logcat 时，这个文件是唯一线索。
    let default_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
        let _ = std::fs::create_dir_all(dir);
        let path = dir.join("crash.log");
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        let line = format!("[{stamp}] panic: {info}\\n");
        use std::io::Write as _;
        if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&path) {
            let _ = f.write_all(line.as_bytes());
        }
        default_hook(info);
    }));
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    settings = root / "crates/ui-egui/src/panels/settings.rs"
    src = settings.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(RECOVERY_OLD) != 1:
            raise SystemExit(f"recovery anchor: {src.count(RECOVERY_OLD)}")
        settings.write_text(src.replace(RECOVERY_OLD, RECOVERY_NEW, 1), encoding="utf-8")
        print("android: recovery opens the auto-save instead of prompting")

    app_main = root / "apps/effectcraft/src/main.rs"
    src = app_main.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(HOOK_ANCHOR) != 1:
            raise SystemExit(f"main anchor: {src.count(HOOK_ANCHOR)}")
        src = src.replace(HOOK_ANCHOR, HOOK_INSERT, 1)
        app_main.write_text(src, encoding="utf-8")
        print("panic hook writes DCIM/EffectCraft/crash.log")


if __name__ == "__main__":
    main()
