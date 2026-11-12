#!/usr/bin/env python3
"""As the timeline column narrows, optional columns drop out so the switches stay usable."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TIMELINE_COLUMNS_V1"
OLD = "impl Vis {\n    fn of(tl: &crate::state::TimelineState) -> Vis {\n"
NEW = OLD + '''        // `LEFT_EXTRA` is what the user dragged the divider by: as the column narrows, the
        // optional columns step aside instead of squeezing the switches off the pane.
        let extra = LEFT_EXTRA.with(|c| c.get());
'''

TAIL_OLD = "        Vis {\n            av: v(\"av\"),"
TAIL_NEW = '''        let mut vis = Vis {
            av: v("av"),'''

POST_OLD = "            stretch: v(\"stretch\"),\n        }\n    }"
POST_NEW = '''            stretch: v("stretch"),
        };
        if extra < -30.0 {
            vis.comment = false;
            vis.stretch = false;
            vis.in_ = false;
            vis.out = false;
            vis.duration = false;
        }
        if extra < -120.0 {
            vis.modes = false;
            vis.parent = false;
        }
        if extra < -220.0 {
            vis.num = false;
            vis.label = false;
        }
        vis
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("adaptive columns already installed")
        return
    for old, new in ((OLD, NEW), (TAIL_OLD, TAIL_NEW), (POST_OLD, POST_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}: {old[:40]}")
        src = src.replace(old, new, 1)
    src = src.replace("struct Vis {", "// " + MARKER + "\nstruct Vis {", 1)
    path.write_text(src, encoding="utf-8")
    print("optional timeline columns drop out as the column narrows")


if __name__ == "__main__":
    main()
