#!/usr/bin/env python3
"""Settings ▸ Labels in Chinese: the stored default names (Red, Yellow, Aqua …) were English.

The label names are data — the settings page draws the stored name — so translating at draw time was
not enough. Defaults are created in Chinese now, and prefs written before this change are migrated
when they load (`Prefs::normalize`). A label the user renamed is not in the table and stays as it is,
and `Prefs::default()` itself is Chinese, so a round trip through JSON is unchanged (the engine's
own `prefs_round_trip_through_json` test checks that).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1"

HELPER = '''
/// 默认标签名的中文写法；自己改过的名字不在表里，返回 None。
pub(super) fn zh_label_name(name: &str) -> Option<&'static str> {
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

SECTIONS_OLD = '''pub(super) fn default_labels() -> Vec<LabelPref> {
    Label::ALL.iter().skip(1).map(|l| LabelPref { name: l.name().to_string(), color: hex(l.rgb()) }).collect()
}
'''
SECTIONS_NEW = '''pub(super) fn default_labels() -> Vec<LabelPref> {
    // EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1 — 默认标签名直接用中文
    Label::ALL
        .iter()
        .skip(1)
        .map(|l| LabelPref { name: zh_label_name(l.name()).unwrap_or(l.name()).to_string(), color: hex(l.rgb()) })
        .collect()
}
'''

MIGRATE = '''        // EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1
        // 旧设置里存的默认英文标签名，加载时换成中文（自己改过的名字不在表里，保持不变）。
        for pref in &mut self.labels {
            if let Some(zh) = super::sections::zh_label_name(&pref.name) {
                pref.name = zh.to_string();
            }
        }
'''

TEST_OLD = '    assert_eq!(p.labels[2].name, "Aqua");\n'
TEST_NEW = '    // EFFECTCRAFT_OURS_LABEL_DEFAULTS_ZH_V1 — 默认标签名是中文（第三个是 Aqua → 青）\n    assert_eq!(p.labels[2].name, "青");\n'

NORMALIZE = "    pub fn normalize(&mut self) {\n        self.version = PREFS_VERSION;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    sections = root / "crates/engine/src/settings/prefs/sections.rs"
    src = sections.read_text(encoding="utf-8")
    if "zh_label_name" not in src:
        if src.count(SECTIONS_OLD) != 1:
            raise SystemExit(f"sections anchor: {src.count(SECTIONS_OLD)}")
        src = src.replace(SECTIONS_OLD, SECTIONS_NEW, 1)
        src = src.rstrip() + "\n" + HELPER
        sections.write_text(src, encoding="utf-8")
        print("default label names are Chinese")

    doc = root / "crates/engine/src/settings/prefs/document.rs"
    src = doc.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(NORMALIZE) != 1:
            raise SystemExit(f"normalize anchor: {src.count(NORMALIZE)}")
        src = src.replace(NORMALIZE, NORMALIZE + MIGRATE, 1)
        doc.write_text(src, encoding="utf-8")
        print("old label names are migrated on load")

    tests = root / "crates/engine/src/tests/settings.rs"
    t = tests.read_text(encoding="utf-8")
    if TEST_NEW not in t and t.count(TEST_OLD) == 1:
        tests.write_text(t.replace(TEST_OLD, TEST_NEW, 1), encoding="utf-8")
        print("settings test expects the Chinese default")


if __name__ == "__main__":
    main()
