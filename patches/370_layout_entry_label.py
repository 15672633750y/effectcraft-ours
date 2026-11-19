#!/usr/bin/env python3
"""「布局」入口显示当前布局名（After Effects / CapCut / …），切换后立刻能看出生效了。

原来入口永远写「布局」，切完只有中央浮出的名字提示；现在入口本身跟着当前布局变，
再切回来时也不会记不清用的是哪套。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_ENTRY_LABEL_V1"

OLD = '''        p.text(r.center(), Align2::CENTER_CENTER, "布局", Tokens::ui(12.0), Color32::from_rgba_unmultiplied(t.text.r(), t.text.g(), t.text.b(), (255.0 * fade) as u8));
        self.auto.add("layout.switcher", r, "布局");'''

NEW = '''        // EFFECTCRAFT_OURS_LAYOUT_ENTRY_LABEL_V1 — 入口显示当前布局名，切换后一眼可见。
        let label = match self.ui.workspace.as_str() {
            "ae" | "classic" | "pro" => "AE",
            "capcut" | "simple" => "CapCut",
            "blurrr" | "minimal" => "Blurrr",
            "kuaishou" => "快影",
            "jianying" => "剪映",
            _ => "布局",
        };
        p.text(r.center(), Align2::CENTER_CENTER, label, Tokens::ui(12.0), Color32::from_rgba_unmultiplied(t.text.r(), t.text.g(), t.text.b(), (255.0 * fade) as u8));
        self.auto.add("layout.switcher", r, label);'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("entry label already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("layout entry shows the current layout name")


if __name__ == "__main__":
    main()
