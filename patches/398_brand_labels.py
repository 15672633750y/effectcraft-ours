#!/usr/bin/env python3
"""按钮文案按各家习惯，但每个都还是真功能：

* CapCut   视频 / 文字 / 形状 / 效果 / 播放 / 导出
* 快影      导入 / 字幕 / 特效 / 形状 / 播放 / 导出
* AM/Blurrr 导入 / 文字 / 形状 / 预设 / 播放 / 导出

对应关系（不造假）：
  视频 / 导入  → 打开导入面板（可导入 mp4/png/wav/mp3）
  字幕 / 文字  → layer.new（新建文字图层）
  特效 / 效果 / 预设 → 打开预设库
  形状        → layer.newShape
  播放        → playback.playing
  导出        → 导出对话框

同时把 CapCut 播放条的全屏键文字改成参考图里的 `Full`。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BRAND_LABELS_V1"

ITEMS_OLD = '''                    let items: [(&str, &str, u8); 6] = [
                        ("\\u{ff0b}", "导入", 0),
                        ("T", "文字", 1),
                        ("\\u{25c7}", "形状", 2),
                        ("\\u{2605}", "预设", 3),
                        ("\\u{25b6}", "播放", 4),
                        ("\\u{2191}", "导出", 8),
                    ];'''

ITEMS_NEW = '''                    // EFFECTCRAFT_OURS_BRAND_LABELS_V1 — 文案按各家习惯，动作不变
                    let items: Vec<(&str, &str, u8)> = match ws.as_str() {
                        "capcut" => vec![
                            ("\\u{ff0b}", "视频", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "效果", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],
                        "kuaishou" => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "字幕", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "特效", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],
                        _ => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "预设", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],
                    };'''

FULL_OLD = '''                        ("\\u{26f6}", 13, true),
                        ("\\u{ff0b}", 14, true),'''
FULL_NEW = '''                        ("Full", 13, true),
                        ("\\u{ff0b}", 14, true),'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("brand labels already present")
        return
    for name, old, new in (("items", ITEMS_OLD, ITEMS_NEW), ("full", FULL_OLD, FULL_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("tray labels follow each brand; capcut fullscreen reads Full")


if __name__ == "__main__":
    main()
