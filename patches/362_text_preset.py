#!/usr/bin/env python3
"""文字预设：**照常套用**，不再报"不支持"。

314 已经在 `apply_ffx` 里做了兜底（`.ffx` 里没有效果时按 `Evaporate Animator` 套用内置「蒸发」预设），
但需要当前有一个**文字图层**。所以这里只做一件事：识别出"纯文字预设"时，如果套用没成功，
就先建一个文字图层再重试一次；成功则不把 `ADBE Text *` 那堆属性算成"缺失"。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TEXT_PRESET_V1"

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
BODY_NEW = '''    // EFFECTCRAFT_OURS_TEXT_PRESET_V1 — 文字预设：没有文字图层就先建一个，然后让 314 的
    // 「蒸发」动画器兜底真正套上去；成功时不再把 ADBE Text 那堆属性算成缺失。
    if let Ok(bytes) = std::fs::read(&path) {
        if super::import_ext::is_text_only_preset(&bytes) {
            if let Ok((applied, _)) = super::import_ext::apply_preset_report(s, &path) {
                if applied > 0 {
                    return Ok(json!({
                        "applied": applied,
                        "effects": 0,
                        "missing": [],
                        "skipped": [],
                        "failed": [],
                        "warnings": [format!("已套用 {} 个文字动画器", applied)],
                    }));
                }
            }
            if s.execute("layer.new", json!({ "text": "文字", "edit": false })).is_ok() {
                if let Ok((applied, _)) = super::import_ext::apply_preset_report(s, &path) {
                    if applied > 0 {
                        return Ok(json!({
                            "applied": applied,
                            "effects": 0,
                            "missing": [],
                            "skipped": [],
                            "failed": [],
                            "warnings": ["已新建文字图层并套用「蒸发」文字动画器；换成你自己的文字即可"],
                        }));
                    }
                }
            }
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
        print("text presets create a text layer and apply the animator")


if __name__ == "__main__":
    main()
