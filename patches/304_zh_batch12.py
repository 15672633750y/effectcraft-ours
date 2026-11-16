#!/usr/bin/env python3
"""效果参数名第四批：130 条，全部走 `i18n/ui.rs` 的 SIMPLIFIED_CHINESE 表。

效果参数名现在也查这张表：`zzzzzzzzzzzzzzzzz_zh_prop_fallback.py` 把 `prop::name` 的兜底
（`other => other`）改成查表，所以参数名和界面文字共用同一张表、同一条插入锚点。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH12_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH12_V1 — 效果参数名第四批
    ("Master Lightness", "主明度"),
    ("Colorize Hue", "着色色相"),
    ("Colorize Saturation", "着色饱和度"),
    ("Colorize Lightness", "着色明度"),
    ("Don't Clip", "不裁切"),
    ("Bypass Linear Light Conversion", "绕过线性光转换"),
    ("Reds", "红色"),
    ("Yellows", "黄色"),
    ("Greens", "绿色"),
    ("Cyans", "青色"),
    ("Blues", "蓝色"),
    ("Magentas", "洋红"),
    ("Fill Mask", "填充遮罩"),
    ("All Masks", "所有遮罩"),
    ("Horizontal Feather", "水平羽化"),
    ("Vertical Feather", "垂直羽化"),
    ("Change", "变化"),
    ("Change By", "变化量"),
    ("View Correction Matte", "查看校正遮罩"),
    ("Amount to Decolor", "去色量"),
    ("Color To Leave", "保留的颜色"),
    ("Filter", "滤镜"),
    ("Monochrome", "单色"),
    ("Get Phase From", "相位来源"),
    ("Add Phase", "添加相位"),
    ("Add Phase From", "添加相位来源"),
    ("Add Mode", "添加方式"),
    ("Phase Shift", "相位偏移"),
    ("Use Preset Palette", "使用预设调色板"),
    ("Output Cycle", "输出循环"),
    ("Cycle Repetitions", "循环次数"),
    ("Interpolate Palette", "插值调色板"),
    ("Modify", "修改"),
    ("Modify Alpha", "修改 Alpha"),
    ("Change Empty Pixels", "改变空白像素"),
    ("Matching Color", "匹配颜色"),
    ("Matching Mode", "匹配方式"),
    ("Mask Layer", "遮罩图层"),
    ("Masking Mode", "遮罩方式"),
    ("Composite Over Layer", "在图层上合成"),
    ("Slider", "滑块"),
    ("Checkbox", "复选框"),
    ("Point", "点"),
    ("3D Point", "3D 点"),
    ("Menu", "菜单"),
    ("Configuration", "配置"),
    ("Stereo Scene Depth", "立体场景深度"),
    ("Enable Convergence", "启用会聚"),
    ("Convergence Of", "会聚于"),
    ("Convergence Z Offset", "会聚 Z 偏移"),
    ("Center of Sphere", "球心"),
    ("Horizontal Radius", "水平半径"),
    ("Vertical Radius", "垂直半径"),
    ("Bulge Center", "凸起中心"),
    ("Bulge Height", "凸起高度"),
    ("Taper Radius", "锥化半径"),
    ("Pin All Edges", "固定所有边缘"),
    ("Center of Ripple", "波纹中心"),
    ("Ripple Phase", "波纹相位"),
    ("Reflection Center", "反射中心"),
    ("Reflection Angle", "反射角度"),
    ("Shift Center To", "中心移到"),
    ("Interpolation", "插值"),
    ("Uniform Scale", "等比缩放"),
    ("Use Composition's Shutter Angle", "使用合成的快门角度"),
    ("Sampling", "采样"),
    ("Upper Left", "左上"),
    ("Upper Right", "右上"),
    ("Lower Left", "左下"),
    ("Lower Right", "右下"),
    ("Displacement Map Layer", "置换图图层"),
    ("Displacement Map Layer Source", "置换图图层来源"),
    ("Use For Horizontal Displacement", "用于水平置换"),
    ("Max Horizontal Displacement", "最大水平置换"),
    ("Use For Vertical Displacement", "用于垂直置换"),
    ("Max Vertical Displacement", "最大垂直置换"),
    ("Displacement Map Behavior", "置换图行为"),
    ("Wrap Pixels Around", "环绕像素"),
    ("Expand Output", "扩展输出"),
    ("Field Of View (FOV)", "视野（FOV）"),
    ("Reverse Lens Distortion", "反转镜头畸变"),
    ("FOV Orientation", "视野方向"),
    ("View Center", "视图中心"),
    ("Optimal Pixels (Invalidates Resize)", "最佳像素（会使调整大小失效）"),
    ("Resize", "调整大小"),
    ("Magnification", "放大率"),
    ("Link", "链接"),
    ("Scaling", "缩放"),
    ("Top Left Vertex", "左上顶点"),
    ("Top Left Tangent", "左上切线"),
    ("Top Right Tangent", "右上切线"),
    ("Right Top Vertex", "右上顶点"),
    ("Right Top Tangent", "右上切线"),
    ("Right Bottom Tangent", "右下切线"),
    ("Bottom Right Vertex", "右下顶点"),
    ("Bottom Right Tangent", "右下切线"),
    ("Bottom Left Tangent", "左下切线"),
    ("Left Bottom Vertex", "左下顶点"),
    ("Left Bottom Tangent", "左下切线"),
    ("Left Top Tangent", "左上切线"),
    ("Render Prestart", "预渲染起始"),
    ("Convergence", "会聚"),
    ("Fold Position", "折叠位置"),
    ("Fold Direction", "折叠方向"),
    ("Fold Radius", "折叠半径"),
    ("Back Opacity", "背面不透明度"),
    ("Paper Color", "纸张颜色"),
    ("Tile Size", "拼贴大小"),
    ("Cut Tiles", "裁切拼贴"),
    ("Style", "样式"),
    ("Adjust To Distance", "按距离调整"),
    ("Base", "基色"),
    ("Blob Layer", "斑点图层"),
    ("Cut Away", "切掉"),
    ("Top Left", "左上"),
    ("Top Right", "右上"),
    ("Bottom Left", "左下"),
    ("Bottom Right", "右下"),
    ("Perspective", "透视"),
    ("Unstretch", "取消拉伸"),
    ("Pulse Level (animate)", "脉冲强度（动画）"),
    ("Time Span (sec)", "时间跨度（秒）"),
    ("Render Bump As Well", "同时渲染凹凸"),
    ("Stretching", "拉伸"),
    ("Floor", "地面"),
    ("Reach", "触及范围"),
    ("Split", "分割"),
    ("Split 1", "分割 1"),
    ("Split 2", "分割 2"),
    ("Mask Offset", "遮罩偏移"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("304_zh_batch12.py already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH12_V1", 1)
    path.write_text(src, encoding="utf-8")
    print("304_zh_batch12.py added")


if __name__ == "__main__":
    main()
