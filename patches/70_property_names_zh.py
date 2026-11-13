#!/usr/bin/env python3
"""Show the transform property names in Chinese without renaming the stored properties.

The names stay English in the project data (scripts and expressions match on them); only the
text drawn in the Effect Controls panel and the Timeline goes through this table.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PROP_NAMES_ZH_V1"

MODULE = r'''//! Chinese display names for the common transform properties.

/// The Chinese label for a property's stored English name, but only inside the transform
/// groups: effect parameters keep their English names.
pub fn name<'a>(en: &'a str, _group: &str) -> &'a str {
    match en {
        "Transform" => "变换",
        "Audio" => "音频",
        "Audio Levels" => "音频电平",
        "Waveform" => "波形",
        "Levels" => "电平",
        "Effects" => "效果",
        "Layer Transform" => "图层变换",
        "Anchor Point" => "锚点",
        "Position" => "位置",
        "Scale" => "缩放",
        "Rotation" => "旋转",
        "Opacity" => "不透明度",
        "Orientation" => "方向",
        "X Rotation" => "X 轴旋转",
        "Y Rotation" => "Y 轴旋转",
        "Z Rotation" => "Z 轴旋转",
        "Skew" => "倾斜",
        "Skew Axis" => "倾斜轴",
        "Material Options" => "材质选项",
        "Contents" => "内容",
        "Text" => "文本",
        "Shape" => "形状",
        "Mask" => "遮罩",
        "Masks" => "遮罩",
        "Position X" => "X 位置",
        "Position Y" => "Y 位置",
        "Scale X" => "X 缩放",
        "Scale Y" => "Y 缩放",
        other => other,
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    prop_path = root / "crates/ui-egui/src/i18n/prop.rs"
    prop_path.parent.mkdir(parents=True, exist_ok=True)
    prop_path.write_text(MODULE, encoding="utf-8")

    i18n = root / "crates/ui-egui/src/i18n.rs"
    src = i18n.read_text(encoding="utf-8")
    if MARKER not in src:
        anchor = "mod ui;\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"i18n module anchor: expected 1, found {src.count(anchor)}")
        src = src.replace(anchor, anchor + "pub mod prop;\n", 1)
        i18n.write_text(f"// {MARKER}\n{src}", encoding="utf-8")
        print("i18n.rs: prop module registered")

    targets = [
        ("crates/ui-egui/src/panels/effect_controls/rows.rs",
         "pos2(swr.max.x + 6.0, cy), Align2::LEFT_CENTER, &prop.name, Tokens::ui(12.0)",
         "pos2(swr.max.x + 6.0, cy), Align2::LEFT_CENTER, crate::i18n::prop::name(&prop.name, &group.name), Tokens::ui(12.0)"),

    ]
    for rel, old, new in targets:
        p = root / rel
        s = p.read_text(encoding="utf-8")
        if new in s:
            continue
        if s.count(old) != 1:
            raise SystemExit(f"{rel}: expected 1 match, found {s.count(old)}")
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
        print(f"{rel}: property name drawing goes through the table")


if __name__ == "__main__":
    main()
