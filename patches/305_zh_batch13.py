#!/usr/bin/env python3
"""效果参数名第五批：140 条，全部走 `i18n/ui.rs` 的 SIMPLIFIED_CHINESE 表。

效果参数名现在也查这张表：`zzzzzzzzzzzzzzzzz_zh_prop_fallback.py` 把 `prop::name` 的兜底
（`other => other`）改成查表，所以参数名和界面文字共用同一张表、同一条插入锚点。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH13_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH13_V1 — 效果参数名第五批
    ("Mask Rotation", "遮罩旋转"),
    ("Mask Scale", "遮罩缩放"),
    ("Destination Mask", "目标遮罩"),
    ("Correspondence Points", "对应点"),
    ("Warp Style", "变形样式"),
    ("Warp Axis", "变形轴"),
    ("Horizontal Distortion", "水平扭曲"),
    ("Vertical Distortion", "垂直扭曲"),
    ("Reduce Noise", "降噪"),
    ("Alpha", "Alpha"),
    ("Knot 1", "节点 1"),
    ("Amount 1", "数量 1"),
    ("Knot 2", "节点 2"),
    ("Amount 2", "数量 2"),
    ("Tile Edges", "平铺边缘"),
    ("Antialiasing", "抗锯齿"),
    ("Falloff", "衰减"),
    ("Tool", "工具"),
    ("Brush Pressure", "画笔压力"),
    ("Freeze Area Mask", "冻结区域遮罩"),
    ("Turbulent Jitter", "湍流抖动"),
    ("Clone Offset", "克隆偏移"),
    ("Reconstruction Mode", "重建模式"),
    ("View Freeze Area Mask", "查看冻结区域遮罩"),
    ("View Mesh", "查看网格"),
    ("Mesh Size", "网格大小"),
    ("Mesh Color", "网格颜色"),
    ("Distortion Mesh Offset", "变形网格偏移"),
    ("Distortion Percentage", "变形百分比"),
    ("Distortion Display Quality", "变形显示质量"),
    ("Rolling Shutter Rate", "卷帘快门速率"),
    ("Scan Direction", "扫描方向"),
    ("Pixel Motion Detail", "像素运动细节"),
    ("Start of Ramp", "渐变起点"),
    ("Start Color", "起始颜色"),
    ("End of Ramp", "渐变终点"),
    ("End Color", "结束颜色"),
    ("Ramp Shape", "渐变形状"),
    ("Ramp Scatter", "渐变散开"),
    ("Point 1", "点 1"),
    ("Color 1", "颜色 1"),
    ("Point 2", "点 2"),
    ("Color 2", "颜色 2"),
    ("Point 3", "点 3"),
    ("Color 3", "颜色 3"),
    ("Point 4", "点 4"),
    ("Color 4", "颜色 4"),
    ("Jitter", "抖动"),
    ("Invert Grid", "反转网格"),
    ("Edge", "边缘"),
    ("Edge Radius", "边缘半径"),
    ("Feather Outer Edge", "羽化外边缘"),
    ("Feather Inner Edge", "羽化内边缘"),
    ("Invert Circle", "反转圆形"),
    ("Cell Pattern", "单元格图案"),
    ("Disperse", "分散"),
    ("Enable Tiling", "启用平铺"),
    ("Cells Horizontal", "水平单元格"),
    ("Cells Vertical", "垂直单元格"),
    ("Flare Center", "光晕中心"),
    ("Flare Brightness", "光晕亮度"),
    ("Lens Type", "镜头类型"),
    ("Starting Point", "起点"),
    ("Ending Point", "终点"),
    ("Time", "时间"),
    ("Starting Thickness", "起始粗细"),
    ("Ending Thickness", "结束粗细"),
    ("3D Perspective", "3D 透视"),
    ("Producer Point", "生成点"),
    ("Parameters Are Set At", "参数设置于"),
    ("Render Quality", "渲染质量"),
    ("Sides", "边数"),
    ("Star", "星形"),
    ("Star Depth", "星形深度"),
    ("Source Center", "源中心"),
    ("Value Channel", "值通道"),
    ("Value Threshold", "值阈值"),
    ("Pre-Blur", "预模糊"),
    ("Contour", "轮廓"),
    ("Expansion", "扩展"),
    ("Spin", "旋转速度"),
    ("Lifespan (sec)", "生命周期（秒）"),
    ("Profile", "剖面"),
    ("Fade-in Time", "淡入时间"),
    ("Fade-out Time", "淡出时间"),
    ("Start Width", "起始宽度"),
    ("End Width", "结束宽度"),
    ("Lightning Type", "闪电类型"),
    ("Origin", "原点"),
    ("Conductivity State", "传导状态"),
    ("Core Radius", "核心半径"),
    ("Core Opacity", "核心不透明度"),
    ("Core Color", "核心颜色"),
    ("Glow Opacity", "辉光不透明度"),
    ("Forking", "分叉"),
    ("Decay Main Core", "主核心衰减"),
    ("Alpha Obstacle", "Alpha 障碍"),
    ("Min Fork Distance", "最小分叉距离"),
    ("Termination Threshold", "终止阈值"),
    ("Main Core Collision Only", "仅主核心碰撞"),
    ("Core Drain", "核心消耗"),
    ("Fork Strength", "分叉强度"),
    ("Fork Variation", "分叉变化"),
    ("Warp Softness", "变形柔和度"),
    ("Ray Length", "光线长度"),
    ("Burst", "爆发"),
    ("Set Color", "设置颜色"),
    ("Sweep Intensity", "扫光强度"),
    ("Edge Intensity", "边缘强度"),
    ("Light Reception", "光照接收"),
    ("Match colors", "匹配颜色"),
    ("Key Operation", "抠像操作"),
    ("Color Tolerance", "颜色容差"),
    ("Key Type", "抠像类型"),
    ("Color Matching Accuracy", "颜色匹配精度"),
    ("Partial A In Black", "部分 A 输入黑场"),
    ("Partial A In White", "部分 A 输入白场"),
    ("Partial A Gamma", "部分 A 灰度系数"),
    ("Partial A Out Black", "部分 A 输出黑场"),
    ("Partial A Out White", "部分 A 输出白场"),
    ("Partial B In Black", "部分 B 输入黑场"),
    ("Partial B In White", "部分 B 输入白场"),
    ("Partial B Gamma", "部分 B 灰度系数"),
    ("Partial B Out Black", "部分 B 输出黑场"),
    ("Partial B Out White", "部分 B 输出白场"),
    ("Matte In Black", "遮罩输入黑场"),
    ("Matte In White", "遮罩输入白场"),
    ("Matte Gamma", "遮罩灰度系数"),
    ("Fuzziness", "模糊度"),
    ("Color Space", "色彩空间"),
    ("Min (L, Y, R)", "最小（L、Y、R）"),
    ("Max (L, Y, R)", "最大（L、Y、R）"),
    ("Min (a, U, G)", "最小（a、U、G）"),
    ("Max (a, U, G)", "最大（a、U、G）"),
    ("Min (b, V, B)", "最小（b、V、B）"),
    ("Max (b, V, B)", "最大（b、V、B）"),
    ("Black Softness", "黑场柔和度"),
    ("White Softness", "白场柔和度"),
    ("Despill", "去溢色"),
    ("Clip Black", "裁切黑场"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("305_zh_batch13.py already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH13_V1", 1)
    path.write_text(src, encoding="utf-8")
    print("305_zh_batch13.py added")


if __name__ == "__main__":
    main()
