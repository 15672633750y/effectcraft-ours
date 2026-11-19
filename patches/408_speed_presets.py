#!/usr/bin/env python3
"""变速快捷档：0.5× / 1× / 2×，直接调引擎的 `layer.timeStretch`。

引擎的 `layer.timeStretch {layers?, percent?, hold?, op?}` 就是"时间伸缩"：
percent 200（时长×2）= 0.5× 慢放，50 = 2× 快放，100 = 原速。
所以这三个按钮是真变速，不是摆设。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SPEED_PRESETS_V1"

LINE = '                            ("\\u{25a3}", "存帧", 17),'
ADD = '\n                            ("\\u{00bd}", "0.5×", 18),\n                            ("1", "1×", 19),\n                            ("2", "2×", 20),'

MATCH_OLD = '''                Some(17) => {
                    // EFFECTCRAFT_OURS_SAVE_FRAME_V1 — 当前预览帧存 PNG'''

MATCH_NEW = '''                Some(18) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.timeStretch",
                        serde_json::json!({ "percent": 200.0 }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已设为 0.5× 慢放（时长 ×2）".into()
                    } else {
                        "先选中图层".into()
                    };
                }
                Some(19) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.timeStretch",
                        serde_json::json!({ "percent": 100.0 }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已恢复原速".into()
                    } else {
                        "先选中图层".into()
                    };
                }
                Some(20) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.timeStretch",
                        serde_json::json!({ "percent": 50.0 }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已设为 2× 快放（时长 ÷2）".into()
                    } else {
                        "先选中图层".into()
                    };
                }
                Some(17) => {
                    // EFFECTCRAFT_OURS_SAVE_FRAME_V1 — 当前预览帧存 PNG'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("speed presets already present")
        return
    n = src.count(LINE)
    if n < 1:
        raise SystemExit(f"tray anchor: {n}")
    src = src.replace(LINE, LINE + ADD)
    if src.count(MATCH_OLD) != 1:
        raise SystemExit(f"match anchor: {src.count(MATCH_OLD)}")
    src = src.replace(MATCH_OLD, MATCH_NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("speed presets 0.5x / 1x / 2x wired to layer.timeStretch")


if __name__ == "__main__":
    main()
