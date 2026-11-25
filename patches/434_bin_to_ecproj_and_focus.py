#!/usr/bin/env python3
"""两处兜底修复。

1) **保存成 .bin**：SAF 的 create-document 对话框由系统决定扩展名（DocumentsUI 对未知 mime
   会补 .bin）。与其继续和系统斗，不如在保存完成后自己兜底：只要 `session.path` 以 `.bin` 结尾，
   就把工程另存为同名 `.ecproj`（真实文件，`file.saveAs` 直接写路径），状态栏告知新路径。

2) **全选效果看不见**：即使把效果与 effects 组都放进选中集合，效果控件没有焦点时也不画选中态。
   分派到效果控件后直接把焦点设回 EffectControls，高亮就会出现。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BIN_TO_ECPROJ_V1"

FRAME_ANCHOR = '''        // EFFECTCRAFT_OURS_ECPROJ_MIME_V1 — 上次异常退出过：这一轮不还原保存的布局，直接默认'''

FRAME_INSERT = '''        // EFFECTCRAFT_OURS_BIN_TO_ECPROJ_V1 — 系统把工程存成 .bin 时，自动另存为同名 .ecproj
        if let Some(p) = self.session.path.clone() {
            if p.to_ascii_lowercase().ends_with(".bin") && std::path::Path::new(&p).exists() {
                let fixed = format!("{}.ecproj", p.trim_end_matches(".bin"));
                if std::fs::copy(&p, &fixed).is_ok() {
                    let _ = self.session.execute(
                        "file.saveAs",
                        serde_json::json!({ "path": fixed }),
                    );
                    self.ui.status = format!("已保存为 {fixed}");
                }
            }
        }
        // EFFECTCRAFT_OURS_ECPROJ_MIME_V1 — 上次异常退出过：这一轮不还原保存的布局，直接默认'''

INV_OLD = '''            let r = invoke(app, ctx, "ours.selectAllEffects", json!({}))?;'''
INV_NEW = '''            // EFFECTCRAFT_OURS_BIN_TO_ECPROJ_V1 — 选完把焦点交回效果控件，选中态才画得出来
            app.ui.focused = crate::PanelKind::EffectControls;
            let r = invoke(app, ctx, "ours.selectAllEffects", json!({}))?;'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FRAME_ANCHOR) != 1:
            raise SystemExit(f"frame anchor: {src.count(FRAME_ANCHOR)}")
        frame.write_text(src.replace(FRAME_ANCHOR, FRAME_INSERT, 1), encoding="utf-8")
        print("saving to .bin now also writes a .ecproj")

    inv = root / "crates/ui-egui/src/menus/invoke.rs"
    src = inv.read_text(encoding="utf-8")
    if INV_OLD in src:
        inv.write_text(src.replace(INV_OLD, INV_NEW, 1), encoding="utf-8")
        print("select-all returns focus to Effect Controls")


if __name__ == "__main__":
    main()
