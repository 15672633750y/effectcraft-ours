#!/usr/bin/env python3
"""「保存预设」绕开 SAF：不弹系统保存对话框，直接写进预设库目录。

Android 的 SAF 保存框会强制改后缀（实测出现 `Preset.bin`），即使导出逻辑正确，路径也会被
改写。所以这里直接算路径：

    DCIM/EffectCraft/Presets/<图层名>.ffx

三个好处：路径确定、后缀可控；预设库扫的就是这个目录，写完立刻能看到；手机上少一次系统交互。

落地由 `349_save_preset_json` 的 `save_preset` 兜底分支完成（没选中具体效果时调
`ours_export::export_preset`），所以这里只需要把 path 递进去。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_SAVE_NO_SAF_V1"

ANCHOR = '''    let (key, ask) = match id {
'''

INSERT = '''    // EFFECTCRAFT_OURS_PRESET_SAVE_NO_SAF_V1 — 保存预设不走系统对话框（SAF 会强改成 .bin）：
    // 直接写到预设库目录，文件名取当前选中图层的名字。
    if id == "anim.savePreset" {
        let dir = std::path::PathBuf::from("/storage/emulated/0/DCIM/EffectCraft/Presets");
        let _ = std::fs::create_dir_all(&dir);
        let layer_name = app
            .session
            .active_comp()
            .and_then(|c| {
                app.session
                    .state
                    .selected_layers
                    .first()
                    .and_then(|lid| c.layer(*lid))
            })
            .map(|l| l.name.clone())
            .unwrap_or_else(|| "Preset".to_string());
        let safe: String = layer_name
            .chars()
            .map(|c| if c.is_alphanumeric() || c == '_' || c == '-' { c } else { '_' })
            .collect();
        let name = if safe.trim_matches('_').is_empty() { "Preset".to_string() } else { safe };
        let path = dir.join(format!("{name}.ffx")).to_string_lossy().to_string();
        return Some(run_with_picked(app, id, "path", &params, json!(path)));
    }
    let (key, ask) = match id {
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/menus/frontend.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset save already bypasses SAF")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"frontend anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("save preset writes DCIM/EffectCraft/Presets/<layer>.ffx directly")


if __name__ == "__main__":
    main()
