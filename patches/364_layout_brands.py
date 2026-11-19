#!/usr/bin/env python3
"""布局切换器：五套品牌布局，真的重排面板（含竖屏/横屏两种排法），并给每张卡片做区域扫光。

- `dock::ours_layout()` 扩成五套：AE（横屏：左项目｜中预览｜右属性 + 下时间线）、
  CapCut / Blurrr / 快影 / 剪映（竖屏：上预览、中时间线、下工具条的三段式排法，比例各不同）。
- 旧 id（classic/simple/pro/minimal）继续可用，避免已存的设置失效。
- 卡片里的扫光改成**每张卡自己的扫描带**（相位错开、只在本卡内可见），不再是全屏一条带。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_BRANDS_V1"

# ---------------------------------------------------------------- dock.rs
DOCK_OLD = '''pub fn ours_layout(name: &str) -> Layout {
    use PanelKind::*;
    use SplitSize::*;
    let simple = || Layout { root: Some(vsplit(Ratio(0.65), tabs(&[Composition], 0), tabs(&[Timeline], 0))), floating: Vec::new() };
    match name {'''

DOCK_NEW = '''pub fn ours_layout(name: &str) -> Layout {
    use PanelKind::*;
    use SplitSize::*;
    let simple = || Layout { root: Some(vsplit(Ratio(0.65), tabs(&[Composition], 0), tabs(&[Timeline], 0))), floating: Vec::new() };
    // 竖屏三段式：上预览 / 中时间线 / 下属性（手机剪辑软件的典型排法）。
    // `top` 是预览占比，`mid` 是时间线在上半段里的占比。
    let portrait = |top: f32, mid: f32| Layout {
        root: Some(vsplit(
            Ratio(top),
            tabs(&[Composition], 0),
            vsplit(
                Ratio(mid),
                tabs(&[Timeline], 0),
                hsplit(Ratio(0.62), tabs(&[EffectControls], 0), tabs(&[Project], 0)),
            ),
        )),
        floating: Vec::new(),
    };
    match name {
        // —— 五套品牌布局（EFFECTCRAFT_OURS_LAYOUT_BRANDS_V1）——
        // After Effects：横屏。左项目栏固定宽度 | 中间预览 + 右侧效果控件 | 底部时间线。
        "ae" => Layout {
            root: Some(vsplit(
                Ratio(0.58),
                hsplit(
                    FixedFirst(168.0),
                    tabs(&[Project], 0),
                    hsplit(Ratio(0.68), tabs(&[Composition], 0), tabs(&[EffectControls], 0)),
                ),
                tabs(&[Timeline], 0),
            )),
            floating: Vec::new(),
        },
        // CapCut：竖屏。预览 52%，下面时间线 + 属性/项目并排。
        "capcut" => portrait(0.52, 0.42),
        // Blurrr：竖屏，预览占比更大，时间线更薄。
        "blurrr" => portrait(0.60, 0.34),
        // 快影：竖屏，属性栏更宽（右侧给参数留位置）。
        "kuaishou" => Layout {
            root: Some(vsplit(
                Ratio(0.50),
                tabs(&[Composition], 0),
                vsplit(
                    Ratio(0.45),
                    tabs(&[Timeline], 0),
                    hsplit(Ratio(0.50), tabs(&[EffectControls], 0), tabs(&[Project], 0)),
                ),
            )),
            floating: Vec::new(),
        },
        // 剪映：竖屏，时间线占比最大（贴手机剪映的排法）。
        "jianying" => portrait(0.46, 0.58),'''

DOCK_TAIL_OLD = '''        _ => {
            // 经典：上游的 Default 工作区。它要是不存在（以后改了名）就给一个最小可用布局，
            // 绝不把用户丢到空界面。
            let classic = workspace("Default");
            if classic.root.is_some() { classic } else { simple() }
        }'''

# ---------------------------------------------------------------- frame.rs
ENTRIES_OLD = '''        let entries: [(&str, &str, &str); 4] = [
            ("classic", "经典", "项目 | 合成 | 属性 | 时间轴"),
            ("simple", "简易", "上预览、下时间轴"),
            ("pro", "专业", "项目 | 预览 | 属性 + 时间轴"),
            ("minimal", "极简", "只有合成预览"),
        ];'''

ENTRIES_NEW = '''        // EFFECTCRAFT_OURS_LAYOUT_BRANDS_V1 — 五套品牌布局，各自真的重排面板。
        let entries: [(&str, &str, &str); 5] = [
            ("ae", "After Effects", "横屏 · 项目 | 预览 | 效果控件 + 底部时间轴"),
            ("capcut", "CapCut", "竖屏 · 上预览、中时间线、下属性/项目"),
            ("blurrr", "Blurrr", "竖屏 · 大预览、薄时间线"),
            ("kuaishou", "快影", "竖屏 · 预览 + 宽属性栏"),
            ("jianying", "剪映", "竖屏 · 预览小、时间线大"),
        ];'''

IDS_OLD = '''    pub(crate) const OURS_LAYOUT_IDS: [&'static str; 4] = ["classic", "simple", "pro", "minimal"];'''
IDS_NEW = '''    pub(crate) const OURS_LAYOUT_IDS: [&'static str; 5] = ["ae", "capcut", "blurrr", "kuaishou", "jianying"];'''

# 卡片内的区域扫光：插在卡片描边之后、缩略图之前
SWEEP_OLD = '''                // 缩略图：真实布局预览（直接按 dock 布局树画，比例就是真实比例）'''
SWEEP_NEW = '''                // EFFECTCRAFT_OURS_LAYOUT_BRANDS_V1 — 区域扫光：每张卡自己的扫描带，
                // 相位错开、只在本卡内可见（跟参考 app 一样是"分区扫描"而不是全屏一条）。
                {
                    let phase = ((e - i as f32 * 0.12) / 1.6).rem_euclid(1.0);
                    let band = 52.0_f32;
                    let bx = r.min.x - band + (r.width() + band * 2.0) * phase;
                    let clip = ui.painter().with_clip_rect(r.shrink(1.0));
                    for (k, a) in [(1.0f32, 0.05f32), (0.5, 0.11), (0.2, 0.20)] {
                        let hw = band * k * 0.5;
                        let g = Rect::from_min_max(
                            Pos2::new(bx - hw, r.min.y),
                            Pos2::new(bx + hw, r.max.y),
                        );
                        clip.rect_filled(g, 12.0, t.accent.gamma_multiply(a * ease));
                    }
                }
                // 缩略图：真实布局预览（直接按 dock 布局树画，比例就是真实比例）'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(DOCK_OLD) != 1:
            raise SystemExit(f"dock anchor: {src.count(DOCK_OLD)}")
        src = src.replace(DOCK_OLD, DOCK_NEW, 1)
        dock.write_text(src, encoding="utf-8")
        print("dock: five brand layouts (landscape + portrait)")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER not in src:
        for name, old, new in (
            ("entries", ENTRIES_OLD, ENTRIES_NEW),
            ("ids", IDS_OLD, IDS_NEW),
            ("sweep", SWEEP_OLD, SWEEP_NEW),
        ):
            if src.count(old) != 1:
                raise SystemExit(f"{name} anchor: {src.count(old)}")
            src = src.replace(old, new, 1)
        frame.write_text(src, encoding="utf-8")
        print("frame: five cards + per-card scan glow")


if __name__ == "__main__":
    main()
