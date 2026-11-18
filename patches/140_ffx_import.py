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

/// 预设里能识别的效果名 → 我们的效果 id。
const FFX_KNOWN: [(&str, &str); 10] = [
    ("S_VintageColor3Strip", "S_VintageColor3Strip"),
    ("S_VintageColor2Strip", "org.effectcraft.compat.sapphire.vintagecolor2strip"),
    ("S_Vignette", "S_Vignette"),
    ("S_Glow", "S_Glow"),
    ("S_Rays", "S_Rays"),
    ("S_TextureFlux", "S_TextureFlux"),
    ("S_DropShadow", "S_DropShadow"),
    // AE 内置效果：预设里常见，映射到我们已有的实现
    ("ADBE HUE SATURATION", "ec.color.huesaturation"),
    ("ADBE Sharpen", "ec.blur.sharpen"),
    ("ADBE Unsharp Mask2", "ec.blur.unsharp"),];

/// The effects an `.ffx` preset names, in the order they first appear, as our effect ids.
fn ffx_effect_ids(text: &str) -> Vec<&'static str> {
    let mut found: Vec<(&str, usize)> = Vec::new();
    for (name, id) in FFX_KNOWN {
        // 预设里同一个效果可能出现多次（例如三条彩放两份）：按出现次数逐个应用
        let bytes = text.as_bytes();
        let mut from = 0usize;
        while let Some(rel) = text[from..].find(name) {
            let at = from + rel;
            let after = at + name.len();
            let boundary = bytes.get(after).map(|b| !b.is_ascii_alphanumeric() && *b != b'-' && *b != b' ').unwrap_or(true);
            if boundary {
                found.push((id, at));
            }
            from = at + name.len();
        }
    }
    found.sort_by_key(|(_, at)| *at);
    found.into_iter().map(|(id, _)| id).collect()
}

/// 预设 XML 里出现过的效果名（`<Effect name="…" matchName="…">` 的两种属性都算）。
/// 用来告诉用户「缺哪些」——即使我们一个都认不出来，也能把名字报出来。
fn ffx_effect_names(text: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for raw in text.split('<').skip(1) {
        let head: String = raw.chars().take_while(|c| *c != '>').collect();
        let lower = head.to_ascii_lowercase();
        if !(lower.starts_with("effect") || lower.starts_with("filter")) {
            continue;
        }
        for key in ["name", "matchname", "match_name"] {
            let needle = format!("{key}=\"");
            let lower_head = head.to_ascii_lowercase();
            if let Some(at) = lower_head.find(&needle) {
                let value: String = head[at + needle.len()..].chars().take_while(|c| *c != '"').collect();
                let value = value.trim().to_string();
                if !value.is_empty() && !out.contains(&value) {
                    out.push(value);
                }
            }
        }
    }
    out
}

/// Apply a preset's effects to the selected layer. Returns how many were added.
/// The two-tuple is `(applied, missing)`: `missing` lists the preset's effect names this build does
/// not have, so the panel can say what is absent instead of reporting a silent success.
pub(crate) fn apply_ffx(s: &mut Session, path: &str) -> Result<(usize, Vec<String>)> {
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
    // 我们认识并能应用的名字
    let known: Vec<String> = FFX_KNOWN
        .iter()
        .flat_map(|(name, _)| {
            let mut both = vec![name.to_string()];
            both.push(name.to_ascii_lowercase());
            both
        })
        .collect();
    let mut missing: Vec<String> = Vec::new();
    for name in ffx_effect_names(&text) {
        let lower = name.to_ascii_lowercase();
        let matched = known.iter().any(|k| lower.contains(&k.to_ascii_lowercase()) || k.eq_ignore_ascii_case(&name));
        if !matched && !missing.contains(&name) {
            missing.push(name);
        }
    }
    Ok((applied, missing))
}
'''

FILE_OLD = '''    // EFFECTCRAFT_OURS_IMPORT_EXT_V1 — 剪映/CapCut 草稿与 Nuke 脚本：导入它们引用的媒体
    let (recipes, media_paths): (Vec<String>, Vec<String>) = paths.into_iter().partition(|x| super::import_ext::is_recipe_path(x));
    paths = media_paths;
'''
FILE_NEW = '''    // EFFECTCRAFT_OURS_IMPORT_EXT_V1 — 剪映/CapCut 草稿与 Nuke 脚本：导入它们引用的媒体
    // EFFECTCRAFT_OURS_FFX_IMPORT_V1 — .ffx 效果预设：把效果套到选中图层
    let (ffx, rest): (Vec<String>, Vec<String>) = paths.into_iter().partition(|x| {
        let l = x.to_ascii_lowercase();
        l.ends_with(".ffx") || l.ends_with(".gp")
    });
    let (recipes, media_paths): (Vec<String>, Vec<String>) = rest.into_iter().partition(|x| super::import_ext::is_recipe_path(x));
    paths = media_paths;
    for preset in ffx {
        match super::import_ext::apply_ffx(s, &preset) {
            Ok((n, _missing)) => inserted_effects.push((preset, n)),
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
