#!/usr/bin/env python3
"""汉化第七批：运动素描 / 摄像机求解 / 通用词（约 40 条）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH7_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("Unlock", "解锁"),\n    ("Type slot", "类型槽位"),\n    ("SOURCE FOOTAGE", "源素材"),\n    ("Nested", "嵌套"),\n    ("Inner", "内"),\n    ("Outer", "外"),\n    ("Other", "其他"),\n    ("Music", "音乐"),\n    ("Unused", "未使用"),\n    ("Physical", "物理"),\n    ("Camera", "摄像机"),\n    ("Curve", "曲线"),\n    ("Polyline", "折线"),\n    ("Jagged", "锯齿"),\n    ("Object", "对象"),\n    ("Surface", "表面"),\n    ("Subtle", "轻微"),\n    ("Select a layer to sketch its motion", "选择一个图层来描绘它的运动"),\n    ("Motion Sketch: drag in the Composition panel to record", "运动素描：在合成面板里拖动即可记录"),\n    ("Motion Sketch capture area", "运动素描捕获区域"),\n    ("Keyframe Fields (doubles rate)", "关键帧字段（加倍速率）"),\n    ("Pixels Between Vertices", "顶点之间的像素"),\n    ("Total Vertices", "顶点总数"),\n    ("Percentage of Outline", "轮廓百分比"),\n    ("Use 1:1 Vertex Matches", "使用 1:1 顶点匹配"),\n    ("First Vertices Match", "首顶点匹配"),\n    ("Applies to the selected Mask Path keyframes", "应用于所选蒙版路径关键帧"),\n    ("Select two or more Mask Path keyframes", "请选择两个或更多蒙版路径关键帧"),\n    ("Analyzing in background (step 1 of 2)", "后台分析中（第 1/2 步）"),\n    ("Solving camera", "正在求解摄像机"),\n    ("Unable to solve camera: try another Solve Method or Shot Type", "无法求解摄像机：请换一种求解方法或镜头类型"),\n    ("Waiting to analyze", "等待分析"),\n    ("Not analyzed: click Analyze", "未分析：点「分析」"),\n    ("Select a layer with a Subtract mask", "请选择带「相减」蒙版的图层"),\n    ("Save As opens a dialog again", "「另存为」会再次弹出对话框"),\n    ("Opened", "已打开"),\n    ("Saved", "已保存"),\n    ("Red: 128", "红：128"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 7 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH7_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 7 added")


if __name__ == "__main__":
    main()
