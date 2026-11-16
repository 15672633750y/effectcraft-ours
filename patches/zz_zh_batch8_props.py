#!/usr/bin/env python3
"""汉化第八批：效果控件/时间轴里的参数名（约 110 条，按出现次数取最常用的一批）。

效果参数名不走 `i18n/ui.rs` 的表，而是走 `i18n/prop.rs` 的 match（效果控件行、属性面板行、
时间轴属性行、拖拽提示都用它）。所以这一批补在 prop.rs 的 `other => other` 之前。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH8_V1"

ANCHOR = "        other => other,"

ROWS = """        // EFFECTCRAFT_OURS_ZH_BATCH8_V1 — 效果参数名（按需补，越常用越靠前）
        "Blending Mode" => "混合模式",
        "View" => "视图",
        "Render" => "渲染",
        "Type" => "类型",
        "Layer" => "图层",
        "Edge Softness" => "边缘柔和度",
        "Cycle (in Revolutions)" => "循环（转数）",
        "Property" => "属性",
        "From" => "自",
        "To" => "至",
        "Gradient Layer" => "渐变图层",
        "Overflow" => "溢出",
        "Invert Mask" => "反转遮罩",
        "Detailed Analysis" => "详细分析",
        "Pinning" => "固定",
        "Resize Layer" => "调整图层大小",
        "Top" => "顶部",
        "Point A" => "A 点",
        "Point B" => "B 点",
        "Border" => "边框",
        "Composite On Original" => "合成到原图",
        "Glow Radius" => "辉光半径",
        "Fractal Type" => "分形类型",
        "Edge Thickness" => "边缘厚度",
        "Edge Thin" => "边缘变细",
        "Edge Feather" => "边缘羽化",
        "Blurriness" => "模糊度",
        "Viewing Mode" => "查看模式",
        "Operate On Alpha Channel" => "作用于 Alpha 通道",
        "Rotate" => "旋转",
        "Smoothness" => "平滑度",
        "Fill Color" => "填充颜色",
        "Stroke Color" => "描边颜色",
        "Tracking" => "跟踪",
        "Reverse Transition" => "反向过渡",
        "Blur Mask" => "模糊遮罩",
        "Threshold (dB)" => "阈值（dB）",
        "Attack (ms)" => "起音（毫秒）",
        "Release (ms)" => "释放（毫秒）",
        "Modulation Rate" => "调制速率",
        "Invert Phase" => "反转相位",
        "Colorize" => "着色",
        "Blur Radius" => "模糊半径",
        "Aspect Ratio" => "宽高比",
        "Transfer Mode" => "转换模式",
        "Show Track Points" => "显示跟踪点",
        "Track Point Size" => "跟踪点大小",
        "Hide Warning Banner" => "隐藏警告横幅",
        "Focal Length" => "焦距",
        "Clip Result Values" => "钳制结果值",
        "Background Color" => "背景颜色",
        "If Layer Sizes Differ" => "图层大小不同时",
        "Invert Input" => "反转输入",
        "Composite Original" => "与原图合成",
        "Display" => "显示",
        "Clip" => "裁剪",
        "Clip To Output Black" => "钳制到输出黑场",
        "Clip To Output White" => "钳制到输出白场",
        "Temporal Smoothing (seconds)" => "时间平滑（秒）",
        "Scene Detect" => "场景检测",
        "Black Clip" => "黑场裁切",
        "White Clip" => "白场裁切",
        "Brights" => "亮部",
        "Temperature" => "色温",
        "Midpoint" => "中间点",
        "Match Colors" => "匹配颜色",
        "Preserve Luminosity" => "保持明度",
        "Twirl Radius" => "扭转半径",
        "Twirl Center" => "扭转中心",
        "Wave Type" => "波浪类型",
        "Wave Height" => "波浪高度",
        "Wave Width" => "波浪宽度",
        "Wave Speed" => "波浪速度",
        "Type of Conversion" => "转换类型",
        "Scale Height" => "缩放高度",
        "Scale Width" => "缩放宽度",
        "Displacement" => "置换",
        "Offset (Turbulence)" => "偏移（湍流）",
        "Rows" => "行数",
        "Columns" => "列数",
        "Distortion Mesh" => "变形网格",
        "Bend" => "弯曲",
        "Horizontal Scale" => "水平缩放",
        "Vertical Scale" => "垂直缩放",
        "Metal" => "金属",
        "Left" => "左",
        "Right" => "右",
        "Bottom" => "底部",
        "Amplitude" => "振幅",
        "Source Mask" => "源遮罩",
        "Boundary Mask" => "边界遮罩",
        "Percent" => "百分比",
        "Elasticity" => "弹性",
        "Interpolation Method" => "插值方式",
        "Anchor" => "锚点",
        "Size From" => "尺寸来源",
        "Corner" => "角",
        "Color from Source" => "颜色取自源",
        "Screen Colour" => "屏幕颜色",
        "Screen Gain" => "屏幕增益",
        "Screen Balance" => "屏幕平衡",
        "Screen Pre-blur" => "屏幕预模糊",
        "Screen Shrink/Grow" => "屏幕收缩/扩张",
        "Screen Softness" => "屏幕柔和度",
        "Edge Colour" => "边缘颜色",
        "Suppression" => "抑制",
        "Additional Edge Radius" => "额外边缘半径",
        "Alpha Contrast" => "Alpha 对比度",
        "Replace Method" => "替换方式",
        "Replace Colour" => "替换颜色",
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/prop.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 8 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("batch 8 added")


if __name__ == "__main__":
    main()
