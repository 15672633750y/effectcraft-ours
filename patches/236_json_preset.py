#!/usr/bin/env python3
"""`.ffx` 也能是 JSON：我们自己写的预设文件，带效果名和每个参数的数值。

AE's `.ffx` stores parameters by opaque ids, so values cannot be recovered from it. A JSON preset is
readable: `{"effects":[{"effect":"S_VintageColor3Strip","params":{"amount":1.0,...}}, ...]}`.
`apply_ffx` now notices a file that starts with `{` and applies exactly that chain.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_JSON_PRESET_V1"

OLD = """    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes);
"""
NEW = """    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes);
    // EFFECTCRAFT_OURS_JSON_PRESET_V1 — JSON 预设：效果名 + 数值
    if bytes.first() == Some(&b'{') {
        let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: 预设不是合法 JSON（{e}）")))?;
        let Some(list) = doc.get("effects").and_then(Value::as_array) else {
            return Err(EngineError::Other(format!("{path}: JSON 预设缺少 effects 数组")));
        };
        let mut applied = 0usize;
        for item in list {
            let Some(id) = item.get("effect").and_then(Value::as_str) else { continue };
            s.execute("effect.apply", serde_json::json!({"effect": id}))?;
            applied += 1;
            if let Some(params) = item.get("params").and_then(Value::as_object) {
                for (name, value) in params {
                    let _ = s.execute(
                        "prop.set",
                        serde_json::json!({"path": format!("effects/{id}/{name}"), "value": value.clone()}),
                    );
                }
            }
        }
        if applied == 0 {
            return Err(EngineError::Other(format!("{path}: 预设里没有可用的效果")));
        }
        return Ok(applied);
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("JSON presets already supported")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("JSON presets are applied with their values")


if __name__ == "__main__":
    main()
