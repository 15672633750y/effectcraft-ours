#!/usr/bin/env python3
"""补中文：38 个混合模式 + 纯色设置的字段（之前显示英文）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1"

OLD = '    ("GPU Acceleration (no GPU: software)", "GPU 加速（无 GPU：软件）"),\n];'

ROWS = '    ("Normal", "正常"),\n    ("Dissolve", "溶解"),\n    ("Dancing Dissolve", "动态溶解"),\n    ("Darken", "变暗"),\n    ("Multiply", "正片叠底"),\n    ("Color Burn", "颜色加深"),\n    ("Classic Color Burn", "经典颜色加深"),\n    ("Linear Burn", "线性加深"),\n    ("Darker Color", "较暗颜色"),\n    ("Add", "相加"),\n    ("Lighten", "变亮"),\n    ("Screen", "滤色"),\n    ("Color Dodge", "颜色减淡"),\n    ("Classic Color Dodge", "经典颜色减淡"),\n    ("Linear Dodge", "线性减淡"),\n    ("Lighter Color", "较亮颜色"),\n    ("Overlay", "叠加"),\n    ("Soft Light", "柔光"),\n    ("Hard Light", "强光"),\n    ("Linear Light", "线性光"),\n    ("Vivid Light", "亮光"),\n    ("Pin Light", "点光"),\n    ("Hard Mix", "纯色混合"),\n    ("Difference", "差值"),\n    ("Classic Difference", "经典差值"),\n    ("Exclusion", "排除"),\n    ("Subtract", "相减"),\n    ("Divide", "划分"),\n    ("Hue", "色相"),\n    ("Saturation", "饱和度"),\n    ("Color", "颜色"),\n    ("Luminosity", "明度"),\n    ("Stencil Alpha", "模板 Alpha"),\n    ("Stencil Luma", "模板亮度"),\n    ("Silhouette Alpha", "轮廓 Alpha"),\n    ("Silhouette Luma", "轮廓亮度"),\n    ("Alpha Add", "Alpha 相加"),\n    ("Luminescent Premul", "发光预乘"),\n    ("Solid Settings", "纯色设置"),\n    ("Square Pixels", "方形像素"),\n    ("Width: {}% of comp", "宽度：合成的 {}%"),\n    ("Height: {}% of comp", "高度：合成的 {}%"),\n    ("Frame Aspect Ratio: {}", "帧长宽比：{}"),\n    ("Affect all layers that use this solid", "影响使用该纯色的所有图层"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("blend/solid translations already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    new = ROWS + '\n];' + '\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'
    src = src.replace(OLD, '    ("GPU Acceleration (no GPU: software)", "GPU 加速（无 GPU：软件）"),\n' + new, 1)
    path.write_text(src, encoding="utf-8")
    print("38 blend modes + solid settings translated")


if __name__ == "__main__":
    main()
