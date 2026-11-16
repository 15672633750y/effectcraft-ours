#!/usr/bin/env python3
"""修借用错误：音频提示不能在 `comp` 借用期间调用 frontend，改到循环之后。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_BORROW_V1"

EDITS = [('    let mut out = vec![];\n    for lid in &layers {\n        let Some(l) = comp.layer(*lid) else { continue };\n        // EFFECTCRAFT_OURS_AUDIO_REVEAL_V1', '    let mut out = vec![];\n    let mut no_audio = false;\n    for lid in &layers {\n        let Some(l) = comp.layer(*lid) else { continue };\n        // EFFECTCRAFT_OURS_AUDIO_REVEAL_V1'), ('            if found == 0 {\n                // 没有音频的图层（图片/纯色）不报错，只提示\n                frontend(s, "ui.status", &json!({"text": "该图层没有音频属性（图片或纯色层）"}))?;\n                continue;\n            }\n', '            if found == 0 {\n                // 没有音频的图层（图片/纯色）不报错，等循环结束后再提示（借用到那时已结束）\n                no_audio = true;\n                continue;\n            }\n'), ('    if out.is_empty() {\n        return Err(bad("layer.revealProperty", "the layer has no such property"));\n    }\n', '    if no_audio && out.is_empty() {\n        frontend(s, "ui.status", &json!({"text": "该图层没有音频属性（图片或纯色层）"}))?;\n        return Ok(json!({"props": []}));\n    }\n    if out.is_empty() {\n        return Err(bad("layer.revealProperty", "the layer has no such property"));\n    }\n')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/animation.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("audio borrow already fixed")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("audio hint moved out of the borrow")


if __name__ == "__main__":
    main()
