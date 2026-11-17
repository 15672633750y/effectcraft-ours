#!/usr/bin/env python3
"""汉化第十八批：引擎状态/报错长句收尾（129 条）。

引擎的命令报错走 `i18n::status()`（`命令: 消息` 只翻后半句），这些句子按原文进表即可。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_BATCH18_V1"

ANCHOR = '];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1'

ROWS = """    // EFFECTCRAFT_OURS_ZH_BATCH18_V1 — 引擎状态与报错
    ("A2B0 must map 3 device channels to 3 PCS values", "A2B0 必须把 3 个设备通道映射到 3 个 PCS 值"),
    ("EffectCraft asked the helper to shut down", "EffectCraft 要求效果助手退出"),
    ("Error: circular expression reference (the expression needs its own value)", "错误：表达式循环引用（表达式需要它自己的值）"),
    ("Error: expression needs too many property reads", "错误：表达式读取的属性太多"),
    ("Error: expression reads too many other expressions' values (circular or fanning-out references?)", "错误：表达式读取了太多其它表达式的值（循环引用或扇出引用？）"),
    ("Error: expression result is not a finite number", "错误：表达式结果不是有限数值"),
    ("Error: expression result is undefined", "错误：表达式结果未定义"),
    ("Error: expression result must be a path", "错误：表达式结果必须是路径"),
    ("Error: expression selector amount must be a number or an array of numbers", "错误：表达式选择器的数量必须是数字或数字数组"),
    ("Error: expressions reference each other too deeply (circular reference?)", "错误：表达式互相引用层级过深（循环引用？）"),
    ("Error: path points must be finite numbers", "错误：路径点必须是有限数值"),
    ("GPU readback cancelled", "GPU 回读已取消"),
    ("GPU readback exceeds buffer budget", "GPU 回读超出缓冲区预算"),
    ("GPU readback request id exhausted", "GPU 回读请求编号已用尽"),
    ("PAD: rank mismatch", "PAD：维度不匹配"),
    ("Texture inspection only", "仅纹理检查"),
    ("`expect_error` must be true or a text the error contains", "`expect_error` 必须是 true 或错误信息里包含的文本"),
    ("`params` must be an object", "`params` 必须是对象"),
    ("`start` object needs a `project` path", "`start` 对象需要 `project` 路径"),
    ("a tensor is too large", "张量过大"),
    ("bad channel counts", "通道数不对"),
    ("bad clut precision", "CLUT 精度不对"),
    ("bad grid", "网格参数不对"),
    ("bad pool size", "池化大小不对"),
    ("bad stride", "步长不对"),
    ("bad table dimensions", "表维度不对"),
    ("bad table sizes", "表尺寸不对"),
    ("bad window", "窗口参数不对"),
    ("bias_add_parallel needs contiguous inputs", "bias_add_parallel 需要连续输入"),
    ("bias_add_parallel needs f32", "bias_add_parallel 需要 f32"),
    ("bias_add_parallel: sizes do not fit", "bias_add_parallel：尺寸不匹配"),
    ("box: expected [x, y, width, height] or null", "box：需要 [x, y, width, height] 或 null"),
    ("checkpoint exceeds the 1024 MiB archive limit", "检查点超出 1024 MiB 归档上限"),
    ("checkpoint exceeds the decompressed storage limit", "检查点超出解压后存储上限"),
    ("checkpoint exceeds the tensor count limit", "检查点张量数量超出上限"),
    ("checkpoint exceeds the total element limit", "检查点元素总数超出上限"),
    ("composer: expected everyLine|singleLine", "composer：需要 everyLine|singleLine"),
    ("could not start reading the Cryptomatte IDs", "无法开始读取 Cryptomatte ID"),
    ("diagnostics evaluated on UI thread", "诊断在界面线程上求值"),
    ("direction: expected ltr|rtl", "direction：需要 ltr|rtl"),
    ("effects through this helper are nested too deeply", "经由该效果助手的嵌套过深"),
    ("empty GPU texture readback", "GPU 纹理回读为空"),
    ("empty image", "图像为空"),
    ("face detector: missing outputs", "人脸检测器：缺少输出"),
    ("face mesh: missing outputs", "人脸网格：缺少输出"),
    ("figureStyle: expected default|lining|oldStyle", "figureStyle：需要 default|lining|oldStyle"),
    ("figureWidth: expected default|proportional|tabular", "figureWidth：需要 default|proportional|tabular"),
    ("figures: expected default|tabularLining|proportionalLining|tabularOldstyle|proportionalOldstyle", "figures：需要 default|tabularLining|proportionalLining|tabularOldstyle|proportionalOldstyle"),
    ("frame has a non-finite sample", "帧里有非有限采样值"),
    ("frame too large for a 32-bit plug-in", "帧对 32 位插件来说太大"),
    ("frames and truth masks must be the same size and count", "帧与真值遮罩的尺寸和数量必须一致"),
    ("gamma must be between 0.1 and 10", "伽马必须在 0.1 到 10 之间"),
    ("gelu_erf_parallel needs a contiguous input", "gelu_erf_parallel 需要连续输入"),
    ("gelu_erf_parallel needs f32", "gelu_erf_parallel 需要 f32"),
    ("held back by the test renderer", "被测试渲染器拦住"),
    ("image (JPEG)", "图像（JPEG）"),
    ("image (sample allocation)", "图像（采样分配）"),
    ("image (size)", "图像（尺寸）"),
    ("invalid GPU readback layout", "GPU 回读布局无效"),
    ("it has no path (the default path of a layer without a source is not sampled)", "它没有路径（无源图层的默认路径不参与取样）"),
    ("its path has more than 65 536 vertices", "它的路径超过 65 536 个顶点"),
    ("its path has no vertices", "它的路径没有顶点"),
    ("its path has too many vertices", "它的路径顶点过多"),
    ("its path holds a number that is not valid", "它的路径里有无效数值"),
    ("its path is unreadable", "它的路径无法读取"),
    ("its point count is not a multiple of three", "它的点数不是三的倍数"),
    ("needs render_v2", "需要 render_v2"),
    ("not read", "未读取"),
    ("old choice failed", "旧的选择失败"),
    ("pickle exceeds the object limit", "pickle 超出对象上限"),
    ("pickle stack underflow", "pickle 栈下溢"),
    ("pickle: bad STACK_GLOBAL", "pickle：STACK_GLOBAL 无效"),
    ("pickle: bad persistent id", "pickle：持久 ID 无效"),
    ("render output destinations exceed 1 MiB of path names", "渲染输出目标路径名超过 1 MiB"),
    ("render output plan exceeds 65536 paths or 16 MiB of path names; split the queue", "渲染输出计划超过 65536 个路径或 16 MiB 路径名；请拆分队列"),
    ("render output planning supports at most 256 storage overflow folders", "渲染输出规划最多支持 256 个存储溢出文件夹"),
    ("renders nested too deeply", "渲染嵌套层级过深"),
    ("session log header exceeds 1024 bytes", "会话日志头超过 1024 字节"),
    ("simulated yuv420 init failure", "模拟 yuv420 初始化失败"),
    ("staged pre-render paths exceed the 16 MiB limit", "暂存预渲染路径超过 16 MiB 上限"),
    ("stylisticSets: expected [1, 2, …] or a bit mask", "stylisticSets：需要 [1, 2, …] 或位掩码"),
    ("synchronous GPU readback is unavailable in the browser", "浏览器里没有同步 GPU 回读"),
    ("test did not start the replacement", "测试没有启动替换"),
    ("test encoder failure", "测试编码器失败"),
    ("test exporter timed out waiting for the frontend", "测试导出器等待前端超时"),
    ("test exporter waited for a blocked UI", "测试导出器在等被阻塞的界面"),
    ("the 3D Camera Tracker was removed during analysis", "3D 摄像机跟踪在分析过程中被移除"),
    ("the B curves are required", "B 曲线是必需的"),
    ("the Cryptomatte probe is unavailable", "Cryptomatte 探针不可用"),
    ("the JSON holds no samples", "JSON 里没有样本"),
    ("the Warp Stabilizer was removed during analysis", "变形稳定器在分析过程中被移除"),
    ("the analysed property was removed during the analysis", "被分析的属性在分析过程中被移除"),
    ("the checkpoint is not a state dict", "检查点不是 state dict"),
    ("the config has no colorspaces", "配置里没有色彩空间"),
    ("the frontend stopped waiting for the script's render", "前端已停止等待脚本渲染"),
    ("the helper keeps stopping; it stays off until the next scan (Effect ▸ Scan for Effect Helpers)", "效果助手一直在退出；它会保持关闭直到下次扫描（效果 ▸ 扫描效果助手）"),
    ("the helper's pipes are unavailable", "效果助手的管道不可用"),
    ("the installed file changed since it was installed (SHA-256 differs): install it again", "已安装的文件在安装后被改动（SHA-256 不一致）：请重新安装"),
    ("the job stopped unexpectedly", "任务意外停止"),
    ("the model's tensor metadata is too large", "模型的张量元数据过大"),
    ("the module implements WebAssembly ABI 1 but exports ec_render2", "模块实现的是 WebAssembly ABI 1，却导出 ec_render2"),
    ("the module implements WebAssembly ABI 2 but exports ec_render", "模块实现的是 WebAssembly ABI 2，却导出 ec_render"),
    ("the primaries must form a triangle", "三原色必须构成三角形"),
    ("the restarted helper could not list its effects", "重启后的效果助手无法列出效果"),
    ("the script that made this window has ended", "创建这个窗口的脚本已结束"),
    ("the tracker broke after emitting a frame", "跟踪器在输出一帧后中断"),
    ("there is no settings folder to save the repro in; pass `path`", "没有可保存复现文件的设置文件夹；请传 `path`"),
    ("this helper does not load files", "该效果助手不加载文件"),
    ("this session has no settings folder to install plug-ins into", "本会话没有可安装插件的设置文件夹"),
    ("this session has no settings folder to install scripts into", "本会话没有可安装脚本的设置文件夹"),
    ("too many pending GPU readbacks", "待处理的 GPU 回读太多"),
    ("too many staged pre-render movies", "暂存预渲染影片太多"),
    ("tracker gone", "跟踪器已消失"),
    ("tracker reported an unknown object", "跟踪器报告了未知对象"),
    ("truncated model", "模型被截断"),
    ("unexpected face detector", "意外的人脸检测器"),
    ("unexpected face mesh", "意外的人脸网格"),
    ("unexpected pool shapes", "意外的池化形状"),
    ("unknown or duplicate favorite theme", "未知或重复的收藏主题"),
    ("unknown profile connection space", "未知的配置文件连接空间"),
    ("unsupported curve element", "不支持的曲线元素"),
    ("usage: snapshot [--out ui.png] [--size WxH] [--scale 2] [--settle secs] [--empty] [--script f.jsonl | --step json]...", "用法：snapshot [--out ui.png] [--size 宽x高] [--scale 2] [--settle 秒] [--empty] [--script f.jsonl | --step json]…"),
    ("use the panel open commands to preserve viewer and ScriptUI lifecycle callbacks", "请用面板打开命令，以保留预览与 ScriptUI 的生命周期回调"),
    ("use the window.workspace commands for named workspaces", "命名工作区请用 window.workspace 命令"),
    ("worker lost", "工作线程已丢失"),
    ("workspace dock tree exceeds supported limits", "工作区停靠树超出支持上限"),
    ("workspace file exceeds 1 MiB", "工作区文件超过 1 MiB"),
    ("workspace names or count exceed supported limits", "工作区名称或数量超出支持上限"),
    ("zip entry exceeds the size limit", "zip 条目超出大小上限"),
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("batch 18 already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ROWS + ANCHOR + "\n// EFFECTCRAFT_OURS_ZH_BATCH18_V1", 1)
    path.write_text(src, encoding="utf-8")
    print("batch 18 added")


if __name__ == "__main__":
    main()
