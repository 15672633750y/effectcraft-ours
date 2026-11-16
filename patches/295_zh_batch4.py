#!/usr/bin/env python3
"""汉化第四批：设置 / 快捷键编辑器 / 文本面板 / 跟踪 / 绘制（约 120 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH4_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("EffectCraft: property links", "EffectCraft：属性链接"),\n    ("A source path is required", "需要提供源文件路径"),\n    ("The web app has no local presets folder", "网页版没有本地预设文件夹"),\n    ("No presets folder is configured", "尚未配置预设文件夹"),\n    ("The presets folder path is not valid UTF-8", "预设文件夹路径不是有效的 UTF-8"),\n    ("GPU Information", "GPU 信息"),\n    ("Render finished", "渲染完成"),\n    ("Render every n-th pixel", "每 n 个像素渲染一次"),\n    ("Panel Background Color", "面板背景颜色"),\n    ("The Tools panel is the toolbar in the header", "工具面板就是顶栏的工具栏"),\n    ("New Workspace", "新建工作区"),\n    ("Untitled Workspace", "未命名工作区"),\n    ("Edit Workspaces", "编辑工作区"),\n    ("Workspace", "工作区"),\n    ("Rename to", "重命名为"),\n    ("A script wants to open a file", "有脚本想打开文件"),\n    ("Report", "报告"),\n    ("Untitled Project", "未命名工程"),\n    ("Watch Folder", "监视文件夹"),\n    ("Collected Files", "收集的文件"),\n    ("Origin Private File System", "源私有文件系统"),\n    ("Disk cache limit in effect:", "生效的磁盘缓存上限："),\n    ("New name", "新名称"),\n    ("Application-wide", "应用级"),\n    ("Panel-specific", "面板级"),\n    ("Click, then press keys", "点击后按键"),\n    ("OK button", "确定按钮"),\n    ("Mine", "我的"),\n    ("Cancel keeps the preset", "取消则保留当前预设"),\n    ("Metrics", "度量"),\n    ("Optical", "视觉"),\n    ("Kerning", "字距调整"),\n    ("All Fills Over All Strokes", "所有填充在描边之上"),\n    ("All Strokes Over All Fills", "所有描边在填充之上"),\n    ("Miter", "尖角"),\n    ("Bevel", "斜面"),\n    ("Stroke Order", "描边顺序"),\n    ("Font style", "字体样式"),\n    ("OpenType", "OpenType"),\n    ("Tate-Chu-Yoko", "纵中横"),\n    ("Standard Vertical Roman", "标准竖排罗马字"),\n    ("Editing: caret (applies to typed text)", "编辑：光标（对输入文字生效）"),\n    ("Swash", "花体"),\n    ("Ordinals", "序数"),\n    ("Fractions", "分数"),\n    ("Left-to-Right Text", "从左到右文本"),\n    ("Right-to-Left Text", "从右到左文本"),\n    ("World-Ready Every-line Composer", "全球语言逐行排版"),\n    ("World-Ready Single-line Composer", "全球语言单行排版"),\n    ("Composer", "排版器"),\n    ("Font family", "字体家族"),\n    ("Search fonts", "搜索字体"),\n    ("Close font list", "关闭字体列表"),\n    ("Selection", "选区"),\n    ("Horizontal Center", "水平居中"),\n    ("Vertical Center", "垂直居中"),\n    ("Sample", "示例"),\n    ("Motion Source", "运动来源"),\n    ("Current Track", "当前跟踪"),\n    ("Track Type", "跟踪类型"),\n    ("Motion Target", "运动目标"),\n    ("Edit Target...", "编辑目标…"),\n    ("Options...", "选项…"),\n    ("Analyze:", "分析："),\n    ("Analyze 1 frame backward", "向前分析 1 帧"),\n    ("Analyze 1 frame forward", "向后分析 1 帧"),\n    ("Analysis progress", "分析进度"),\n    ("Method:", "方法："),\n    ("Method", "方法"),\n    ("Track:", "跟踪："),\n    ("Track selected masks 1 frame backward", "所选蒙版向前跟踪 1 帧"),\n    ("Track selected masks backward", "所选蒙版向前跟踪"),\n    ("Track selected masks forward", "所选蒙版向后跟踪"),\n    ("Track selected masks 1 frame forward", "所选蒙版向后跟踪 1 帧"),\n    ("Extract & Copy Face Measurements", "提取并复制面部测量"),\n    ("Mask tracking progress", "蒙版跟踪进度"),\n    ("Tracks the pixels inside the mask and keys its Mask Path.", "跟踪蒙版内的像素并给蒙版路径打关键帧。"),\n    ("Blur pixels", "模糊像素"),\n    ("If Confidence is Below action", "置信度低于时执行"),\n    ("Confidence threshold", "置信度阈值"),\n    ("Apply Dimensions", "应用尺寸"),\n    ("Feature region corner", "特征区域角点"),\n    ("Search region corner", "搜索区域角点"),\n    ("Feature region", "特征区域"),\n    ("Search region", "搜索区域"),\n    ("Foreground color", "前景色"),\n    ("Background color", "背景色"),\n    ("Swap colors", "交换颜色"),\n    ("Default colors", "默认颜色"),\n    ("Flow:", "流量："),\n    ("Mode:", "模式："),\n    ("Channels:", "通道："),\n    ("Custom duration (frames)", "自定义时长（帧）"),\n    ("Erase:", "擦除："),\n    ("Current Layer", "当前图层"),\n    ("Source:", "源："),\n    ("Aligned", "已对齐"),\n    ("Lock Source Time", "锁定源时间"),\n    ("Clone offset", "克隆偏移"),\n    ("Source Time:", "源时间："),\n    ("Source Time Shift:", "源时间偏移："),\n    ("Clone Source Overlay", "克隆源叠加"),\n    ("Difference mode overlay", "差值模式叠加"),\n    ("Brush tip", "画笔笔尖"),\n    ("Angle:", "角度："),\n    ("Roundness:", "圆度："),\n    ("Hardness:", "硬度："),\n    ("Spacing", "间距"),\n    ("Pen Pressure", "压感"),\n    ("Size:", "大小："),\n    ("Minimum Size:", "最小大小："),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 4 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH4_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 4 added")


if __name__ == "__main__":
    main()
