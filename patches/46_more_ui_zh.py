#!/usr/bin/env python3
"""More interface strings in Chinese: project panel, timeline headers, empty states."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MORE_UI_ZH_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"

ROWS = '''    // EFFECTCRAFT_OURS_MORE_UI_ZH_V1
    ("Select an item to see its details", "选择一个项目以查看详情"),
    ("Select a layer to see its properties", "选择图层以查看其属性"),
    ("Select a layer to see its effects", "选择图层以查看其效果"),
    ("Layer Name", "图层名称"),
    ("Parent & Link", "父级与链接"),
    ("Switch Toggle/Modes", "切换开关/模式"),
    ("Switches", "开关"),
    ("Modes", "模式"),
    ("No Composition", "没有合成"),
    ("New Composition", "新建合成"),
    ("New Composition from Footage", "从素材新建合成"),
    ("Search project", "搜索项目"),
    ("Search effects and presets", "搜索效果和预设"),
    ("Search timeline", "搜索时间轴"),
    ("Timeline", "时间轴"),
    ("Render Queue", "渲染队列"),
    ("Project", "项目"),
    ("Effect Controls", "效果控件"),
    ("Preview", "预览"),
    ("Properties", "属性"),
    ("Align", "对齐"),
    ("Audio", "音频"),
    ("Effects & Presets", "效果和预设"),
    ("Assets", "素材"),
    ("Composition", "合成"),
    ("Folder", "文件夹"),
    ("Solid", "纯色"),
    ("Video", "视频"),
    ("Audio Only", "仅音频"),
    ("Name", "名称"),
    ("Type", "类型"),
    ("Size", "大小"),
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("extra interface strings already translated")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"catalog anchor: expected 1, found {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + ROWS, 1), encoding="utf-8")
    print("project panel, timeline headers and empty states are Chinese now")


if __name__ == "__main__":
    main()
