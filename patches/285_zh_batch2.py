#!/usr/bin/env python3
"""汉化第二批：时间轴 / 图层面板 / 形状菜单（66 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH2_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("A/V Features", "音视频特性"),\n    ("Keys", "关键帧"),\n    ("Comment", "注释"),\n    ("Out", "输出"),\n    ("Video: shows or hides the layer\'s picture in the composition", "视频：显示或隐藏该图层在合成中的画面"),\n    ("Audio: turns the layer\'s sound on or off", "音频：打开或关闭该图层的声音"),\n    ("Lock: keeps the layer from being selected or changed", "锁定：使图层不能被选中或修改"),\n    ("Collapse Transformations / Continuously Rasterize", "塌陷变换 / 连续栅格化"),\n    ("Quality and Sampling", "品质与采样"),\n    ("Effect: turns the layer\'s effects on or off", "效果：打开或关闭该图层的效果"),\n    ("Frame Blending", "帧混合"),\n    ("Geometry Options", "几何选项"),\n    ("Drop footage to create a composition", "拖入素材以创建合成"),\n    ("Drag empty outline to select layers", "在空白外框拖动以选择图层"),\n    ("Graph Editor", "图表编辑器"),\n    ("Hides all layers for which the Shy switch is set", "隐藏所有开启了“害羞”开关的图层"),\n    ("Draft 3D", "草稿 3D"),\n    ("Time navigator", "时间导航条"),\n    ("Time navigator start", "时间导航条起点"),\n    ("Time navigator end", "时间导航条终点"),\n    ("Work area", "工作区"),\n    ("Source Name", "源名称"),\n    ("Mode", "模式"),\n    ("Track Matte", "轨道遮罩"),\n    ("Columns (right-click)", "列（右键）"),\n    ("Parent", "父级"),\n    ("Slip", "错移"),\n    ("Past the source", "超出源"),\n    ("Trim In", "入点裁剪"),\n    ("Trim Out", "出点裁剪"),\n    ("EffectControls", "效果控件"),\n    ("Expression field height", "表达式输入框高度"),\n    ("Add or remove keyframe", "添加或移除关键帧"),\n    ("Z Rotation", "Z 旋转"),\n    ("Select All Keyframes", "选择所有关键帧"),\n    ("Right-click to create a layer", "右键创建图层"),\n    ("Current time indicator", "当前时间指示器"),\n    ("Zoom Out (Time)", "时间缩小"),\n    ("Zoom In (Time)", "时间放大"),\n    ("Hand (hold Spacebar)", "抓手（按住空格）"),\n    ("Replace the layer\'s source", "替换图层源"),\n    ("Drop target layer", "拖放目标图层"),\n    ("Add a Dash or Gap", "添加虚线或间隙"),\n    ("Remove a Dash or Gap", "移除虚线或间隙"),\n    ("Group (empty)", "组（空）"),\n    ("Rectangle", "矩形"),\n    ("Polystar", "多边星形"),\n    ("Gradient Fill", "渐变填充"),\n    ("Gradient Stroke", "渐变描边"),\n    ("Merge Paths", "合并路径"),\n    ("Offset Paths", "偏移路径"),\n    ("Pucker & Bloat", "收缩和膨胀"),\n    ("Repeater", "中继器"),\n    ("Round Corners", "圆角"),\n    ("Trim Paths", "修剪路径"),\n    ("Twist", "扭转"),\n    ("Wiggle Paths", "摆动路径"),\n    ("Wiggle Transform", "摆动变换"),\n    ("Zig Zag", "锯齿"),\n    ("Animate:", "动画："),\n    ("Add property or selector", "添加属性或选择器"),\n    ("Animate text", "动画文字"),\n    ("Selector: Range", "选择器：范围"),\n    ("Selector: Wiggly", "选择器：摆动"),\n    ("Selector: Expression", "选择器：表达式"),\n    ("Link Channels", "链接通道"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 2 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH2_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 2 added")


if __name__ == "__main__":
    main()
