#!/usr/bin/env python3
"""效果参数名第三批：116 条，全部走 `i18n/ui.rs` 的 SIMPLIFIED_CHINESE 表。

效果参数名现在也查这张表：`zzzzzzzzzzzzzzzzz_zh_prop_fallback.py` 把 `prop::name` 的兜底
（`other => other`）改成查表，所以参数名和界面文字共用同一张表、同一条插入锚点。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH11_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH11_V1 — 效果参数名第三批
    ("Source Opacity", "源不透明度"),
    ("Clip HDR Values", "钳制 HDR 值"),
    ("Take Matte From Layer", "从图层取遮罩"),
    ("Use For Matte", "用于遮罩"),
    ("Invert Matte", "反转遮罩"),
    ("Stretch Matte to Fit", "拉伸遮罩以适合"),
    ("Composite Matte with Original", "遮罩与原图合成"),
    ("Premultiply Matte Layer", "预乘遮罩图层"),
    ("Input Channel", "输入通道"),
    ("Second Layer Channel", "第二图层通道"),
    ("Second Layer Opacity", "第二图层不透明度"),
    ("Invert Second Layer", "反转第二图层"),
    ("Stretch Second Layer to Fit", "拉伸第二图层以适合"),
    ("Preserve Transparency", "保持透明度"),
    ("RGB Only", "仅 RGB"),
    ("Operate On Channels", "作用通道"),
    ("Overflow Behavior", "溢出行为"),
    ("Stretch Second Source to Fit", "拉伸第二源以适合"),
    ("3D Channel", "3D 通道"),
    ("Clamp Output", "钳制输出"),
    ("Invert Depth Map", "反转深度图"),
    ("Anti-alias", "抗锯齿"),
    ("Matte Only", "仅遮罩"),
    ("Focal Plane", "焦平面"),
    ("Maximum Radius", "最大半径"),
    ("Focal Plane Thickness", "焦平面厚度"),
    ("Focal Bias", "焦距偏移"),
    ("UnMult", "取消预乘"),
    ("Fog Color", "雾颜色"),
    ("Fog Start Depth", "雾起始深度"),
    ("Fog End Depth", "雾结束深度"),
    ("Fog Opacity", "雾不透明度"),
    ("Scattering Density", "散射密度"),
    ("Foggy Background", "有雾背景"),
    ("Layer Contribution", "图层贡献"),
    ("Aux. Channel", "辅助通道"),
    ("ID Selection", "ID 选择"),
    ("Use Coverage", "使用覆盖"),
    ("Channel Type", "通道类型"),
    ("Snap Neutral Midtones", "对齐中性中间调"),
    ("Absolute Value", "绝对值"),
    ("Equalize", "色调均化"),
    ("Amount to Equalize", "均化量"),
    ("Auto Amounts", "自动数量"),
    ("Shadow Amount", "阴影数量"),
    ("Highlight Amount", "高光数量"),
    ("Shadow Tonal Width", "阴影色调宽度"),
    ("Shadow Radius", "阴影半径"),
    ("Highlight Tonal Width", "高光色调宽度"),
    ("Highlight Radius", "高光半径"),
    ("Color Correction", "颜色校正"),
    ("Midtone Contrast", "中间调对比度"),
    ("Source Layer Source", "源图层来源"),
    ("Sample", "取样"),
    ("Stencil Original Alpha", "模板原 Alpha"),
    ("Broadcast Locale", "广播区域"),
    ("How To Make Color Safe", "色彩安全方式"),
    ("Maximum Signal Amplitude (IRE)", "最大信号幅度（IRE）"),
    ("Tones", "色调"),
    ("Darktones", "暗调"),
    ("Red Phase", "红色相位"),
    ("Green Phase", "绿色相位"),
    ("Blue Phase", "蓝色相位"),
    ("High Dynamic Range", "高动态范围"),
    ("Input LUT", "输入 LUT"),
    ("Input LUT File", "输入 LUT 文件"),
    ("Whites", "白场"),
    ("Blacks", "黑场"),
    ("HDR White", "HDR 白场"),
    ("HDR Specular", "HDR 高光"),
    ("Look", "外观"),
    ("Look File", "外观文件"),
    ("Faded Film", "褪色胶片"),
    ("Shadow Tint", "阴影染色"),
    ("Highlight Tint", "高光染色"),
    ("Tint Balance", "染色平衡"),
    ("Hue Center", "色相中心"),
    ("Hue Range", "色相范围"),
    ("Hue Softness", "色相柔和度"),
    ("Saturation Low", "饱和度下限"),
    ("Saturation High", "饱和度上限"),
    ("Saturation Softness", "饱和度柔和度"),
    ("Lightness Low", "明度下限"),
    ("Lightness High", "明度上限"),
    ("Lightness Softness", "明度柔和度"),
    ("Show Mask", "显示遮罩"),
    ("Mask Style", "遮罩样式"),
    ("Denoise", "降噪"),
    ("Correction", "校正"),
    ("Hue Transform", "色相变换"),
    ("Lightness Transform", "明度变换"),
    ("Saturation Transform", "饱和度变换"),
    ("Color To Change", "要改变的颜色"),
    ("Invert Color Correction Mask", "反转颜色校正遮罩"),
    ("Clip Level", "裁切级别"),
    ("Clip Method", "裁切方式"),
    ("Compression before Clipping", "裁切前压缩"),
    ("Gamut Warning", "色域警告"),
    ("Gamut Warning Color", "色域警告颜色"),
    ("Shadows Unbalance", "阴影失衡"),
    ("Shadows Balance", "阴影平衡"),
    ("Midtones Unbalance", "中间调失衡"),
    ("Midtones Balance", "中间调平衡"),
    ("Highlights Unbalance", "高光失衡"),
    ("Highlights Balance", "高光平衡"),
    ("Darks", "暗部"),
    ("Apply Phase Map To Alpha", "相位映射应用到 Alpha"),
    ("Map", "映射"),
    ("Black Stretch", "黑场拉伸"),
    ("Map Black To", "黑色映射到"),
    ("Map White To", "白色映射到"),
    ("Amount to Tint", "染色量"),
    ("Use Legacy", "使用旧版"),
    ("Channel Control", "通道控制"),
    ("Master Hue", "主色相"),
    ("Master Saturation", "主饱和度"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("303_zh_batch11.py already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH11_V1", 1)
    path.write_text(src, encoding="utf-8")
    print("303_zh_batch11.py added")


if __name__ == "__main__":
    main()
