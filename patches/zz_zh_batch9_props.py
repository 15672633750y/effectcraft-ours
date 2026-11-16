#!/usr/bin/env python3
"""汉化第九批：效果参数名第二批（120 条），含 S_Vintage / S_Vignette 的全部参数。

补在 `i18n/prop.rs` 的 match 里（效果控件行、属性面板行、时间轴属性行都走这里）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH9_V1"

ANCHOR = "        other => other,"

ROWS = """        // EFFECTCRAFT_OURS_ZH_BATCH9_V1 — 效果参数名第二批
        "Colour Suppression" => "色彩抑制",
        "Colour Balance Hue" => "色彩平衡色相",
        "Choke" => "阻塞",
        "Sharpen Amount" => "锐化量",
        "Relief" => "浮雕",
        "Shadow Only" => "仅阴影",
        "Box Color" => "盒状颜色",
        "Noise Phase" => "噪波相位",
        "Displacement Amount" => "置换量",
        "Offset Turbulence" => "湍流偏移",
        "Noise Type" => "噪波类型",
        "Sub Scaling" => "子缩放",
        "Rotation X" => "X 轴旋转",
        "Rotation Y" => "Y 轴旋转",
        "Rotation Z" => "Z 轴旋转",
        "Light Angle" => "光照角度",
        "Use Layer As Map" => "以图层为映射",
        "Scanlines" => "扫描线",
        "Alignment" => "对齐",
        "Line Spacing" => "行距",
        "Vector Detail" => "矢量细节",
        "Shutter Control" => "快门控制",
        "Shutter Samples" => "快门采样",
        "Native Motion Blur" => "原生运动模糊",
        "Flip Direction" => "翻转方向",
        "Layer to Reveal" => "要显示的图层",
        "Effect" => "效果",
        "Center XY" => "中心 XY",
        "Squareness" => "方化",
        "Rel Height" => "相对高度",
        "Rel Width" => "相对宽度",
        "Smooth Curve" => "平滑曲线",
        "Blur Amount" => "模糊量",
        "Blur Inside" => "内部模糊",
        "Source Brightness" => "源亮度",
        "Combine" => "混合方式",
        "Swap Channels" => "交换通道",
        "Bass" => "低频",
        "Treble" => "高频",
        "Ratio (x:1)" => "压缩比（x:1）",
        "Knee (dB)" => "拐点（dB）",
        "Auto Release" => "自动释放",
        "Makeup Gain (dB)" => "补偿增益（dB）",
        "Output Limit (dB)" => "输出限制（dB）",
        "Delay Time (milliseconds)" => "延迟时间（毫秒）",
        "Volume" => "音量",
        "Resolution (bit)" => "位深",
        "Downsample (x)" => "降采样（x）",
        "Voice Separation Time (ms)" => "声音分离时间（毫秒）",
        "Voices" => "声部",
        "Voice Phase Change" => "声部相位变化",
        "Stereo Voices" => "立体声声部",
        "Hold (ms)" => "保持（毫秒）",
        "Filter Options" => "滤波选项",
        "Cutoff Frequency" => "截止频率",
        "Modulation Type" => "调制类型",
        "Reverb Time (milliseconds)" => "混响时间（毫秒）",
        "Left Level" => "左声道电平",
        "Right Level" => "右声道电平",
        "Left Pan" => "左声道声像",
        "Right Pan" => "右声道声像",
        "Waveform Options" => "波形选项",
        "Frequency 1" => "频率 1",
        "Frequency 2" => "频率 2",
        "Frequency 3" => "频率 3",
        "Frequency 4" => "频率 4",
        "Frequency 5" => "频率 5",
        "Red Blurriness" => "红色模糊度",
        "Green Blurriness" => "绿色模糊度",
        "Blue Blurriness" => "蓝色模糊度",
        "Alpha Blurriness" => "Alpha 模糊度",
        "Blur Layer" => "模糊图层",
        "Maximum Blur" => "最大模糊",
        "Stretch Map to Fit" => "拉伸映射以适合",
        "Invert Blur" => "反转模糊",
        "Diffraction Fringe" => "衍射边缘",
        "Placement" => "放置",
        "Invert Blur Map" => "反转模糊映射",
        "Use Linear Working Space" => "使用线性工作空间",
        "Angle Offset" => "角度偏移",
        "Map Softness" => "映射柔和度",
        "Blur Duration" => "模糊时长",
        "Deblur Method" => "去模糊方式",
        "Shake Sensitivity" => "抖动灵敏度",
        "Search Range" => "搜索范围",
        "Patch Size" => "补丁大小",
        "Show Blurry Frames" => "显示模糊帧",
        "Shot Type" => "镜头类型",
        "Horizontal Angle of View" => "水平视角",
        "Render Track Points" => "渲染跟踪点",
        "Target Size" => "目标大小",
        "Solve Method" => "解算方式",
        "Solve Lens Distortion" => "解算镜头畸变",
        "Undistort Footage" => "去畸变素材",
        "Auto-delete Points Across Time" => "跨时间自动删除跟踪点",
        "Camera System" => "摄像机系统",
        "X, Y Position" => "X、Y 位置",
        "Transform Order" => "变换顺序",
        "Upper Left Corner" => "左上角",
        "Upper Right Corner" => "右上角",
        "Lower Left Corner" => "左下角",
        "Lower Right Corner" => "右下角",
        "Auto Focal Length" => "自动焦距",
        "Light Depth" => "灯光深度",
        "Ambient Light" => "环境光",
        "Diffuse Reflection" => "漫反射",
        "Specular Reflection" => "镜面反射",
        "Highlight Sharpness" => "高光锐度",
        "Source Layer 1" => "源图层 1",
        "Source Layer 2" => "源图层 2",
        "Source Layer 3" => "源图层 3",
        "Source Layer 4" => "源图层 4",
        "Stretch Layers to Fit" => "拉伸图层以适合",
        "Use 2nd Layer" => "使用第二个图层",
        "Solid Alpha" => "纯色 Alpha",
        "Operation" => "运算",
        "Don't Shrink Edges" => "不收缩边缘",
        "Red Value" => "红色值",
        "Green Value" => "绿色值",
        "Blue Value" => "蓝色值",
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/prop.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 9 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("batch 9 added")


if __name__ == "__main__":
    main()
