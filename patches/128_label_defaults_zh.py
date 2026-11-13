#!/usr/bin/env python3
"""Settings ▸ Labels in Chinese: the stored default names (Red, Yellow, Aqua …) were English.

The label names are data — the settings page that draws them reads the stored name — so translating
at draw time was not enough. `normalize()` now rewrites the *default* English names to their Chinese
ones when the preferences load; a name the user typed themselves is not in the table and stays."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1"

CALL = '''        // EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1
        // 默认标签名（Red、Yellow…）在加载时就换成中文，设置页、右键菜单、提示都跟着变。
        for pref in &mut self.labels {
            if let Some(zh) = zh_label_name(&pref.name) {
                pref.name = zh.to_string();
            }
        }
'''

HELPER = '''
/// 默认标签名的中文写法；自己改过的名字不在表里，原样返回 None。
fn zh_label_name(name: &str) -> Option<&'static str> {
    Some(match name {
        "Red" => "红",
        "Yellow" => "黄",
        "Aqua" => "青",
        "Pink" => "粉",
        "Lavender" => "淡紫",
        "Peach" => "桃",
        "Sea Foam" => "海沫",
        "Blue" => "蓝",
        "Purple" => "紫",
        "Green" => "绿",
        "Orange" => "橙",
        "Fuchsia" => "洋红",
        "Brown" => "棕",
        "Cyan" => "青蓝",
        "Sandstone" => "砂岩",
        "Dark Green" => "墨绿",
        _ => return None,
    })
}
'''

ANCHOR = "    pub fn normalize(&mut self) {\n        self.version = PREFS_VERSION;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/settings/prefs/document.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("label defaults already Chinese")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"normalize anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ANCHOR + CALL, 1)
    src = src.rstrip() + "\n" + HELPER
    path.write_text(src, encoding="utf-8")
    print("default label names are Chinese")


if __name__ == "__main__":
    main()
