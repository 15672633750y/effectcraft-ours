#!/usr/bin/env python3
"""时间轴里真正的行点击处理有两处，多选标志只补了一处；这里把另一处也接上。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MULTI_ROWS_V1"

OLD = '        if (body.clicked() || body.drag_started()) && !is_sel {\n            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "add": shift})));\n        }'

NEW = '        // EFFECTCRAFT_OURS_MULTI_ROWS_V1 — 多选模式下点行就是加选/取消\n        let multi: bool = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-multi-mode")).unwrap_or(false));\n        if (body.clicked() || body.drag_started()) && (!is_sel || multi) {\n            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": multi, "add": shift})));\n        }'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("row handler already respects multi mode")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("row clicks respect the multi-select mode")


if __name__ == "__main__":
    main()
