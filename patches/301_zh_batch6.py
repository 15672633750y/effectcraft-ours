#!/usr/bin/env python3
"""汉化第六批：展开/添加属性命令、工具栏、面板命令（约 60 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH6_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("Reveal Position", "展开位置"),\n    ("Reveal Scale", "展开缩放"),\n    ("Reveal Rotation", "展开旋转"),\n    ("Reveal Opacity", "展开不透明度"),\n    ("Reveal Anchor Point", "展开锚点"),\n    ("Reveal Effects", "展开效果"),\n    ("Reveal Masks", "展开蒙版"),\n    ("Reveal Mask Feather", "展开蒙版羽化"),\n    ("Reveal Audio Levels (press twice: Waveform)", "展开音频电平（按两次：波形）"),\n    ("Reveal Time Remap", "展开时间重映射"),\n    ("Reveal Expressions", "展开表达式"),\n    ("Reveal Mask Opacity", "展开蒙版不透明度"),\n    ("Reveal Mask Path", "展开蒙版路径"),\n    ("Reveal Material Options", "展开材质选项"),\n    ("Reveal Paint, Roto Brush and Puppet", "展开绘画、Roto 画笔与木偶"),\n    ("Reveal Selected Properties", "展开所选属性"),\n    ("Reveal Missing Effects", "展开缺失的效果"),\n    ("Reveal Audio Waveform", "展开音频波形"),\n    ("Add Position to Revealed Properties", "将位置加入已展开属性"),\n    ("Add Scale to Revealed Properties", "将缩放加入已展开属性"),\n    ("Add Rotation to Revealed Properties", "将旋转加入已展开属性"),\n    ("Add Opacity to Revealed Properties", "将不透明度加入已展开属性"),\n    ("Add Anchor Point to Revealed Properties", "将锚点加入已展开属性"),\n    ("Add Effects to Revealed Properties", "将效果加入已展开属性"),\n    ("Add Masks to Revealed Properties", "将蒙版加入已展开属性"),\n    ("Add Mask Feather to Revealed Properties", "将蒙版羽化加入已展开属性"),\n    ("Add Audio Levels to Revealed Properties", "将音频电平加入已展开属性"),\n    ("Add Animated Properties to Revealed Properties", "将动画属性加入已展开属性"),\n    ("Show/Hide Timeline Column", "显示/隐藏时间轴列"),\n    ("Source Name / Layer Name", "源名称 / 图层名称"),\n    ("Search Timeline", "搜索时间轴"),\n    ("Flowchart Options", "流程图选项"),\n    ("Flowchart Graph", "流程图"),\n    ("Collapse All", "全部折叠"),\n    ("Twirl Selected Layers Open / Closed", "展开/收起所选图层"),\n    ("Add or Remove Anchor Point Keyframe", "添加或移除锚点关键帧"),\n    ("Add or Remove Position Keyframe", "添加或移除位置关键帧"),\n    ("Add or Remove Scale Keyframe", "添加或移除缩放关键帧"),\n    ("Add or Remove Rotation Keyframe", "添加或移除旋转关键帧"),\n    ("Add or Remove Opacity Keyframe", "添加或移除不透明度关键帧"),\n    ("Orbit Tool", "环绕工具"),\n    ("Pan Camera Tool", "平移摄像机工具"),\n    ("Dolly Tool", "推拉工具"),\n    ("Camera Tools", "摄像机工具"),\n    ("Pan Behind Tool", "定位点工具"),\n    ("Shape Tools", "形状工具"),\n    ("Type Tools", "文字工具"),\n    ("Brush Tools", "画笔工具"),\n    ("Roto Brush & Refine Edge Tools", "Roto 画笔与细化边缘工具"),\n    ("Puppet Tools", "木偶工具"),\n    ("New Solid...", "新建纯色…"),\n    ("Marker Settings...", "标记设置…"),\n    ("Maximize Panel Under Pointer", "最大化指针下的面板"),\n    ("Maximize or Restore Application Window", "最大化或还原窗口"),\n    ("Switch Between Composition and Timeline Panel", "在合成与时间轴面板间切换"),\n    ("Next Panel in Frame", "框中的下一个面板"),\n    ("Previous Panel in Frame", "框中的上一个面板"),\n    ("Close Panel or All Viewers", "关闭面板或所有预演"),\n    ("Dock Panel", "停靠面板"),\n    ("Can\'t Undo", "无法撤销"),\n    ("Can\'t Redo", "无法重做"),\n    ("Project clipboard actions are not supported yet", "工程剪贴板操作暂不支持"),\n    ("From Script", "来自脚本"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 6 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH6_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 6 added")


if __name__ == "__main__":
    main()
