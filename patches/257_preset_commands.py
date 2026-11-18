#!/usr/bin/env python3
"""预设库：扫描 `DCIM/EffectCraft/Presets`，列出来/一键套用，不用每次手动导入。

`ours.presets` returns `[{name, path, kind}]` for every `.ffx` / `.gp` / `.json` preset in the folder;
`ours.applyPreset {path}` runs the same loader the import dialog uses, on the selected layer.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRESET_LIB_V1"

SPEC_OLD = """    ), cmd!(
        "ours.shareFile","""
SPEC_NEW = """    ), cmd!(
        "ours.presets",
        "预设库列表",
        [],
        None,
        "{}",
        always,
        list_presets
    ), cmd!(
        "ours.applyPreset",
        "套用预设",
        ["path"],
        None,
        "{path: 预设文件路径}",
        always,
        apply_preset
    ), cmd!(
        "ours.shareFile","""

FN = r'''

/// EFFECTCRAFT_OURS_PRESET_LIB_V1 — 预设目录：放进去就能在面板里看到。
pub(crate) fn preset_dir() -> std::path::PathBuf {
    std::path::PathBuf::from("/storage/emulated/0/DCIM/EffectCraft/Presets")
}

/// 目录里所有可用预设（按文件名排序）。
fn list_presets(_s: &mut Session, _p: &Value) -> Result<Value> {
    let dir = preset_dir();
    let _ = std::fs::create_dir_all(&dir);
    let mut items: Vec<Value> = Vec::new();
    if let Ok(rd) = std::fs::read_dir(&dir) {
        for e in rd.flatten() {
            let path = e.path();
            let name = e.file_name().to_string_lossy().to_string();
            let low = name.to_ascii_lowercase();
            if low.ends_with(".ffx") || low.ends_with(".gp") || low.ends_with(".json") {
                items.push(json!({
                    "name": name.trim_end_matches(|c: char| c == '.' ).to_string(),
                    "path": path.to_string_lossy(),
                    "kind": if low.ends_with(".gp") { "gp" } else if low.ends_with(".json") { "json" } else { "ffx" },
                }));
            }
        }
    }
    items.sort_by(|a, b| a["name"].as_str().unwrap_or("").cmp(b["name"].as_str().unwrap_or("")));
    Ok(json!({ "dir": dir.to_string_lossy(), "items": items }))
}

/// 套用一个预设文件到选中图层。
fn apply_preset(s: &mut Session, p: &Value) -> Result<Value> {
    let path = str_p(p, "path").unwrap_or("").to_string();
    if path.is_empty() {
        return Err(bad("ours.applyPreset", "no path"));
    }
    // 不能只回一个数字：面板要能把「缺哪些效果」说清楚。
    match super::import_ext::apply_preset_report(s, &path) {
        Ok((applied, missing)) => Ok(json!({ "effects": applied, "missing": missing, "unsupported": false })),
        // 格式本身不认得（不是 RIFX 也不是 XML）：单独标出来，面板好说「格式不支持」。
        Err(e) if e.to_string().contains("无法识别的预设格式") => {
            Ok(json!({ "effects": 0, "missing": [], "unsupported": true, "why": e.to_string() }))
        }
        Err(e) => Err(e),
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preset library commands already present")
        return
    if src.count(SPEC_OLD) != 1:
        raise SystemExit(f"spec anchor: {src.count(SPEC_OLD)}")
    src = src.replace(SPEC_OLD, SPEC_NEW, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("preset library commands added")


if __name__ == "__main__":
    main()
