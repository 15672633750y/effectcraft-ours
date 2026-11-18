#!/usr/bin/env python3
"""「布局」按钮：放回正常绘制流，只是提前到所有浮层之前。

之前它被画在 539-548 那一段浮层之后，所以永远盖着预设库/导入/云端面板。
改成独立 Area 又因为 `draw_layout_switcher` 内部按自己算的位置 + clip_rect 绘制而看不见。

最终做法最简单：仍用原来的绘制调用，只是插在 `shortcut_panel(...)` 之前。
- 位置/动画/点击/字体全部保持原样（画布右上角）
- 浮层在这之后绘制，自然盖住它
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1"

ANCHOR = "        shortcut_panel(self, ui, full);\n"

INSERT = """        // EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1 — 「布局」在任何浮层之前绘制，
        // 所以预设库/导入/云端/账号面板都会盖住它（以前它最后画，永远最上层）。
        let layout_crashed =
            ui.data(|d| d.get_temp::<bool>(egui::Id::new("ours-layout-crashed")).unwrap_or(false));
        if !layout_crashed
            && std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                self.draw_layout_switcher(ui, full)
            }))
            .is_err()
        {
            ui.data_mut(|d| d.insert_temp(egui::Id::new("ours-layout-crashed"), true));
            ui.data_mut(|d| d.remove::<f64>(egui::Id::new("layout-open-at")));
            self.ours_layout_error("switcher", "panic inside draw_layout_switcher");
        }
        shortcut_panel(self, ui, full);
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("layout call already moved")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    frame.write_text(src.replace(ANCHOR, INSERT, 1), encoding="utf-8")
    print("布局 drawn before the floating panels (so they cover it)")


if __name__ == "__main__":
    main()
