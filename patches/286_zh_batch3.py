#!/usr/bin/env python3
"""汉化第三批：表单 / 导出 / 蒙版 / 木偶 / 时间码（71 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH3_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("New Composition from Selection", "从所选创建合成"),\n    ("Create", "创建"),\n    ("Overlap", "重叠"),\n    ("Transition", "过渡"),\n    ("Embedded / sRGB", "内嵌 / sRGB"),\n    ("Cineon Settings", "Cineon 设置"),\n    ("Logarithmic Conversion", "对数转换"),\n    ("Converted Black Point", "转换后黑场"),\n    ("Converted White Point", "转换后白场"),\n    ("Current Gamma", "当前 Gamma"),\n    ("Highlight Rolloff", "高光过渡"),\n    ("Units", "单位"),\n    ("Interpret Footage: Proxy", "解释素材：代理"),\n    ("Project Settings", "工程设置"),\n    ("Depth", "深度"),\n    ("Frames", "帧"),\n    ("Frame count", "帧数"),\n    ("Start at 0", "从 0 开始"),\n    ("Start at 1", "从 1 开始"),\n    ("HDR on SDR displays and outputs", "在 SDR 显示与输出上呈现 HDR"),\n    ("Compand", "压缩/扩展"),\n    ("Rec. 2100 PQ (HDR)", "Rec. 2100 PQ（HDR）"),\n    ("Rec. 2100 HLG (HDR)", "Rec. 2100 HLG（HDR）"),\n    ("Export Adobe Premiere Pro Project", "导出 Adobe Premiere Pro 工程"),\n    ("File", "文件"),\n    ("Format", "格式"),\n    ("FCPXML (.fcpxml)", "FCPXML（.fcpxml）"),\n    ("OpenTimelineIO (.otio)", "OpenTimelineIO（.otio）"),\n    ("CMX 3600 EDL (.edl, V1 only)", "CMX 3600 EDL（.edl，仅视频轨）"),\n    ("AAF (.aaf)", "AAF（.aaf）"),\n    ("OMF (.omf, audio)", "OMF（.omf，音频）"),\n    ("Pre-render (ProRes 4444)", "预渲染（ProRes 4444）"),\n    ("Precomps", "预合成"),\n    ("Pre-render", "预渲染"),\n    ("Orientation", "方向"),\n    ("Degrees", "度"),\n    ("Opacity (%)", "不透明度（%）"),\n    ("Page", "页面"),\n    ("Puppet Follow-Through", "木偶跟随"),\n    ("Puppet Record Options", "木偶记录选项"),\n    ("Smoothing", "平滑"),\n    ("Mask Feather", "蒙版羽化"),\n    ("Feather (pixels)", "羽化（像素）"),\n    ("Mask Opacity", "蒙版不透明度"),\n    ("Mask Expansion", "蒙版扩展"),\n    ("Expansion (pixels)", "扩展（像素）"),\n    ("Mask Shape", "蒙版形状"),\n    ("Shape", "形状"),\n    ("Auto-Orientation", "自动定向"),\n    ("Go to Time", "跳到时间"),\n    ("Add Guide", "添加参考线"),\n    ("Add Percentage Guide", "添加百分比参考线"),\n    ("Auto-trace", "自动追踪"),\n    ("Scene Edit Detection", "场景剪切检测"),\n    ("Action", "操作"),\n    ("New Placeholder", "新建占位符"),\n    ("Placeholder", "占位符"),\n    ("My Template", "我的模板"),\n    ("Save as Template", "存为模板"),\n    ("Description", "说明"),\n    ("Category", "分类"),\n    ("My Templates", "我的模板"),\n    ("My Custom RGB", "我的自定义 RGB"),\n    ("Red x", "红 X"),\n    ("Red y", "红 Y"),\n    ("Green x", "绿 X"),\n    ("Green y", "绿 Y"),\n    ("Blue x", "蓝 X"),\n    ("Blue y", "蓝 Y"),\n    ("White point x", "白点 X"),\n    ("White point y", "白点 Y"),\n    ("Gamma", "Gamma"),\n    ("Use the sRGB curve (ignore Gamma)", "使用 sRGB 曲线（忽略 Gamma）"),\n    ("ICC profile (replaces the numbers)", "ICC 配置文件（替换上述数值）"),\n    ("View Options", "视图选项"),\n    ("OK on the unedited time stays put", "未编辑的时间保持不变"),\n    ("Spot", "聚光"),\n    ("Final Cut Pro XML (.xml)", "Final Cut Pro XML（.xml）"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 3 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH3_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 3 added")


if __name__ == "__main__":
    main()
