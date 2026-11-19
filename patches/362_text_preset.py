#!/usr/bin/env python3
"""文字预设给一句准确的话，而不是"缺 120 项"。

`.ffx` 文字预设里没有任何 effect，全是 `ADBE Text *`（文字文档 + 文字动画器 + 范围选择器）。
引擎支持文字图层，但不支持文字动画器，所以这类预设**注定无法套用**，不是匹配算法的问题。
这里把结果改写成一句能解释清楚的话（并且不误建一个写着"源文本"的图层）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TEXT_PRESET_V1"

# 在 import_ext.rs 里加一个判断：这个预设是不是纯文字预设
HELPER_ANCHOR = "pub(crate) fn apply_preset_report("
HELPER = '''/// 这个预设是不是"文字预设"：只含 `ADBE Text *`，没有任何可套用的效果。
pub(crate) fn is_text_only_preset(bytes: &[u8]) -> bool {
    let mut text = 0usize;
    let mut other = 0usize;
    let mut i = 0usize;
    while i + 9 < bytes.len() {
        if &bytes[i..i + 4] == b"tdmn" {
            let len = u32::from_be_bytes([bytes[i + 4], bytes[i + 5], bytes[i + 6], bytes[i + 7]]) as usize;
            let start = i + 8;
            if len > 0 && len < 512 && start + len <= bytes.len() {
                if let Ok(name) = std::str::from_utf8(&bytes[start..start + len]) {
                    let name = name.trim_matches('\\0');
                    if name.starts_with("ADBE Text") {
                        text += 1;
                    } else if !name.is_empty() {
                        other += 1;
                    }
                }
            }
            i = start + len;
            continue;
        }
        i += 1;
    }
    text > 0 && other == 0
}

'''

BODY_OLD = '''    match super::import_ext::apply_preset_report(s, &path) {
        Ok((applied, missing)) => Ok(json!({'''
BODY_NEW = '''    // EFFECTCRAFT_OURS_TEXT_PRESET_V1 — 文字预设：没有可套的效果，直说原因。
    if let Ok(bytes) = std::fs::read(&path) {
        if super::import_ext::is_text_only_preset(&bytes) {
            return Ok(json!({
                "applied": 0,
                "effects": 0,
                "missing": [],
                "skipped": [],
                "failed": [],
                "warnings": [
                    "该预设是 AE 文字动画器，本软件暂不支持；文字图层和动画器可以通过导入 .aep 工程还原"
                ],
            }));
        }
    }
    match super::import_ext::apply_preset_report(s, &path) {
        Ok((applied, missing)) => Ok(json!({'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    ext = root / "crates/engine/src/cmd/import_ext.rs"
    src = ext.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(HELPER_ANCHOR) != 1:
            raise SystemExit(f"helper anchor: {src.count(HELPER_ANCHOR)}")
        src = src.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)
        ext.write_text(src, encoding="utf-8")
        print("is_text_only_preset added")

    cmd = root / "crates/engine/src/cmd/ours_export.rs"
    src = cmd.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(BODY_OLD) != 1:
            raise SystemExit(f"apply_preset anchor: {src.count(BODY_OLD)}")
        src = src.replace(BODY_OLD, BODY_NEW, 1)
        cmd.write_text(src, encoding="utf-8")
        print("text presets report the real reason")


if __name__ == "__main__":
    main()
