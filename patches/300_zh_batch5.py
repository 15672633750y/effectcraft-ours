#!/usr/bin/env python3
"""汉化第五批：命令名 / 面板提示 / 颜色与主题菜单（约 70 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH5_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("Eyedropper", "吸管"),\n    ("Color field", "颜色输入框"),\n    ("Color slider", "颜色滑块"),\n    ("New color", "新颜色"),\n    ("Original color", "原始颜色"),\n    ("Physical+", "物理+"),\n    ("Username", "用户名"),\n    ("Commits", "提交"),\n    ("Company", "公司"),\n    ("Version", "版本"),\n    ("History", "历史"),\n    ("More compositions", "更多合成"),\n    ("Composition Intro", "合成开场"),\n    ("Effect Controls Title", "效果控件标题"),\n    ("Properties: Title", "属性：标题"),\n    ("Move panel group", "移动面板组"),\n    ("More tabs", "更多标签"),\n    ("Move floating panel", "移动浮动面板"),\n    ("Close floating panel", "关闭浮动面板"),\n    ("Resize floating panel", "调整浮动面板大小"),\n    ("Hidden expression", "隐藏的表达式"),\n    ("Solo plate", "单独显示底板"),\n    ("Workspaces", "工作区"),\n    ("Expansion:", "扩展："),\n    ("Density:", "密度："),\n    ("Follow-Through...", "跟随…"),\n    ("Polygon", "多边形"),\n    ("Lifecycle", "生命周期"),\n    ("My Layout", "我的布局"),\n    ("Hide Shy Layers", "隐藏害羞图层"),\n    ("Enable Frame Blending", "启用帧混合"),\n    ("Enable Motion Blur", "启用运动模糊"),\n    ("Draft 3D", "草稿 3D"),\n    ("Available", "可用"),\n    ("Missing", "缺失"),\n    ("Regular", "常规"),\n    ("Hot text", "高亮文字"),\n    ("The script render waiter is unavailable.", "脚本渲染等待器不可用。"),\n    ("GPU compositor unavailable: the window has no wgpu device", "GPU 合成不可用：窗口没有 wgpu 设备"),\n    ("Recovery", "恢复"),\n    ("Renamed", "已重命名"),\n    ("Underlay", "底层"),\n    ("Inner solid", "内部纯色"),\n    ("Audio Layer", "音频图层"),\n    ("Time Remap", "时间重映射"),\n    ("Controls", "控件"),\n    ("Docking Action", "停靠操作"),\n    ("Preview (Numpad 0)", "预览（小键盘 0）"),\n    ("Preview (Shift+Spacebar)", "预览（Shift+空格）"),\n    ("Next Composition in Viewer", "预演中的下一个合成"),\n    ("Previous Composition in Viewer", "预演中的上一个合成"),\n    ("Move Selected Layers Up 1 Pixel at Current Magnification", "按当前缩放将所选图层上移 1 像素"),\n    ("Move Selected Layers Down 1 Pixel at Current Magnification", "按当前缩放将所选图层下移 1 像素"),\n    ("Move Selected Layers Left 1 Pixel at Current Magnification", "按当前缩放将所选图层左移 1 像素"),\n    ("Move Selected Layers Right 1 Pixel at Current Magnification", "按当前缩放将所选图层右移 1 像素"),\n    ("Move Selected Layers Up 10 Pixels at Current Magnification", "按当前缩放将所选图层上移 10 像素"),\n    ("Move Selected Layers Down 10 Pixels at Current Magnification", "按当前缩放将所选图层下移 10 像素"),\n    ("Move Selected Layers Left 10 Pixels at Current Magnification", "按当前缩放将所选图层左移 10 像素"),\n    ("Move Selected Layers Right 10 Pixels at Current Magnification", "按当前缩放将所选图层右移 10 像素"),\n    ("Transparency Grid", "透明网格"),\n    ("Next Appearance Mode", "下一个外观模式"),\n    ("Theme: Dark", "主题：深色"),\n    ("Theme: Darker", "主题：更暗"),\n    ("Theme: Light", "主题：浅色"),\n    ("Zoom In Time", "时间放大"),\n    ("Zoom Out Time", "时间缩小"),\n    ("Zoom to Fit Comp", "缩放以适合合成"),\n    ("Scroll to Current Time", "滚动到当前时间"),\n    ("Scroll Topmost Selected Layer to Top", "将最上面的所选图层滚到顶部"),\n    ("Show/Hide Parent Column", "显示/隐藏父级列"),\n    ("Zoom In to Frame Level / Out to the Whole Comp", "放大到帧级 / 缩小到整个合成"),\n    ("Graph Editor", "图表编辑器"),\n    ("Set Work Area Begin", "设置工作区起点"),\n    ("Set Work Area End", "设置工作区终点"),\n    ("Move Layer In Point to Current Time", "将图层入点移到当前时间"),\n    ("Move Layer Out Point to Current Time", "将图层出点移到当前时间"),\n    ("Trim Layer In Point to Current Time", "将图层入点裁剪到当前时间"),\n    ("Trim Layer Out Point to Current Time", "将图层出点裁剪到当前时间"),\n    ("Rectangle Path 1", "矩形路径 1"),\n    ("Ellipse Path 1", "椭圆路径 1"),\n    ("Polystar Path 1", "多边星形路径 1"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 5 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH5_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 5 added")


if __name__ == "__main__":
    main()
