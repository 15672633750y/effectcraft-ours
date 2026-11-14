#!/usr/bin/env python3
"""The composition viewer's frame has no tab strip: the picture starts at the top of the panel.

craft-ui already has this — "a lone protected panel (a document canvas) draws no strip and no drag
bar" — but the default workspace puts the viewer in the same tab group as the Layer panel, so it is
never lone. Two changes:

* the Composition panel is declared a canvas (`Permissions::PROTECTED`);
* the default workspaces stop grouping Layer with Composition, so the canvas really is alone.

An existing saved layout keeps its own arrangement; 窗口 ▸ 工作区 ▸ 默认 applies the new default.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CANVAS_V1"

PERM_ANCHOR = "    fn group_header_width(&self, _panels: &[PanelKind], active: &PanelKind, _floating: bool, strip_width: f32) -> f32 {\n"
PERM_ADD = '''    // EFFECTCRAFT_OURS_CANVAS_V1 — 合成预览是画布：单独成组时不画标签条，画面顶到最上面
    fn permissions(&self, panel: &PanelKind) -> craft_ui::docking::Permissions {
        if matches!(panel, PanelKind::Composition) {
            craft_ui::docking::Permissions::PROTECTED
        } else {
            craft_ui::docking::Permissions::default()
        }
    }

'''

LAYOUT_OLD = "tabs(&[Composition, Layer], 0)"
LAYOUT_NEW = "tabs(&[Composition], 0)"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/dock_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(PERM_ANCHOR) != 1:
            raise SystemExit(f"perm anchor: {src.count(PERM_ANCHOR)}")
        src = src.replace(PERM_ANCHOR, PERM_ADD + PERM_ANCHOR, 1)
        path.write_text(src, encoding="utf-8")
        print("viewer is a canvas")

    dock = root / "crates/ui-egui/src/dock.rs"
    src = dock.read_text(encoding="utf-8")
    if MARKER not in src:
        n = src.count(LAYOUT_OLD)
        if n == 0:
            print("no Composition+Layer groups to change")
        else:
            src = src.replace(LAYOUT_OLD, LAYOUT_NEW)
            dock.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
            print(f"{n} default layouts keep the canvas alone")


if __name__ == "__main__":
    main()
