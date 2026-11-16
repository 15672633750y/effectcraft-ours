#!/usr/bin/env python3
"""快捷键补全：预合成 Ctrl+Shift+C、音频频谱 L；面板加高一行放得下。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHORTCUT_MORE_V1"

EDITS = [('        for top in l.props.groups() {\n            if top.match_id != "transform" {\n                continue;\n            }\n            if let Some(pr) = top.get(&want) {\n                out.push(json!({"layer": lid.0, "prop": pr.uid}));\n            }\n        }\n', '        // EFFECTCRAFT_OURS_AUDIO_REVEAL_V1 — 音频组（音量/电平）也能展开\n        if want == "audio" {\n            for top in l.props.groups() {\n                if top.match_id != "audio" {\n                    continue;\n                }\n                for pr in top.props() {\n                    out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                }\n                for sub in top.groups() {\n                    for pr in sub.props() {\n                        out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                    }\n                }\n            }\n            continue;\n        }\n        for top in l.props.groups() {\n            if top.match_id != "transform" {\n                continue;\n            }\n            if let Some(pr) = top.get(&want) {\n                out.push(json!({"layer": lid.0, "prop": pr.uid}));\n            }\n        }\n'), ('        ("关键帧", "U", "anim.reveal", serde_json::json!({"kind": "keyframes"})),\n    ];', '        ("关键帧", "U", "anim.reveal", serde_json::json!({"kind": "keyframes"})),\n        ("预合成", "Ctrl+Shift+C", "layer.precompose", serde_json::json!({})),\n        ("音频频谱", "L", "layer.revealProperty", serde_json::json!({"prop": "audio"})),\n    ];'), ('    let size = egui::vec2(196.0, 184.0);\n', '    let size = egui::vec2(196.0, 232.0);\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frames = root / "crates/ui-egui/src/app/frame.rs"
    anim = root / "crates/engine/src/cmd/animation.rs"
    fs = frames.read_text(encoding="utf-8")
    if MARKER in fs:
        print("extra shortcuts already present")
        return
    (eng_o, eng_n), (t_o, t_n), (s_o, s_n) = EDITS
    a = anim.read_text(encoding="utf-8")
    if a.count(eng_o) != 1:
        raise SystemExit(f"engine anchor: {a.count(eng_o)}")
    anim.write_text(a.replace(eng_o, eng_n, 1), encoding="utf-8")
    for o, n in ((s_o, s_n), (t_o, t_n)):
        if fs.count(o) != 1:
            raise SystemExit(f"ui anchor: {fs.count(o)}")
        fs = fs.replace(o, n, 1)
    frames.write_text(fs, encoding="utf-8")
    print("precompose + audio shortcut added")


if __name__ == "__main__":
    main()
