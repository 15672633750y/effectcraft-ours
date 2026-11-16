#!/usr/bin/env python3
"""Sapphire 的 `.gp` 预设：文本 JSON，参数名和数值都写在里面，直接按名字套。

A `.gp` preset is plain text:

    {"name":"S_VintageColor3Strip"} … # segment separator …
    {"params":{"amount":{"channels":[{"value":0.42}]}, …}}

so the names (`amount`, `brightness`, `offset_darks`…) and their values are readable — unlike AE's
`.ffx`, which addresses parameters by opaque ids. Importing one applies the effect and writes exactly
those numbers.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GP_PRESET_V1"

FN = r'''
/// `offset_darks` → `offsetDarks`：Sapphire 用 snake_case，我们用 camelCase。
fn gp_param_name(name: &str) -> Option<&'static str> {
    Some(match name {
        "amount" => "amount",
        "brightness" => "brightness",
        "saturation" => "saturation",
        "offset_darks" => "offsetDarks",
        "key_layer_density" => "keyLayerDensity",
        "grain_amp" => "grainAmp",
        "grain_blur" => "grainBlur",
        "blur_mask" => "blurMask",
        "invert_mask" => "invertMask",
        "mask_use" => "maskUse",
        "show" => "show",
        "tint" => "tint",
        "effect" => "effect",
        "squareness" => "squareness",
        "radius" => "radius",
        "rel_height" => "relHeight",
        "rel_width" => "relWidth",
        "rotate" => "rotate",
        "edge_softness" => "edgeSoftness",
        "smooth_curve" => "smoothCurve",
        "color" => "color",
        "opacity" => "opacity",
        "blur_amount" => "blurAmount",
        "blur_inside" => "blurInside",
        "source_brightness" => "sourceBrightness",
        "combine" => "combine",
        _ => return None,
    })
}

/// 每个 `{"channels":[{"value":…}], "type": …}` 取出值（颜色是 3/4 个通道）。
fn gp_value(v: &Value) -> Option<Value> {
    let chans = v.get("channels")?.as_array()?;
    let mut nums: Vec<f64> = chans.iter().filter_map(|c| c.get("value").and_then(Value::as_f64)).collect();
    if nums.is_empty() {
        return None;
    }
    let kind = v.get("type").and_then(Value::as_str).unwrap_or("float");
    match kind {
        "color" => {
            while nums.len() < 4 {
                nums.push(1.0);
            }
            Some(json!([nums[0], nums[1], nums[2], nums[3]]))
        }
        "popup" => Some(json!(nums[0] as i64)),
        _ => Some(json!(nums[0])),
    }
}

/// 套一个 `.gp` 预设；返回应用的效果数。
pub(crate) fn apply_gp(s: &mut Session, path: &str) -> Result<usize> {
    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes);
    let mut effect: Option<String> = None;
    let mut params: Vec<(String, Value)> = Vec::new();
    for seg in text.split("# segment separator do not remove this line") {
        let body = seg.trim();
        let start = body.find('{');
        let Some(start) = start else { continue };
        let Some(doc) = serde_json::from_str::<Value>(&body[start..]).ok() else { continue };
        if let Some(name) = doc.get("name").and_then(Value::as_str) {
            effect = Some(name.to_string());
        }
        if let Some(map) = doc.get("params").and_then(Value::as_object) {
            for (k, v) in map {
                if let Some(value) = gp_value(v) {
                    params.push((k.clone(), value));
                }
            }
        }
    }
    let Some(effect) = effect else {
        return Err(EngineError::Other(format!("{path}: 预设里没有效果名")));
    };
    let id = match effect.as_str() {
        "S_VintageColor3Strip" => "S_VintageColor3Strip",
        "S_VintagColor3Strip" => "S_VintageColor3Strip",
        "S_VintageColor2Strip" => "org.effectcraft.compat.sapphire.vintagecolor2strip",
        "S_Vignette" => "S_Vignette",
        other => {
            return Err(EngineError::Other(format!("{path}: 本机还没有 {other} 的实现")));
        }
    };
    s.execute("effect.apply", json!({ "effect": id }))?;
    let mut set = 0usize;
    for (name, value) in params {
        let Some(param) = gp_param_name(&name) else { continue };
        if s.execute("prop.set", json!({"path": format!("effects/{id}/{param}"), "value": value})).is_ok() {
            set += 1;
        }
    }
    Ok(1 + set / 100)
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(".gp presets already supported")
        return
    anchor = "/// Apply a preset's effects to the selected layer. Returns how many were added.\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    # 让 apply_ffx 里对 .gp 走这条分支
    hook_old = "    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!(\"cannot read {path}: {e}\")))?;\n    let text = String::from_utf8_lossy(&bytes);\n"
    hook_new = hook_old + "    if path.to_ascii_lowercase().ends_with(\".gp\") {\n        return apply_gp(s, path);\n    }\n"
    if src.count(hook_old) < 1:
        raise SystemExit(f"hook anchor: {src.count(hook_old)}")
    src = src.replace(hook_old, hook_new, 1)
    path.write_text(src, encoding="utf-8")
    print(".gp presets apply their named values")


if __name__ == "__main__":
    main()
