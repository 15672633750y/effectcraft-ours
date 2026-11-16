#!/usr/bin/env python3
"""汉化第七批：对话框标题、动画工具标签、路径/摄像机工具、预演与工程命令（85 条）。

这些行多数由 302 以外的「绘制路由」补丁（zzzzzzzzzzzzzzzz_zh_draw_routes.py）取用：
那批控件把字符串原样画到 painter 上，不查表，所以这里先把中文补进表，再让控件查表。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH7_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    ("% of all commits", "占全部提交"),
    ("Lines +/−", "增删行数"),
    ("A null moving along the path, driven by its Progress slider", "空对象沿路径移动，由「进度」滑块驱动"),
    ("A null on each vertex that follows the (animated) path", "每个顶点上一个空对象，跟随（动画的）路径"),
    ("Add Mask Shape Vertices", "添加蒙版形状顶点"),
    ("Add Parameter", "添加参数"),
    ("Adjust composition duration", "调整合成时长"),
    ("All Panels", "所有面板"),
    ("Bending Resistance:", "弯曲阻力："),
    ("By {by}", "作者 {by}"),
    ("Camera Settings", "摄像机设置"),
    ("Clamp Signal", "钳制信号"),
    ("Composition Settings...", "合成设置…"),
    ("Continuous", "连续"),
    ("Copy Frame to Clipboard", "复制帧到剪贴板"),
    ("Create Multiple Nulls and Camera", "创建多个空对象与摄像机"),
    ("Create Multiple Solids and Camera", "创建多个纯色层与摄像机"),
    ("Create Multiple Text Layers and Camera", "创建多个文本图层与摄像机"),
    ("Delete Items", "删除项目"),
    ("Delete Template", "删除模板"),
    ("Dimension:", "尺寸："),
    ("Easy Ease In", "缓入"),
    ("Easy Ease Out", "缓出"),
    ("Edit Workspaces...", "编辑工作区…"),
    ("Font Control", "字体控制"),
    ("Frequency:", "频率："),
    ("Gradient", "渐变"),
    ("Incoming Velocity", "进入速度"),
    ("Keyboard Shortcuts", "键盘快捷键"),
    ("Keyframe Interpolation", "关键帧插值"),
    ("Layer In-point", "图层入点"),
    ("Layer Out-point", "图层出点"),
    ("Leave all attributes", "保留全部属性"),
    ("Light Settings", "灯光设置"),
    ("Location", "位置"),
    ("Magnitude:", "强度："),
    ("Matching Method:", "匹配方式："),
    ("Media only", "仅媒体"),
    ("Motion Tracking", "运动跟踪"),
    ("Move all attributes", "移动全部属性"),
    ("Move time to preview time", "将时间移到预演时间"),
    ("Mute Keyframes", "静音关键帧"),
    ("New 3D Primitive", "新建 3D 对象"),
    ("New Composition...", "新建合成…"),
    ("New Viewer", "新建预演"),
    ("New composition name", "新合成名称"),
    ("Nulls Follow Points", "空对象跟随顶点"),
    ("Outgoing Velocity", "离开速度"),
    ("Pan", "平移"),
    ("Pause", "暂停"),
    ("Points Follow Nulls", "顶点跟随空对象"),
    ("Preview (Alt+Numpad 0)", "预览（Alt+小键盘 0）"),
    ("Preview (Shift+Numpad 0)", "预览（Shift+小键盘 0）"),
    ("Proxy: {} ({})", "代理：{}（{}）"),
    ("Quality:", "质量："),
    ("Range:", "范围："),
    ("Roll", "滚转"),
    ("Save Changes to this Workspace", "保存对此工作区的更改"),
    ("Save as New Workspace...", "另存为新工作区…"),
    ("Save from item", "从项目项保存"),
    ("Show Grid", "显示网格"),
    ("Show Selected Properties (else all animated properties)", "显示所选属性（否则显示全部动画属性）"),
    ("Smoothing:", "平滑："),
    ("The script will continue when rendering finishes. Editing is paused to preserve its undo group.", "渲染结束后脚本会继续。为保住撤销分组，编辑已暂停。"),
    ("Tilt", "俯仰"),
    ("Time Stretch", "时间伸缩"),
    ("Tolerance:", "容差："),
    ("Trace Path", "追踪路径"),
    ("Undocked Panels", "已取消停靠的面板"),
    ("Uniform Scale", "等比缩放"),
    ("Un-precompose", "取消预合成"),
    ("Unmute Keyframes", "取消关键帧静音"),
    ("Version {}  •  Motion graphics & VFX in pure Rust", "版本 {}  •  纯 Rust 实现的动态图形与视觉特效"),
    ("View Options…", "视图选项…"),
    ("Watch Folder: rendered {n} project(s)", "监视文件夹：已渲染 {n} 个项目"),
    ("Workspace changes couldn't be saved and may be lost after a restart: {error}", "工作区更改没能保存，重启后可能丢失：{error}"),
    ("less than a minute ago", "不到一分钟前"),
    ("A null on each vertex; move the nulls to reshape the path", "每个顶点上一个空对象；拖动空对象重塑路径"),
    ("Delete Selected Points", "删除所选点"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 7 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH7_V1", 1)
    path.write_text(src, encoding="utf-8")
    print("batch 7 added")


if __name__ == "__main__":
    main()
