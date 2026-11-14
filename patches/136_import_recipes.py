#!/usr/bin/env python3
"""Dropping a 剪映/CapCut draft or a Nuke script into Import brings in the media it references.

Neither format is a project EffectCraft can rebuild, but both are plain text that names the files
its timeline uses: CapCut's `draft_content.json` lists them under `materials`, and a Nuke `.nk`
script under each `Read` node's `file`. Import now recognises both and imports those media files
instead of failing on the JSON/script itself (paths that only exist on another computer are looked
up beside the draft, then skipped with a message).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_IMPORT_EXT_V1"

MODULE = r'''//! 剪映/CapCut 的 `draft_content.json` 和 Nuke 的 `.nk`：把里面引用的媒体拆出来导入。

use serde_json::Value;

use crate::{EngineError, Result, Session};

/// Whether `path` is a recipe EffectCraft expands into media instead of importing as footage.
pub(crate) fn is_recipe_path(path: &str) -> bool {
    let lower = path.to_ascii_lowercase();
    if lower.ends_with(".nk") {
        return true;
    }
    if lower.ends_with("draft_content.json") || lower.ends_with(".json") {
        return true;
    }
    false
}

fn dir_of(path: &str) -> String {
    match path.rfind('/') {
        Some(i) => path[..i].to_string(),
        None => String::new(),
    }
}

fn file_name(path: &str) -> &str {
    match path.rfind(|c: char| c == '/' || c == '\\') {
        Some(i) => &path[i + 1..],
        None => path,
    }
}

/// A media path as the draft stores it: absolute when it resolves here, else the file of that name
/// beside the draft (a project folder moved from a computer keeps the media next to the draft).
fn resolve(s: &Session, raw: &str, dir: &str) -> Option<String> {
    let raw = raw.trim();
    if raw.is_empty() {
        return None;
    }
    if s.services.exists(raw) {
        return Some(raw.to_string());
    }
    let name = file_name(raw);
    if name.is_empty() {
        return None;
    }
    let beside = if dir.is_empty() { name.to_string() } else { format!("{dir}/{name}") };
    s.services.exists(&beside).then_some(beside)
}

/// Media a CapCut/剪映 draft references: `materials.videos[].path` and `materials.audios[].path`,
/// plus images.
fn capcut_media(doc: &Value) -> Vec<String> {
    let mut out = Vec::new();
    let Some(mats) = doc.get("materials").and_then(Value::as_object) else { return out };
    for key in ["videos", "audios", "images"] {
        if let Some(list) = mats.get(key).and_then(Value::as_array) {
            for m in list {
                if let Some(p) = m.get("path").and_then(Value::as_str) {
                    out.push(p.to_string());
                }
            }
        }
    }
    out
}

/// Paths a Nuke script reads: every `file "<path>"` (Read nodes, and Read nodes inside groups).
fn nuke_media(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("file ") {
            let rest = rest.trim();
            let path = rest.trim_matches('"');
            if !path.is_empty() && path.contains('.') {
                out.push(path.to_string());
            }
        }
    }
    out
}

/// The media files a recipe names, resolved beside it. Errors only when nothing usable is left.
pub(crate) fn expand(s: &mut Session, path: &str) -> Result<Vec<String>> {
    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes).to_string();
    let dir = dir_of(path);
    let named = if path.to_ascii_lowercase().ends_with(".nk") {
        nuke_media(&text)
    } else {
        let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: {e}")))?;
        capcut_media(&doc)
    };
    let mut found = Vec::new();
    let mut missing = 0usize;
    for raw in named {
        match resolve(s, &raw, &dir) {
            Some(media) => {
                if !found.contains(&media) {
                    found.push(media)
                }
            }
            None => missing += 1,
        }
    }
    if found.is_empty() {
        return Err(EngineError::Other(format!("{path}: 里面引用的 {missing} 个媒体文件都不在这台机器上")));
    }
    Ok(found)
}
'''

FILE_ANCHOR = "    if let Some(retain) = retain {\n"
FILE_INSERT = '''    // EFFECTCRAFT_OURS_IMPORT_EXT_V1 — 剪映/CapCut 草稿与 Nuke 脚本：导入它们引用的媒体
    let (recipes, media_paths): (Vec<String>, Vec<String>) = paths.into_iter().partition(|x| super::import_ext::is_recipe_path(x));
    paths = media_paths;
    for recipe in recipes {
        match super::import_ext::expand(s, &recipe) {
            Ok(found) => paths.extend(found),
            Err(e) => errors.push(e.to_string()),
        }
    }
'''

MOD_ANCHOR = "mod import_project;\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    module = root / "crates/engine/src/cmd/import_ext.rs"
    if not module.exists():
        module.write_text(MODULE, encoding="utf-8")
        print("import_ext.rs written")

    cmd = root / "crates/engine/src/cmd.rs"
    src = cmd.read_text(encoding="utf-8")
    if "mod import_ext;\n" not in src:
        if src.count(MOD_ANCHOR) != 1:
            raise SystemExit(f"mod anchor: {src.count(MOD_ANCHOR)}")
        cmd.write_text(src.replace(MOD_ANCHOR, MOD_ANCHOR + "mod import_ext;\n", 1), encoding="utf-8")
        print("import_ext registered")

    file_cmd = root / "crates/engine/src/cmd/file.rs"
    src = file_cmd.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FILE_ANCHOR) != 1:
            raise SystemExit(f"file anchor: {src.count(FILE_ANCHOR)}")
        src = src.replace(FILE_ANCHOR, FILE_INSERT + FILE_ANCHOR, 1)
        file_cmd.write_text(src, encoding="utf-8")
        print("file.import expands drafts and Nuke scripts")


if __name__ == "__main__":
    main()
