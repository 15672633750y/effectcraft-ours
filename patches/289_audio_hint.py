#!/usr/bin/env python3
"""L 音频频谱：没有音频的图层改为中文提示，不再抛英文错误。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_HINT_V1"

OLD = '        if want == "audio" {\n            for top in l.props.groups() {\n                if top.match_id != "audio" {\n                    continue;\n                }\n                for pr in top.props() {\n                    out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                }\n                for sub in top.groups() {\n                    for pr in sub.props() {\n                        out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                    }\n                }\n            }\n            continue;\n        }'

NEW = '        if want == "audio" {\n            let mut found = 0usize;\n            for top in l.props.groups() {\n                if top.match_id != "audio" {\n                    continue;\n                }\n                for pr in top.props() {\n                    out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                    found += 1;\n                }\n                for sub in top.groups() {\n                    for pr in sub.props() {\n                        out.push(json!({"layer": lid.0, "prop": pr.uid}));\n                        found += 1;\n                    }\n                }\n            }\n            if found == 0 {\n                // 没有音频的图层（图片/纯色）不报错，只提示\n                frontend(s, "ui.status", &json!({"text": "该图层没有音频属性（图片或纯色层）"}))?;\n                continue;\n            }\n            continue;\n        }'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/animation.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("audio hint already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("audio reveal gives a Chinese hint")


if __name__ == "__main__":
    main()
