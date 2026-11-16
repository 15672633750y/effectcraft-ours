#!/usr/bin/env python3
"""导入按内容识别，不只看后缀：本机动画预设 / .gp 结构 / effects 数组都能进。

Renaming a preset used to break it, because the loader chose its parser by extension. Now a JSON file is
sniffed: our own saved preset (tagged) goes through `anim.applyPreset`, a Sapphire `.gp` shape through the
named-parameter path, and the `effects` array as before.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SNIFF_PRESET_V1"

OLD = '        let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: 预设不是合法 JSON（{e}）")))?;\n        let Some(list) = doc.get("effects").and_then(Value::as_array) else {\n            return Err(EngineError::Other(format!("{path}: JSON 预设缺少 effects 数组")));\n        };\n'

NEW = '        let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: 预设不是合法 JSON（{e}）")))?;\n        // EFFECTCRAFT_OURS_SNIFF_PRESET_V1 — 不看后缀，看内容：\n        // 1) 我们自己保存的动画预设（带 tag 和 properties）  2) Sapphire 的 .gp 结构  3) 我们的 effects 数组\n        if doc.get("effectcraftAnimationPreset").is_some() {\n            let n = s.execute("anim.applyPreset", json!({ "path": path }))?;\n            return Ok(n.get("effects").and_then(Value::as_u64).unwrap_or(0) as usize);\n        }\n        if doc.get("name").and_then(Value::as_str).is_some() && doc.get("params").is_some() {\n            return super::import_ext::apply_gp(s, path);\n        }\n        let Some(list) = doc.get("effects").and_then(Value::as_array) else {\n            return Err(EngineError::Other(format!("{path}: 认不出这个 JSON 预设（既不是 effects 数组，也不是 .gp 或本机预设）")));\n        };\n'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("presets are already sniffed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("preset import sniffs the content")


if __name__ == "__main__":
    main()
