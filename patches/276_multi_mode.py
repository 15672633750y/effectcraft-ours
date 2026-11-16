#!/usr/bin/env python3
"""多选：面板加「多选」按钮（M），打开后点图层就是加选/取消——长按在触摸上不可靠，改用显式模式。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_MULTI_TOGGLE_V1"

EDITS = [('            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": m.command})));', '            // EFFECTCRAFT_OURS_MULTI_TOGGLE_V1 — 「多选」打开时，点一下就是加选/取消\n            let multi: bool = ctx.data(|d| d.get_temp::<bool>(egui::Id::new("ours-multi-mode")).unwrap_or(false));\n            actions.push(("layer.select".into(), json!({"layers": [layer.id.0], "toggle": m.command || multi})));'), ('        ("音频频谱", "L", "layer.revealProperty", serde_json::json!({"prop": "audio"})),\n    ];', '        ("音频频谱", "L", "layer.revealProperty", serde_json::json!({"prop": "audio"})),\n        ("多选", "M", "ours.multiSelect", serde_json::json!({})),\n    ];'), ('    let size = egui::vec2(196.0, 232.0);\n', '    let size = egui::vec2(196.0, 280.0);\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    tl = root / "crates/ui-egui/src/panels/timeline.rs"
    fr = root / "crates/ui-egui/src/app/frame.rs"
    a = tl.read_text(encoding="utf-8")
    b = fr.read_text(encoding="utf-8")
    if MARKER in a:
        print("multi-select mode already present")
        return
    (c_o, c_n), (t_o, t_n), (s_o, s_n) = EDITS
    if a.count(c_o) != 1:
        raise SystemExit(f"click anchor: {a.count(c_o)}")
    tl.write_text(a.replace(c_o, c_n, 1), encoding="utf-8")
    for o, n in ((t_o, t_n), (s_o, s_n)):
        if b.count(o) != 1:
            raise SystemExit(f"frame anchor: {b.count(o)}")
        b = b.replace(o, n, 1)
    fr.write_text(b, encoding="utf-8")
    print("multi-select mode added")


if __name__ == "__main__":
    main()
