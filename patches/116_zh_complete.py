#!/usr/bin/env python3
"""Finish the Simplified Chinese: every tr() string the audit found missing, plus the type
column, the 8/16/32 bpc button and the plug-in/learn/label dialogs.

`tools/audit_i18n.py` lists what still falls back to English (101 strings when this was written);
they are all here, translated. The project panel's Type column never went through `tr()` at all,
and neither did the colour-depth button, so both are routed through the table now.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_COMPLETE_V1"
ANCHOR = "const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[\n"

ROWS = """
    ("A built-in preset has this name", "已有内置预设使用这个名称"),
    ("Active Camera ({})", "活动摄像机（{}）"),
    ("After", "之后"),
    ("Alpha: {}", "不透明度：{}"),
    ("Alt or Ctrl", "Alt 或 Ctrl"),
    ("At its default settings this effect leaves the sample frame unchanged.", "默认设置下，这个效果不会改变示例帧。"),
    ("Before", "之前"),
    ("Blue: {}", "蓝：{}"),
    ("By {}", "作者 {}"),
    ("Cannot import dropped files: {}", "无法导入拖入的文件：{}"),
    ("Cannot open dropped project {}: {}", "无法打开拖入的工程 {}：{}"),
    ("Catalog fetched {} (UTC)", "目录已更新于 {}（UTC）"),
    ("Check for Updates", "检查更新"),
    ("Click IDs in the Composition panel: Shift adds, {} removes, Esc ends", "在合成面板里点击 ID：Shift 加选，{} 减选，Esc 结束"),
    ("Click in the Composition panel to sample text {}", "在合成面板里点击以取样式 {}"),
    ("Click to sample text {}", "点击取样式 {}"),
    ("Click: replace · Shift: add · {}: remove", "点击：替换 · Shift：加选 · {}：减选"),
    ("Close font search", "关闭字体搜索"),
    ("Color under the pointer: {}", "指针处的颜色：{}"),
    ("Comment of {}: {}", "{} 的备注：{}"),
    ("Cryptomatte Selection: {}", "Cryptomatte 选择：{}"),
    ("Disk cache limit in effect: {} MB", "磁盘缓存实际上限：{} MB"),
    ("Drag cancelled the pick", "拖动已取消取色"),
    ("Drop file to import", "松开以导入文件"),
    ("Drop {} files to import", "松开以导入 {} 个文件"),
    ("Effect", "效果"),
    ("Export Anyway", "仍要导出"),
    ("Export Scene to Blender...", "导出场景到 Blender…"),
    ("Fetch Catalog", "获取目录"),
    ("Filter by footage status", "按素材状态筛选"),
    ("Green: {}", "绿：{}"),
    ("Hands-on tutorials that run inside EffectCraft. Do each step yourself, or press Show me.", "在 EffectCraft 里动手做的教程：每个步骤自己做，或者按「演示给我看」。"),
    ("Hide Preview", "隐藏预览"),
    ("Imported footage has an unlabeled alpha channel: choose how to interpret it in File ▸ Interpret Footage ▸ Main…", "导入的素材带有未标记的 Alpha 通道：在「文件 ▸ 解释素材 ▸ 主要…」里选择如何解释它"),
    ("Install", "安装"),
    ("Installed {}", "已安装 {}"),
    ("Installed {}: update available", "已安装 {}：有更新"),
    ("JavaScript with the After Effects scripting object model — try app.project.numItems", "After Effects 脚本对象模型的 JavaScript —— 试试 app.project.numItems"),
    ("Label of {}: {}", "{} 的标签：{}"),
    ("Label {} color", "标签「{}」的颜色"),
    ("Label {} name", "标签「{}」的名称"),
    ("Limited by free disk space: EffectCraft keeps 5% of the disk free (at least {} GB, at most {} GB).", "受可用磁盘空间限制：EffectCraft 预留 5% 磁盘（至少 {} GB，至多 {} GB）。"),
    ("Limited by free disk space: EffectCraft keeps {} GB of this disk free.", "受可用磁盘空间限制：EffectCraft 在这块盘上预留 {} GB。"),
    ("Needs a newer EffectCraft", "需要更新的 EffectCraft"),
    ("No plug-ins match the search.", "没有匹配的插件。"),
    ("No room left: nothing is written to the disk cache until disk space is freed.", "空间不足：腾出磁盘空间之前不会再写入磁盘缓存。"),
    ("Nothing is downloaded until you fetch the catalog.", "获取目录之前不会下载任何东西。"),
    ("Object {}", "对象 {}"),
    ("Object {} ({})", "对象 {}（{}）"),
    ("Only one project can be opened per drop; skipped {} more", "一次拖放只能打开一个工程；已跳过另外 {} 个"),
    ("Open in Essential Graphics", "在基本图形中打开"),
    ("Open on GitHub", "在 GitHub 打开"),
    ("Option or Cmd", "Option 或 Cmd"),
    ("Original color: click to go back to it", "原始颜色：点一下回到它"),
    ("Output file name template", "输出文件名模板"),
    ("Output file: {}", "输出文件：{}"),
    ("Parameters: {}", "参数：{}"),
    ("Partial solve: {} of {} frames solved", "部分解算：已解算 {} / {} 帧"),
    ("Plug-ins folder: {}", "插件文件夹：{}"),
    ("Preview", "预览"),
    ("Project color depth: {}", "工程色彩深度：{}"),
    ("Property: {}", "属性：{}"),
    ("Reading Cryptomatte IDs…", "正在读取 Cryptomatte ID…"),
    ("Red: {}", "红：{}"),
    ("Refresh", "刷新"),
    ("Remove this object's strokes", "移除这个对象的描边"),
    ("Rendering a preview in the sandbox…", "正在沙箱里渲染预览…"),
    ("Replaces your preset with this name", "会用这个名称覆盖同名的自定义预设"),
    ("Resize the Name column", "调整名称列宽"),
    ("Restart EffectCraft to finish", "重启 EffectCraft 以完成"),
    ("Script Console output", "脚本控制台输出"),
    ("Search plug-ins and effects", "搜索插件和效果"),
    ("Selected layers: {}", "选中图层：{}"),
    ("Skipped {} dropped file(s) without a local path. Use File ▸ Import ▸ File…", "已跳过 {} 个没有本地路径的拖入文件。请用「文件 ▸ 导入 ▸ 文件…」"),
    ("Skipped {} more file(s) while a dialog is open; import them again after it", "对话框打开期间又跳过了 {} 个文件；关掉后再导入一次"),
    ("Solid", "纯色层"),
    ("Some parts of this project cannot be exported exactly (left out or changed):", "这个工程的部分内容无法原样导出（已省略或改动）："),
    ("Sort by {}", "按 {} 排序"),
    ("Sort by {}, {}", "按 {}、{} 排序"),
    ("Source", "源"),
    ("Stop playback to pick", "停止播放后再取色"),
    ("Stroke width presets", "描边宽度预设"),
    ("Test catalog: {} (Refresh returns to the community catalog)", "测试目录：{}（点「刷新」回到社区目录）"),
    ("The Plug-in Library is available in the desktop app.", "插件库只在桌面版提供。"),
    ("The catalog lists no plug-ins yet.", "目录里还没有插件。"),
    ("Unpack Anyway", "仍要解包"),
    ("Unpacking this pre-comp layer changes the picture or drops something:", "解包这个预合成图层会改变画面或丢掉内容："),
    ("Update", "更新"),
    ("Update All ({})", "全部更新（{}）"),
    ("Update check is not supported in the web browser.", "浏览器版不支持检查更新。"),
    ("Variable Font Axes: {}", "可变字体轴：{}"),
    ("Video preview is off (Preview panel): audio only", "视频预览已关闭（预览面板）：仅音频"),
    ("Video preview off: audio only", "视频预览已关闭：仅音频"),
    ("Watch video", "看视频"),
    ("What the pre-comp layer itself carries is dropped. You can undo this.", "预合成图层自身携带的内容会被丢掉，可以撤销。"),
    ("X: {}", "X：{}"),
    ("Y: {}", "Y：{}"),
    ("{} (selected)", "{}（已选中）"),
    ("{} ({}) at default settings, on a sample frame", "{}（{}）在默认设置下的示例帧"),
    ("{}, {}", "{}、{}"),
    ("{}, {}, uses {}", "{}、{}，使用 {}"),
    ("Snap Edges Extended", "扩展边缘吸附"),
    ("Snap to Features in Collapsed Compositions and Text Layers", "吸附到折叠合成和文本图层中的特征"),
    ("Move Group To", "移动面板组到"),
    ("Close Other Panels in Group", "关闭面板组中的其他面板"),
    ("Maximize Frame", "最大化面板组"),
    ("Restore Frame Size", "还原面板组大小"),
    ("Folder", "文件夹"),
    ("Image", "图像"),
    ("Image Sequence", "图像序列"),
    ("3D Model", "3D 模型"),
    ("Data", "数据"),
    ("Solids", "固态层"),
"""

TYPE_OLD = '            "type" => it.type_name().to_string(),\n'
TYPE_NEW = '            "type" => crate::i18n::tr(it.type_name()).to_string(),\n'

BPC_OLD = "    let depth = app.session.project.settings.bit_depth.label();\n"
BPC_NEW = """    // The engine calls the depth "8 bpc"; the panel says 位/通道.
    let depth = match app.session.project.settings.bit_depth.label() {
        "8 bpc" => "8 位/通道",
        "16 bpc" => "16 位/通道",
        "32 bpc" => "32 位/通道",
        other => other,
    };
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    ui = root / "crates/ui-egui/src/i18n/ui.rs"
    src = ui.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(ANCHOR) != 1:
            raise SystemExit(f"i18n anchor: expected 1, found {src.count(ANCHOR)}")
        src = src.replace(ANCHOR, ANCHOR + "    // " + MARKER + "\n" + ROWS, 1)
        ui.write_text(src, encoding="utf-8")
        print("added the missing Simplified Chinese rows")

    proj = root / "crates/ui-egui/src/panels/project.rs"
    text = proj.read_text(encoding="utf-8")
    changed = False
    for old, new in ((TYPE_OLD, TYPE_NEW), (BPC_OLD, BPC_NEW)):
        if new.strip().splitlines()[0] in text:
            continue
        if text.count(old) != 1:
            raise SystemExit(f"project anchor: expected 1, found {text.count(old)}: {old[:40]!r}")
        text = text.replace(old, new, 1)
        changed = True
    if changed:
        proj.write_text(text, encoding="utf-8")
        print("type column and colour depth are Chinese")


if __name__ == "__main__":
    main()
