#!/usr/bin/env python3
"""「布局」按钮：放回正常绘制流，只是提前到所有浮层之前。

之前它被画在 539-548 那一段浮层之后，所以永远盖着预设库/导入/云端面板。
改成独立 Area 又因为 `draw_layout_switcher` 内部按自己算的位置 + clip_rect 绘制而看不见。

最终做法最简单：仍用原来的绘制调用，只是插在 `shortcut_panel(...)` 之前。
- 位置/动画/点击/字体全部保持原样（画布右上角）
- 浮层在这之后绘制，自然盖住它
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1"
IMPORT_MARKER = "EFFECTCRAFT_OURS_IMPORT_SHIM_SCAN_V1"

ANCHOR = "        shortcut_panel(self, ui, full);\n"

INSERT = """        // EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1 — 「布局」在任何浮层之前绘制，
        // 所以预设库/导入/云端/账号面板都会盖住它（以前它最后画，永远最上层）。
        let layout_crashed =
            ui.data(|d| d.get_temp::<bool>(egui::Id::new("ours-layout-crashed")).unwrap_or(false));
        if !layout_crashed
            && std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                self.draw_layout_switcher(ui, full)
            }))
            .is_err()
        {
            ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-layout-crashed"), true));
            ui.data_mut(|d| d.remove::<f64>(egui::Id::new("layout-open-at")));
            self.ours_layout_error("switcher", "panic inside draw_layout_switcher");
        }
        shortcut_panel(self, ui, full);
"""


# ImportShim 把「打开方式」送来的文件放到 DCIM/EffectCraft/Import/，这里每帧最多检查一次，
# 有文件就按扩展名分发（和导入面板的分支一致），成功后删掉。
SCAN_ANCHOR = "        // EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1 — 「布局」在任何浮层之前绘制，\n"

SCAN_INSERT = """        // EFFECTCRAFT_OURS_IMPORT_SHIM_SCAN_V1 — ImportShim 落盘的文件，按扩展名走对应命令
        {
            let now = ui.input(|i| i.time);
            let last = ui
                .data(|d| d.get_temp::<f64>(egui::Id::new("ours-import-shim-at")))
                .unwrap_or(0.0);
            if now - last > 1.0 {
                ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-import-shim-at"), now));
                let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft/Import");
                if let Ok(entries) = std::fs::read_dir(dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if !path.is_file() {
                            continue;
                        }
                        let ext = path
                            .extension()
                            .and_then(|e| e.to_str())
                            .unwrap_or("")
                            .to_ascii_lowercase();
                        let p = path.to_string_lossy().to_string();
                        let (cmd, params) = match ext.as_str() {
                            "aep" | "aepx" => ("file.importAep", serde_json::json!({ "path": p })),
                            "ecproj" | "ecprojx" => {
                                ("file.importProject", serde_json::json!({ "path": p }))
                            }
                            "xml" | "fcpxml" | "otio" | "edl" | "aaf" | "omf" => {
                                ("file.importTimeline", serde_json::json!({ "path": p }))
                            }
                            "ffx" | "gp" => ("ours.applyPreset", serde_json::json!({ "path": p })),
                            _ => ("file.import", serde_json::json!({ "paths": [p] })),
                        };
                        match crate::menus::invoke(self, ui.ctx(), cmd, params) {
                            Ok(_) => {
                                let _ = std::fs::remove_file(&path);
                            }
                            Err(e) => {
                                self.ui.status = format!("导入失败：{e}");
                                let _ = std::fs::remove_file(&path);
                            }
                        }
                    }
                }
            }
        }
"""

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("layout call already moved")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, INSERT, 1)
    if IMPORT_MARKER not in src:
        if src.count(SCAN_ANCHOR) != 1:
            raise SystemExit(f"scan anchor: {src.count(SCAN_ANCHOR)}")
        src = src.replace(SCAN_ANCHOR, SCAN_INSERT + SCAN_ANCHOR, 1)
    frame.write_text(src, encoding="utf-8")
    print("布局 drawn before the floating panels; ImportShim drop dir is scanned")


if __name__ == "__main__":
    main()
