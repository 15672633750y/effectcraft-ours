#!/usr/bin/env python3
"""文字动画器导入：`.ffx` 里的 `Evaporate Animator`（蒸发）。

1. `crates/engine/presets/text_animators.json` 新增内置预设 `evaporate`（名字「蒸发」）。
   数值取自 `inbox/奇峰自由文字出场.ffx`：范围选择器 Percent End 100、Max Amount 100、
   Smoothness 100、Range Shape 3（AE 的 Ramp Down → 我们枚举下标 2）、Randomize Order 开、Seed 269、
   Min Ease 100；动画器属性 Scale 147/147/98.66、Blur 107/107、Opacity 0。
   （ffx 里第二个动画器属性全是中性值，不带效果，故不导入。）
2. `crates/engine/src/cmd/import_ext.rs`：`apply_ffx` 在没有效果可套时回退到文字动画器，
   把预设套到当前选中的文本图层上；没有文本图层时给出中文错误。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FFX_TEXT_V1"

PRESET = {
    "id": "evaporate",
    "name": "蒸发",
    "description": "字符一边放大、模糊一边淡出，像蒸发一样消失（来自奇峰自由文字出场.ffx 的 Evaporate Animator）。",
    "animators": [
        {
            "name": "蒸发",
            "properties": {"opacity": 0, "scale": [147.0, 147.0, 100.0], "blur": [107.0, 107.0]},
            "selectors": [
                {
                    "kind": "range",
                    "set": {
                        "advanced/shape": 2,
                        "advanced/smoothness": 100.0,
                        "advanced/amount": 100.0,
                        "advanced/easeLow": 100.0,
                        "advanced/randomize": True,
                        "advanced/randomSeed": 269.0,
                    },
                    "keys": {"offset": [[0.0, -100.0], [1.2, 100.0]]},
                    "ease": True,
                }
            ],
        }
    ],
}

JSON_ANCHOR = '"presets": [\n'

FUNC = r'''

/// EFFECTCRAFT_OURS_FFX_TEXT_V1 — `.ffx` 里的文字动画器（目前支持 Evaporate / 蒸发）。
fn ffx_text_presets(text: &str) -> Vec<&'static str> {
    const KNOWN: [(&str, &str); 2] = [("Evaporate Animator", "evaporate"), ("Evaporate", "evaporate")];
    let mut found: Vec<&'static str> = Vec::new();
    for (name, preset) in KNOWN {
        if text.contains(name) && !found.contains(&preset) {
            found.push(preset);
        }
    }
    found
}
'''

OLD = '''    let ids = ffx_effect_ids(&text);
    if ids.is_empty() {
        return Err(EngineError::Other(format!("{path}: 这个预设里没有本机能识别的效果")));
    }
'''

NEW = '''    let ids = ffx_effect_ids(&text);
    if ids.is_empty() {
        // EFFECTCRAFT_OURS_FFX_TEXT_V1 — 没有效果可套时，看看是不是文字动画器（如「蒸发」）
        let presets = ffx_text_presets(&text);
        if presets.is_empty() {
            return Err(EngineError::Other(format!("{path}: 这个预设里没有本机能识别的效果")));
        }
        let mut applied = 0usize;
        let mut last: Option<String> = None;
        for preset in presets {
            match s.execute("layer.applyTextPreset", serde_json::json!({"preset": preset})) {
                Ok(_) => applied += 1,
                Err(e) => last = Some(e.to_string()),
            }
        }
        if applied == 0 {
            let why = last.unwrap_or_else(|| "先选中一个文本图层".to_string());
            return Err(EngineError::Other(format!("{path}: 文字动画器无法应用（{why}）")));
        }
        return Ok(applied);
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    presets = root / "crates/engine/presets/text_animators.json"
    src = presets.read_text(encoding="utf-8")
    if '"id": "evaporate"' not in src:
        if src.count(JSON_ANCHOR) != 1:
            raise SystemExit(f"presets anchor: {src.count(JSON_ANCHOR)}")
        compact = "    " + json.dumps(PRESET, ensure_ascii=False) + ",\n"
        src = src.replace(JSON_ANCHOR, JSON_ANCHOR + compact, 1)
        json.loads(src)  # fail loudly if the preset made the file invalid JSON
        presets.write_text(src, encoding="utf-8")
        print("text animator preset 'evaporate' added")

    module = root / "crates/engine/src/cmd/import_ext.rs"
    src = module.read_text(encoding="utf-8")
    if MARKER in src:
        print("ffx text animator import already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"apply_ffx anchor: {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    module.write_text(src.rstrip() + "\n" + FUNC, encoding="utf-8")
    print("apply_ffx falls back to text animator presets")


if __name__ == "__main__":
    main()
