#!/usr/bin/env python3
"""Visible Chinese: the project context menu, and the default layer names."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_UI_CHINESE_V1"

ROWS = [
    ("New Composition…", "新建合成…"),
    ("New Folder", "新建文件夹"),
    ("Import File…", "导入文件…"),
    ("Open in Essential Graphics", "在基本图形中打开"),
    ("Select an item to see its details", "选择一个项目以查看详情"),
    ("Layer Name", "图层名称"),
    ("All", "全部"),
    ("None", "无"),
]

EDITS = [
    ("crates/ui-egui/src/panels/dialogs.rs", 'format!("Comp {n}")', 'format!("合成 {n}")'),
    ("crates/ui-egui/src/panels/precomp.rs", 'format!("{} Comp 1", l.name)', 'format!("{} 合成 1", l.name)'),
    ("crates/engine/src/cmd/layer/create.rs", '"Adjustment Layer 1".to_string()', '"调整图层 1".to_string()'),
    ("crates/engine/src/cmd/layer/create.rs", '"Solid 1".to_string()', '"纯色 1".to_string()'),
    ("crates/engine/src/cmd/layer/create.rs", '.unwrap_or("Shape Layer 1")', '.unwrap_or("形状图层 1")'),
    ("crates/engine/src/cmd/layer/create.rs", '"Null 1"', '"空对象 1"'),
    ("crates/engine/src/cmd/three_d.rs", '.unwrap_or("Camera 1")', '.unwrap_or("摄像机 1")'),
    ("crates/engine/src/cmd/three_d.rs", '.unwrap_or("Light 1")', '.unwrap_or("灯光 1")'),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    # 1. Project panel context menu: draw the labels through the translation table.
    proj = root / "crates/ui-egui/src/panels/project.rs"
    src = proj.read_text(encoding="utf-8")
    if MARKER not in src:
        old = "            let response = ui.button(label);\n"
        if src.count(old) != 1:
            raise SystemExit(f"project menu button: expected 1 match, found {src.count(old)}")
        src = src.replace(old, "            let response = ui.button(crate::i18n::tr(label));\n", 1)
        src = f"// {MARKER}\n" + src
        proj.write_text(src, encoding="utf-8")
        print("project.rs: context menu goes through tr()")

    # 2. The three rows in the Simplified Chinese catalog.
    ui = root / "crates/ui-egui/src/i18n/ui.rs"
    usrc = ui.read_text(encoding="utf-8")
    anchor = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"
    if anchor not in usrc:
        raise SystemExit("SIMPLIFIED_CHINESE table not found")
    added = "".join(f'    ("{en}", "{zh}"),\n' for en, zh in ROWS)
    if ROWS[0][0] not in usrc.split(anchor, 1)[1][:4000]:
        usrc = usrc.replace(anchor, anchor + added, 1)
        ui.write_text(usrc, encoding="utf-8")
        print("ui.rs: added", len(ROWS), "rows")

    # 3. Default layer names.
    for rel, old, new in EDITS:
        p = root / rel
        s = p.read_text(encoding="utf-8")
        if new in s:
            continue
        if s.count(old) != 1:
            raise SystemExit(f"{rel}: expected one {old!r}, found {s.count(old)}")
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
        print(f"{rel}: {old} -> {new}")


if __name__ == "__main__":
    main()
