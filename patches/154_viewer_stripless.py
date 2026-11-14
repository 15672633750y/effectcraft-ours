#!/usr/bin/env python3
"""The composition viewer draws no tab strip: its picture starts at the top of the frame.

craft-ui already has the idea — a lone *protected* panel ("a document canvas") draws no strip and
no drag bar — the app just never told it the viewer is one. `permissions()` now says so for the
Composition panel, so when the viewer is alone in its frame the strip and its bar disappear and the
canvas takes that height. A frame where the viewer shares tabs with another panel keeps its strip
(a protected panel takes no new tabs, so this is the only case it can be in).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_VIEWER_STRIPLESS_V1"

ANCHOR = "    fn group_header_width(&self, _panels: &[PanelKind], active: &PanelKind, _floating: bool, strip_width: f32) -> f32 {\n"
ADD = '''    // EFFECTCRAFT_OURS_VIEWER_STRIPLESS_V1 — 合成预览是画布：单独成组时不画标签条，画面顶到最上面
    fn permissions(&self, panel: &PanelKind) -> craft_ui::docking::Permissions {
        if matches!(panel, PanelKind::Composition) {
            craft_ui::docking::Permissions::PROTECTED
        } else {
            craft_ui::docking::Permissions::default()
        }
    }

'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("viewer is already stripless")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, ADD + ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    print("composition viewer is a protected canvas")


if __name__ == "__main__":
    main()
