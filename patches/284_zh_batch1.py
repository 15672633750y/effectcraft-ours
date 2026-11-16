#!/usr/bin/env python3
"""汉化第一批：对话框 / 合成设置 / 渲染队列 / 设置的界面文字（约 100 条）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH1_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = '    ("Null Settings", "空对象设置"),\n    ("Contributors", "贡献者"),\n    ("Models", "模型"),\n    ("Choose Name", "选择名称"),\n    ("Width", "宽度"),\n    ("Height", "高度"),\n    ("Command Palette", "命令面板"),\n    ("Test", "测试"),\n    ("Main", "主"),\n    ("Affect all", "影响全部"),\n    ("Single Composition is the default", "默认为单个合成"),\n    ("OK closed the dialog", "已关闭对话框"),\n    ("Composition Settings is one undo step", "合成设置是一步撤销"),\n    ("Save Preset", "保存预设"),\n    ("Custom Resolution", "自定义分辨率"),\n    ("Anchor", "锚点"),\n    ("Renderer", "渲染器"),\n    ("Composition Name", "合成名称"),\n    ("Composition Settings width", "合成设置宽度"),\n    ("Quality: Best", "品质：最佳"),\n    ("Quality: Draft", "品质：草稿"),\n    ("Time Span: Work Area Only", "时间范围：仅工作区"),\n    ("Time Span: Length of Comp", "时间范围：合成长度"),\n    ("Frame Rate: Use comp\'s frame rate", "帧速率：使用合成的帧速率"),\n    ("Skip Existing Files", "跳过已有文件"),\n    ("Use Storage Overflow", "使用存储溢出"),\n    ("Channels: RGB", "通道：RGB"),\n    ("Channels: RGB + Alpha", "通道：RGB + Alpha"),\n    ("Channels: Alpha", "通道：Alpha"),\n    ("Color: Straight (Unmatted)", "颜色：直接（未预乘）"),\n    ("Color: Premultiplied (Matted)", "颜色：预乘（已遮罩）"),\n    ("Loop Forever", "永久循环"),\n    ("Crop: Off", "裁剪：关"),\n    ("Crop: Use Region of Interest", "裁剪：使用关注区域"),\n    ("Resize: Off", "缩放：关"),\n    ("Resize: Lock Aspect Ratio", "缩放：锁定长宽比"),\n    ("Include Project Link", "包含工程链接"),\n    ("Audio Output: Auto", "音频输出：自动"),\n    ("Audio Output: On", "音频输出：开"),\n    ("Audio Output: Off", "音频输出：关"),\n    ("Audio Channels: Mono", "音频声道：单声道"),\n    ("Audio Channels: Stereo", "音频声道：立体声"),\n    ("Level: Auto", "电平：自动"),\n    ("Key Frames: Auto (2 s)", "关键帧：自动（2 秒）"),\n    ("Key Frames: Every Frame (all intra)", "关键帧：每帧（全帧内）"),\n    ("Make Render Settings Template", "保存渲染设置模板"),\n    ("Make Output Module Template", "保存输出模块模板"),\n    ("Custom Time Span", "自定义时间范围"),\n    ("Start (s)", "开始（秒）"),\n    ("Duration (s)", "时长（秒）"),\n    ("Use This Frame Rate", "使用此帧速率"),\n    ("Frames per second", "帧/秒"),\n    ("Crop", "裁剪"),\n    ("Resize to", "缩放到"),\n    ("WebM Target Bitrate", "WebM 目标码率"),\n    ("Bitrate (kbps)", "码率（kbps）"),\n    ("Target Bitrate", "目标码率"),\n    ("Key Frame Interval", "关键帧间隔"),\n    ("Notify: on", "通知：开"),\n    ("Notify: off", "通知：关"),\n    ("Export is not available in this build", "此版本不支持导出"),\n    ("Output To", "输出到"),\n    ("Not yet specified", "尚未指定"),\n    ("Click to choose where to save; Alt-click to edit the template", "点击选择保存位置；Alt+点击编辑模板"),\n    ("Click to edit", "点击编辑"),\n    ("Drop compositions to queue", "把合成拖到队列"),\n    ("Render: on", "渲染：开"),\n    ("Render: off", "渲染：关"),\n    ("Render Settings:", "渲染设置："),\n    ("Output Module:", "输出模块："),\n    ("EXR Compression", "EXR 压缩"),\n    ("EXR Bit Depth", "EXR 位深"),\n    ("Default Output", "默认输出"),\n    ("Path", "路径"),\n    ("Face tracking", "面部跟踪"),\n    ("In use", "使用中"),\n    ("Built in", "内置"),\n    ("Installed", "已安装"),\n    ("Not installed", "未安装"),\n    ("Project page", "项目主页"),\n    ("Licence", "许可证"),\n    ("Install from File", "从文件安装"),\n    ("Update All", "全部更新"),\n    ("Preview: drag to compare", "预览：拖动对比"),\n    ("Memory only: nothing is kept after a reload", "仅内存：刷新后不保留"),\n    ("Unknown", "未知"),\n    ("Usage unknown", "用量未知"),\n    ("Disk cache: off", "磁盘缓存：关"),\n    ("Persistent storage: granted", "持久存储：已授权"),\n    ("Clear Disk Cache", "清除磁盘缓存"),\n    ("Clear Imported Media", "清除导入的媒体"),\n    ("Clear Auto-Saves", "清除自动保存"),\n    ("Clear Saved Projects", "清除已保存的工程"),\n    ("Recover Project", "恢复工程"),\n    ("Open Auto-Save", "打开自动保存"),'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 1 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + '\n' + ANCHOR + '\n// EFFECTCRAFT_OURS_ZH_BATCH1_V1', 1)
    path.write_text(src, encoding="utf-8")
    print("batch 1: %d rows" % len(ROWS.splitlines()))


if __name__ == "__main__":
    main()
