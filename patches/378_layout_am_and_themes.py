#!/usr/bin/env python3
"""对齐参考 app：删掉「剪映」（和 CapCut 同一种风格），加入 **AM**，并让各布局用**自己的主题色系**。

参考截图里 快影 / AM / CapCut 都是**亮色界面**（白底、浅灰分隔、彩色高亮），只有 Blurrr 偏暗。
所以：
* 布局 id：ae / capcut / blurrr / kuaishou / am（`jianying` 保留为 am 的别名，旧设置不失效）
* capcut / kuaishou / am 三套布局自动切到亮色主题，ae / blurrr 用用户自己的主题
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_AM_V1"

# ---------------- dock.rs：jianying -> am（含别名）
DOCK_OLD = '''        // 剪映：预览 + 很大的时间线（没有底部那一行）
        "jianying" => Layout {
            root: Some(vsplit(Ratio(0.42), tabs(&[Composition], 0), tabs(&[Timeline], 0))),
            floating: Vec::new(),
        },'''
DOCK_NEW = '''        // AM：预览 / 时间线 / 工具（参考截图里是"编组和蒙版"那种浅色界面）
        "am" | "jianying" => Layout {
            root: Some(vsplit(
                Ratio(0.44),
                tabs(&[Composition], 0),
                vsplit(Ratio(0.52), tabs(&[Timeline], 0), tabs(&[EffectControls], 0)),
            )),
            floating: Vec::new(),
        },'''

# ---------------- frame.rs：卡片、id 列表、竖屏判定
ENTRIES_OLD = '''        let entries: [(&str, &str, &str); 5] = [
            ("ae", "After Effects", "横屏 · 项目 | 预览 | 效果控件 + 底部时间轴"),
            ("capcut", "CapCut", "竖屏 · 上预览、中时间线、下属性/项目"),
            ("blurrr", "Blurrr", "竖屏 · 大预览、薄时间线"),
            ("kuaishou", "快影", "竖屏 · 预览 + 宽属性栏"),
            ("jianying", "剪映", "竖屏 · 预览小、时间线大"),
        ];'''
ENTRIES_NEW = '''        let entries: [(&str, &str, &str); 5] = [
            ("ae", "After Effects", "横屏 · 项目 | 预览 | 效果控件 + 底部时间轴"),
            ("capcut", "CapCut", "亮色 · 上预览、中时间线、下属性/项目"),
            ("blurrr", "Blurrr", "深色 · 大预览、薄时间线"),
            ("kuaishou", "快影", "亮色 · 预览 + 宽属性栏"),
            ("am", "AM", "亮色 · 预览 / 大时间线 / 工具行"),
        ];'''

IDS_OLD = '''    pub(crate) const OURS_LAYOUT_IDS: [&'static str; 5] = ["ae", "capcut", "blurrr", "kuaishou", "jianying"];'''
IDS_NEW = '''    pub(crate) const OURS_LAYOUT_IDS: [&'static str; 5] = ["ae", "capcut", "blurrr", "kuaishou", "am"];'''

LEGACY_OLD = '''            "simple" => "capcut".to_string(),
            "minimal" => "blurrr".to_string(),'''
LEGACY_NEW = '''            "simple" => "capcut".to_string(),
            "minimal" => "blurrr".to_string(),
            "jianying" => "am".to_string(),'''

HILITE_OLD = '''                    "simple" => "capcut".to_string(),
                    "minimal" => "blurrr".to_string(),'''
HILITE_NEW = '''                    "simple" => "capcut".to_string(),
                    "minimal" => "blurrr".to_string(),
                    "jianying" => "am".to_string(),'''

ENTRY_LABEL_OLD = '''            "jianying" => "剪映",'''
ENTRY_LABEL_NEW = '''            "am" | "jianying" => "AM",'''

# 竖屏判定统一加 am，去掉 jianying
PORTRAIT_OLD = 'matches!(ws, "capcut" | "blurrr" | "kuaishou" | "jianying")'
PORTRAIT_NEW = 'matches!(ws, "capcut" | "blurrr" | "kuaishou" | "am")'

PORTRAIT2_OLD = '''            "capcut" | "blurrr" | "kuaishou" | "jianying"
        );'''
PORTRAIT2_NEW = '''            "capcut" | "blurrr" | "kuaishou" | "am"
        );'''

CHROME_OLD = '''                if ws == "capcut" || ws == "jianying" {'''
CHROME_NEW = '''                if ws == "capcut" || ws == "am" {'''

CHROME_N_OLD = '''                    let n: usize = if ws == "jianying" { 5 } else { 4 };'''
CHROME_N_NEW = '''                    let n: usize = if ws == "am" { 5 } else { 4 };'''

# ---------------- 主题：亮色布局自动切亮色
THEME_ANCHOR = '''        self.apply_prefs(&ctx);'''
THEME_INSERT = '''        self.apply_prefs(&ctx);
        // EFFECTCRAFT_OURS_LAYOUT_AM_V1 — 布局自带的主题色系：参考 app 里 capcut/快影/AM 都是亮色界面
        {
            let light_layout = matches!(self.ui.workspace.as_str(), "capcut" | "kuaishou" | "am");
            let want = if light_layout {
                crate::theme::ThemeKind::Light
            } else {
                self.ui.theme
            };
            if self.tokens.kind != want {
                self.tokens = Tokens::from_prefs(&self.session.prefs, want);
                crate::theme::apply_visuals(&ctx, &self.tokens);
                ctx.set_theme(crate::theme::theme_preference(
                    &self.session.prefs.appearance.appearance_mode,
                    want.is_light(),
                ));
            }
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(DOCK_OLD) != 1:
            raise SystemExit(f"dock anchor: {src.count(DOCK_OLD)}")
        dock.write_text(src.replace(DOCK_OLD, DOCK_NEW, 1), encoding="utf-8")
        print("dock: jianying replaced by am (alias kept)")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("am layout already present")
        return
    for name, old, new in (
        ("entries", ENTRIES_OLD, ENTRIES_NEW),
        ("ids", IDS_OLD, IDS_NEW),
        ("legacy", LEGACY_OLD, LEGACY_NEW),
        ("hilite", HILITE_OLD, HILITE_NEW),
        ("label", ENTRY_LABEL_OLD, ENTRY_LABEL_NEW),
        ("chrome", CHROME_OLD, CHROME_NEW),
        ("chrome_n", CHROME_N_OLD, CHROME_N_NEW),
        ("theme", THEME_ANCHOR, THEME_INSERT),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    # 竖屏判定（两处）用 replace_all 语义
    src = src.replace(PORTRAIT_OLD, PORTRAIT_NEW)
    src = src.replace(PORTRAIT2_OLD, PORTRAIT2_NEW)
    frame.write_text(src, encoding="utf-8")
    print("frame: 5 cards (am instead of jianying), light theme for capcut/kuaishou/am")


if __name__ == "__main__":
    main()
