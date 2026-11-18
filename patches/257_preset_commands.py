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
        "ours.exportPreset",
        "导出预设",
        ["path"],
        None,
        "{path: 保存到哪个文件}",
        always,
        export_preset
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
                // 看文件头区分：`{` 开头是我们自己导出的 JSON 预设，`RIFX` 是 AE 二进制，
                // `<` 是少见的 XML 版 .ffx。
                let kind = if low.ends_with(".gp") {
                    "gp"
                } else {
                    let head = std::fs::read(&path).map(|b| b[..b.len().min(8)].to_vec()).unwrap_or_default();
                    let text = String::from_utf8_lossy(&head).to_string();
                    if text.trim_start().starts_with('{') {
                        "local"
                    } else if head.starts_with(b"RIFX") {
                        "rifx"
                    } else if text.trim_start().starts_with('<') {
                        "xml"
                    } else {
                        "unknown"
                    }
                };
                let label = match kind {
                    "gp" => "Sapphire .gp",
                    "local" => "本机预设",
                    "rifx" => "AE 二进制",
                    "xml" => "AE 文本",
                    _ => "未知格式",
                };
                items.push(json!({
                    "name": name.trim_end_matches(|c: char| c == '.' ).to_string(),
                    "path": path.to_string_lossy(),
                    "kind": kind,
                    "label": label,
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
    // 统一结果：{applied, missing, skipped, failed, warnings}。
    // 不做「整包拒绝」：格式认不出也只是 warnings 里的一条，界面照常报结果。
    match super::import_ext::apply_preset_report(s, &path) {
        Ok((applied, missing)) => Ok(json!({
            "applied": applied,
            "effects": applied,
            "missing": missing,
            "skipped": [],
            "failed": [],
            "warnings": [],
        })),
        Err(e) => {
            let text = e.to_string();
            if text.contains("无法识别的预设格式") {
                Ok(json!({
                    "applied": 0,
                    "effects": 0,
                    "missing": [],
                    "skipped": [],
                    "failed": [],
                    "warnings": ["这个文件里没有可识别的预设内容"],
                }))
            } else {
                Ok(json!({
                    "applied": 0,
                    "effects": 0,
                    "missing": [],
                    "skipped": [],
                    "failed": [text],
                    "warnings": [],
                }))
            }
        }
    }
}

/// 值 → JSON（只导标量/向量/颜色/布尔/枚举/字符串；路径、文本、图层引用跳过）。
fn prop_value_json(value: &effectcraft_project::Value) -> Option<serde_json::Value> {
    use effectcraft_project::Value as V;
    Some(match value {
        V::Scalar(f) => json!(f),
        V::Vec2(a) => json!(a),
        V::Vec3(a) => json!(a),
        V::Color(c) => json!(c),
        V::Bool(b) => json!(b),
        V::Enum(i) => json!(i),
        V::Str(s) => json!(s),
        _ => return None,
    })
}

/// EFFECTCRAFT_OURS_EXPORT_PRESET_V1 — 把选中图层的效果栈写成 JSON 预设。
/// 上游没有导出预设的功能（保存出来是 0 字节），所以这条链路自己算参数值。
pub(crate) fn export_preset(s: &mut Session, p: &Value) -> Result<Value> {
    let path = str_p(p, "path").unwrap_or("").to_string();
    if path.is_empty() {
        return Err(bad("ours.exportPreset", "no path"));
    }
    let comp = s.active_comp().ok_or(crate::EngineError::NoComp)?;
    // selected_layers 是 Vec<LayerId>，参数里给的 layers 是数字：统一成 LayerId。
    let lid: effectcraft_project::LayerId = if let Some(list) = p.get("layers").and_then(Value::as_array) {
        list.first().and_then(Value::as_u64).map(effectcraft_project::LayerId)
    } else {
        s.state.selected_layers.first().copied()
    }
    .ok_or_else(|| bad("ours.exportPreset", "先选中一个图层"))?;
    let layer = comp.layer(lid).ok_or_else(|| bad("ours.exportPreset", "no layer"))?;
    let Some(effects) = layer.props.sub("effects") else {
        return Err(bad("ours.exportPreset", "这个图层没有效果"));
    };
    let mut list: Vec<Value> = Vec::new();
    for group in effects.groups() {
        let mut params = serde_json::Map::new();
        for prop in group.props() {
            if let Some(v) = prop_value_json(&prop.value) {
                params.insert(prop.name.clone(), v);
            }
        }
        list.push(json!({
            "id": group.match_id,
            "name": group.name,
            "params": params,
        }));
    }
    if list.is_empty() {
        return Err(bad("ours.exportPreset", "这个图层没有效果"));
    }
    let name = std::path::Path::new(&path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_else(|| "Preset".to_string());
    let doc = json!({
        "format": "effectcraft.preset.v1",
        "name": name,
        "effects": list,
    });
    let text = serde_json::to_string_pretty(&doc).map_err(|e| crate::EngineError::Other(format!("序列化失败: {e}")))?;
    std::fs::write(&path, text).map_err(|e| crate::EngineError::Other(format!("写不进 {path}: {e}")))?;
    Ok(json!({ "path": path, "effects": list.len() }))
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
