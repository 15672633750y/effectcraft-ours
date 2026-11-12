#!/usr/bin/env python3
"""The timeline's header row gives up space as the column narrows instead of overlapping."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_ADAPTIVE_V1"

OLD = '    let sr = Rect::from_min_size(pos2(tc_rect.max.x + 14.0, top + 12.0), vec2((left_w - 420.0).clamp(120.0, 220.0), 22.0));\n    let mut search = app.ui.timeline.search.clone();\n    widgets::search_field(ui, sr, &mut search, crate::i18n::tr("Search"), &t);\n    app.ui.timeline.search = search;\n    app.auto.add("timeline.search", sr, "Search");\n'

NEW = '''    // The row shrinks with the column: the search field narrows, then disappears, and the
    // switches stop before they run into it.
    let room = (left_w - 250.0).clamp(0.0, 220.0);
    let sr = Rect::from_min_size(pos2(tc_rect.max.x + 14.0, top + 12.0), vec2(room.max(1.0), 22.0));
    if room >= 90.0 {
        let mut search = app.ui.timeline.search.clone();
        widgets::search_field(ui, sr, &mut search, crate::i18n::tr("Search"), &t);
        app.ui.timeline.search = search;
        app.auto.add("timeline.search", sr, "Search");
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("timeline header already adaptive")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"search anchor: {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    # Stop the switch row before it overlaps the search field.
    loop_old = '    for (icon, on, id, tip) in [\n        (Icon::Graph, app.ui.timeline.graph_editor, "graph", "Graph Editor"),'
    loop_new = '    let stop_x = if room >= 90.0 { sr.max.x + 8.0 } else { tc_rect.max.x + 8.0 };\n    for (icon, on, id, tip) in [\n        (Icon::Graph, app.ui.timeline.graph_editor, "graph", "Graph Editor"),'
    if src.count(loop_old) != 1:
        raise SystemExit("switch loop anchor missing")
    src = src.replace(loop_old, loop_new, 1)
    body_old = '        let r = Rect::from_min_size(pos2(bx - 24.0, top + 11.0), vec2(24.0, 24.0));\n'
    body_new = '        if bx - 24.0 < stop_x {\n            break;\n        }\n' + body_old
    if src.count(body_old) != 1:
        raise SystemExit("switch rect anchor missing")
    src = src.replace(body_old, body_new, 1)
    src = src.replace("fn header_search_and_switches(", "// " + MARKER + "\nfn header_search_and_switches(", 1)
    path.write_text(src, encoding="utf-8")
    print("timeline header row adapts to the column width")




if __name__ == "__main__":
    main()
