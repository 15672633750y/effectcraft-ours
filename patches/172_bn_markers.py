#!/usr/bin/env python3
"""Two toolbar buttons after undo/redo: B and N, the work-area in and out points of After Effects.

B sets the work area's start to the playhead, N its end — the same two keys as AE. The buttons are
the same size and spacing as the undo/redo pair they follow (30×26, 34 apart), drawn as text so no
font glyph is needed. The work is done by the engine's existing `comp.workArea` command with
`set: "begin"` / `set: "end"`, so undo, the automation tree and scripting all see it as usual.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BN_MARKERS_V1"

OLD = "        x += 34.0;\n    }\n    x\n}\n"
NEW = '''        x += 34.0;
    }

    // EFFECTCRAFT_OURS_BN_MARKERS_V1 — B/起点、N/终点，和 AE 的两个键一样
    if let Some(cid) = app.session.active_comp_id() {
        for (label, tip, set) in [("B", "把工作区起点设到当前帧", "begin"), ("N", "把工作区终点设到当前帧", "end")] {
            let r = Rect::from_min_size(pos2(x, cy - 13.0), vec2(30.0, 26.0));
            let resp = ui.interact(r, egui::Id::unique(("ours-bn", set)), Sense::click());
            p.rect_filled(r, 5.0, t.switch_well);
            p.text(r.center(), Align2::CENTER_CENTER, label, Tokens::ui(12.0), t.text);
            if resp.on_hover_text(tip).clicked() {
                let _ = crate::menus::invoke(app, ui.ctx(), "comp.workArea", serde_json::json!({"comp": cid.0, "set": set}));
                app.ui.status = if set == "begin" { "工作区起点已设到当前帧".into() } else { "工作区终点已设到当前帧".into() };
            }
            x += 34.0;
        }
    }
    x
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    candidates = [p for p in (root / "crates/ui-egui/src").rglob("*.rs") if OLD in p.read_text(encoding="utf-8", errors="ignore")]
    if not candidates:
        raise SystemExit("undo/redo toolbar block not found")
    path = candidates[0]
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("B/N buttons already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("B and N buttons added after undo/redo")


if __name__ == "__main__":
    main()
