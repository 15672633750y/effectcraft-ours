#!/usr/bin/env python3
"""保存动画预设时用 `.ffx` 后缀（系统对话框给的是 `.bin`），这样导出就能被本机导入/预设库识别。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_FFX_NAME_V1"

OLD = """    let doc = json!({PRESET_TAG: PRESET_VERSION, "name": name, "properties": props_json, "effects": fx_json});
    let text = serde_json::to_string_pretty(&doc).unwrap_or_default();
    s.write_output(&path, text.as_bytes())?;
"""

NEW = """    let doc = json!({PRESET_TAG: PRESET_VERSION, "name": name, "properties": props_json, "effects": fx_json});
    let text = serde_json::to_string_pretty(&doc).unwrap_or_default();
    // EFFECTCRAFT_OURS_PRESET_FFX_NAME_V1 — 保存成 .ffx（系统对话框默认给 .bin，导入不认）
    let path = {
        let lower = path.to_ascii_lowercase();
        if lower.ends_with(".bin") {
            format!("{}.ffx", &path[..path.len() - 4])
        } else if !std::path::Path::new(&path).extension().is_some() {
            format!("{path}.ffx")
        } else {
            path
        }
    };
    s.write_output(&path, text.as_bytes())?;
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/animation.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset already saved as .ffx")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("saved presets get the .ffx extension")


if __name__ == "__main__":
    main()
