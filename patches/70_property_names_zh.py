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

        // Effect parameters (After Effects' Simplified Chinese wording).
        "Amount" => "数量",
        "Center" => "中心",
        "Direction" => "方向",
        "Random Seed" => "随机种子",
        "Radius" => "半径",
        "Feather" => "羽化",
        "Lightness" => "亮度",
        "Invert" => "反转",
        "Blend With Original" => "与原图像混合",
        "Blend w. Original" => "与原图像混合",
        "Contrast" => "对比度",
        "Saturation" => "饱和度",
        "Hue" => "色相",
        "Softness" => "柔和度",
        "Height" => "高度",
        "Width" => "宽度",
        "Size" => "大小",
        "Position" => "位置",
        "Brightness" => "亮度",
        "Rotation" => "旋转",
        "Channel" => "通道",
        "Threshold" => "阈值",
        "Final Output" => "最终输出",
        "Light Intensity" => "光照强度",
        "Light Color" => "光照颜色",
        "Light Direction" => "光照方向",
        "Light Height" => "光照高度",
        "Light Position" => "灯光位置",
        "Light Type" => "灯光类型",
        "Offset" => "偏移",
        "Intensity" => "强度",
        "Smooth" => "平滑",
        "Thickness" => "粗细",
        "Gamma" => "伽马",
        "Angle" => "角度",
        "Shutter Angle" => "快门角度",
        "Blend" => "混合",
        "Strength" => "强度",
        "Phase" => "相位",
        "Tolerance" => "容差",
        "Complexity" => "复杂度",
        "Evolution" => "演化",
        "Cycle Evolution" => "循环演化",
        "Ambient" => "环境光",
        "Diffuse" => "漫射",
        "Specular" => "高光",
        "Roughness" => "粗糙度",
        "Transition Completion" => "过渡完成",
        "Completion" => "完成度",
        "Gravity" => "重力",
        "X Speed" => "X 速度",
        "Y Speed" => "Y 速度",
        "Stroke Width" => "描边宽度",
        "Speed" => "速度",
        "Velocity" => "速度",
        "Method" => "方法",
        "Highlights" => "高光",
        "Shadows" => "阴影",
        "Midtones" => "中间调",
        "Scatter" => "散布",
        "Inside Color" => "内部颜色",
        "Outside Color" => "外部颜色",
        "Path" => "路径",
        "Stroke" => "描边",
        "Dry Out" => "干出",
        "Wet Out" => "湿出",
        "Mode" => "模式",
        "Repeat Edge Pixels" => "重复边缘像素",
        "Blur Dimensions" => "模糊维度",
        "Radius X" => "X 半径",
        "Radius Y" => "Y 半径",
        "Quality" => "品质",
        "Minimum" => "最小值",
        "Maximum" => "最大值",
        "Black Point" => "黑场",
        "White Point" => "白场",
        "Input Black" => "输入黑场",
        "Input White" => "输入白场",
        "Output Black" => "输出黑场",
        "Output White" => "输出白场",
        "Matching Tolerance" => "匹配容差",
        "Matching Softness" => "匹配柔和度",
        "Density" => "密度",
        "Slant" => "斜体",
        "Noise" => "杂色",
        "Start" => "开始",
        "End" => "结束",
        "Warp" => "变形",
        "Turbulence" => "湍流",
        "Reflection" => "反射",
        "Brush Size" => "画笔大小",
        "Key Color" => "键控颜色",
        "Screen Matte" => "屏幕遮罩",
        "Reduce Chatter" => "减少抖动",
        "Inside Mask" => "内部遮罩",
        "Shift Edge" => "移动边缘",
        "Blending Matte" => "混合遮罩",
        "Display Options" => "显示选项",
        "Gain" => "增益",
        "Decay" => "衰减",
        "Level" => "级别",
        "Horizontal and Vertical" => "水平和垂直",
        "Roundness" => "圆度",
        "X Position" => "X 位置",
        "Y Position" => "Y 位置",
        "Z Position" => "Z 位置",
        "Max RGB" => "最大 RGB",
        "Source Layer" => "源图层",
        "Operator" => "运算符",
        "Object ID" => "对象 ID",
        "Material ID" => "材质 ID",
        "Colors" => "颜色",
        "Depth" => "深度",
        "Curves" => "曲线",
        "Exposure" => "曝光",
        "Sharpen" => "锐化",
        "Vibrance" => "自然饱和度",
        "Blur" => "模糊",
        "Tint Color" => "色调颜色",
        "Fill" => "填充",
        "Clamp" => "钳制",
        "Environment Map" => "环境贴图",
        "Tint" => "色调",
        "Key Layer Density" => "关键层密度",
        "Offset Darks" => "暗部偏移",
        "Show" => "显示",
        "Glow" => "辉光",
        "Glow Width" => "辉光宽度",
        "Glow Color" => "辉光颜色",
        "Glow From Alpha" => "从 Alpha 取辉光",
        "Glow Under Source" => "辉光在源下方",
        "Shadow Color" => "投影颜色",
        "Rays Brightness" => "光线亮度",
        "Light Rays|Dark Rays" => "亮光|暗光",
        "Center X" => "X 中心",
        "Center Y" => "Y 中心",
        "Length" => "长度",
        "Frequency" => "频率",
        "Detail" => "细节",
        "Distance" => "距离",
        "Mask Use" => "蒙版用法",
        "Show Mocha Only" => "仅显示 Mocha",
        "Grain Amp" => "颗粒振幅",
        "Grain Blur" => "颗粒模糊",
        "Grain Size" => "颗粒大小",
        "Viewing Distance" => "观看距离",
        "Blur Focal Distance" => "模糊焦距",
        "Iris Shape" => "光圈形状",
        "Iris Rotation" => "光圈旋转",
        "Specular Highlight" => "高光",
        "Bounce" => "反弹",
        "Height Map" => "高度贴图",
        "Samples" => "采样数",
        "Iterations" => "迭代次数",
        "Seed" => "种子",
        "Angle of View" => "视角",
        "Zoom" => "缩放",
        "Focus Distance" => "对焦距离",
        "Aperture" => "光圈",
        "Blend With" => "混合方式",
        "Channels" => "通道",
        "Curve" => "曲线",
        "Layer Transform" => "图层变换",
        "Anchor Point" => "锚点",
        "Scale" => "缩放",
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
