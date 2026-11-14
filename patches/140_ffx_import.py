#!/usr/bin/env python3
"""`.ffx` effect presets: apply the effects a preset names to the selected layer.

After Effects premade effects are RIFX chunks; each effect node carries its id as a NUL-padded
`tdmn` string (`S_Vignette`, `S_Glow`, `S_Rays` …). Import reads those ids and applies our matching
effects (same ids, or the Sapphire-compatible ones we added) to the selected layer, in the preset's
order — the effects land with their own live parameters rather than as an empty group, and nothing
pretends to have restored a value it could not read.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FFX_IMPORT_V1"

FUNC = r'''

/// The effects an `.ffx` preset names, in the order they first appear, as our effect ids.
fn ffx_effect_ids(text: &str) -> Vec<&'static str> {
    const KNOWN: [(&str, &str); 7] = [
        ("S_VintageColor3Strip", "org.effectcraft.compat.sapphire.vintagecolor3strip"),
        ("S_VintageColor2Strip", "org.effectcraft.compat.sapphire.vintagecolor2strip"),
        ("S_Vignette", "org.effectcraft.compat.sapphire.vignette"),
        ("S_Glow", "S_Glow"),
        ("S_Rays", "S_Rays"),
        ("S_TextureFlux", "S_TextureFlux"),
        ("S_DropShadow", "S_DropShadow"),
    ];
    let mut found: Vec<(&str, usize)> = Vec::new();
    for (name, id) in KNOWN {
        if let Some(at) = text.find(name) {
            found.push((id, at));
        }
    }
    found.sort_by_key(|(_, at)| *at);
    found.into_iter().map(|(id, _)| id).collect()
}

/// Apply a preset's effects to the selected layer. Returns how many were added.
pub(crate) fn apply_ffx(s: &mut Session, path: &str) -> Result<usize> {
    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes);
    let ids = ffx_effect_ids(&text);
    if ids.is_empty() {
        return Err(EngineError::Other(format!("{path}: 这个预设里没有本机能识别的效果")));
    }
    let mut applied = 0usize;
    let mut unknown = Vec::new();
    for id in ids {
        match s.execute("effect.apply", serde_json::json!({"effect": id})) {
            Ok(_) => applied += 1,
            Err(_) => unknown.push(id),
        }
    }
    if applied == 0 {
        return Err(EngineError::Other(format!("{path}: 效果无法应用（先选中一个图层）")));
    }
    Ok(applied)
}
'''

FILE_OLD = '''    // EFFECTCRAFT_OURS_IMPORT_EXT_V1 — 剪映/CapCut 草稿与 Nuke 脚本：导入它们引用的媒体
    let (recipes, media_paths): (Vec<String>, Vec<String>) = paths.into_iter().partition(|x| super::import_ext::is_recipe_path(x));
    paths = media_paths;
'''
FILE_NEW = '''    // EFFECTCRAFT_OURS_IMPORT_EXT_V1 — 剪映/CapCut 草稿与 Nuke 脚本：导入它们引用的媒体
    // EFFECTCRAFT_OURS_FFX_IMPORT_V1 — .ffx 效果预设：把效果套到选中图层
    let (ffx, rest): (Vec<String>, Vec<String>) = paths.into_iter().partition(|x| x.to_ascii_lowercase().ends_with(".ffx"));
    let (recipes, media_paths): (Vec<String>, Vec<String>) = rest.into_iter().partition(|x| super::import_ext::is_recipe_path(x));
    paths = media_paths;
    for preset in ffx {
        match super::import_ext::apply_ffx(s, &preset) {
            Ok(n) => inserted_effects.push((preset, n)),
            Err(e) => errors.push(e.to_string()),
        }
    }
'''

VAR_OLD = '''    let mut comps = vec![];
    let mut items = vec![];
    let mut errors = vec![];
'''
VAR_NEW = '''    let mut comps = vec![];
    let mut items = vec![];
    let mut errors = vec![];
    let mut inserted_effects: Vec<(String, usize)> = vec![];
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    module = root / "crates/engine/src/cmd/import_ext.rs"
    src = module.read_text(encoding="utf-8")
    if MARKER not in src:
        module.write_text(src.rstrip() + "\n" + FUNC, encoding="utf-8")
        print("apply_ffx added to import_ext")

    file_cmd = root / "crates/engine/src/cmd/file.rs"
    src = file_cmd.read_text(encoding="utf-8")
    if "EFFECTCRAFT_OURS_FFX_IMPORT_V1" not in src:
        for old, new in ((VAR_OLD, VAR_NEW), (FILE_OLD, FILE_NEW)):
            if src.count(old) != 1:
                raise SystemExit(f"file anchor {old[:40]!r}: {src.count(old)}")
            src = src.replace(old, new, 1)
        file_cmd.write_text(src, encoding="utf-8")
        print("file.import applies .ffx presets")


if __name__ == "__main__":
    main()
