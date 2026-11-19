#!/usr/bin/env python3
"""底部工具条再加一个真按钮：**存帧**（把当前预览帧存成 PNG）。

调用引擎现成的 `render.saveCurrentPreview {comp?, path}`，文件写到
`/storage/emulated/0/DCIM/EffectCraft/Frames/frame_<毫秒>.png`。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SAVE_FRAME_V1"

ITEMS_LINE = '                            ("\\u{23e9}", "变速", 16),'
ITEM_ADD = '\n                            ("\\u{25a3}", "存帧", 17),'

MATCH_OLD = '''                Some(16) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.enableTimeRemap",
                        serde_json::json!({ "value": true }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已为选中图层打开时间重映射（可做变速）".into()
                    } else {
                        "先选中一个图层".into()
                    };
                }
                _ => {}'''

MATCH_NEW = '''                Some(16) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.enableTimeRemap",
                        serde_json::json!({ "value": true }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已为选中图层打开时间重映射（可做变速）".into()
                    } else {
                        "先选中一个图层".into()
                    };
                }
                Some(17) => {
                    // EFFECTCRAFT_OURS_SAVE_FRAME_V1 — 当前预览帧存 PNG
                    let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft/Frames");
                    let _ = std::fs::create_dir_all(dir);
                    let stamp = std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map(|d| d.as_millis())
                        .unwrap_or(0);
                    let path = dir.join(format!("frame_{stamp}.png"));
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "render.saveCurrentPreview",
                        serde_json::json!({ "path": path.to_string_lossy() }),
                    );
                    self.ui.status = if r.is_ok() {
                        format!("已保存当前帧：{}", path.display())
                    } else {
                        "保存失败：先打开一个合成并定位到要存的帧".into()
                    };
                }
                _ => {}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("save frame already present")
        return
    n = src.count(ITEMS_LINE)
    if n < 1:
        raise SystemExit(f"tray items anchor: {n}")
    src = src.replace(ITEMS_LINE, ITEMS_LINE + ITEM_ADD)
    if src.count(MATCH_OLD) != 1:
        raise SystemExit(f"match anchor: {src.count(MATCH_OLD)}")
    src = src.replace(MATCH_OLD, MATCH_NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("tray gained a real 存帧 button")


if __name__ == "__main__":
    main()
