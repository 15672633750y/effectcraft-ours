#!/usr/bin/env python3
"""把 .ffx 预设里的参数值真正写进效果（之前只挂效果、不写值）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FFX_VALUES_V1"
HERE = Path(__file__).resolve().parent


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if "fn ffx_values(" in src:
        print("ffx values already applied")
        return
    code = (HERE / "ffx_values.rs").read_text(encoding="utf-8")
    anchor = "/// Apply a preset's effects to the selected layer. Returns how many were added.\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, code + "\n" + anchor, 1)

    old = """    let mut applied = 0usize;
    let mut unknown = Vec::new();
    for id in ids {
        match s.execute("effect.apply", serde_json::json!({"effect": id})) {
            Ok(_) => applied += 1,
            Err(_) => unknown.push(id),
        }
    }
"""
    new = """    let mut applied = 0usize;
    let mut unknown = Vec::new();
    // 预设里的数值：只有在我们认得这个参数名时才写，写不进去就跳过
    let values = ffx_values(&bytes);
    for id in ids {
        match s.execute("effect.apply", serde_json::json!({"effect": id})) {
            Ok(_) => {
                applied += 1;
                let _ = apply_ffx_values(s, id, &values);
            }
            Err(_) => unknown.push(id),
        }
    }
"""
    if src.count(old) != 1:
        raise SystemExit(f"loop anchor: {src.count(old)}")
    src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("ffx preset values are written")


if __name__ == "__main__":
    main()
