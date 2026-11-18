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

/// RIFX（AE 的二进制预设）里的效果 matchName：ASCII 与 UTF-16BE 两种编码都扫一遍。
/// 不解析 chunk 树：不同 `.ffx` 版本的 form type 不一定是 `Egg!`，`read::parse` 会直接拒掉，
/// 而 matchName 在字节流里就是以这两种编码出现的。
fn rifx_effect_names(data: &[u8]) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    fn push(out: &mut Vec<String>, text: &str) {
        let name = text.trim().to_string();
        if name.len() > 3 && !out.contains(&name) {
            out.push(name);
        }
    }
    let keep = |b: u8| b.is_ascii_alphanumeric() || b == b' ' || b == b'-' || b == b'.';
    // ASCII
    let mut i = 0usize;
    while i + 5 <= data.len() {
        if &data[i..i + 5] == b"ADBE " {
            let mut j = i;
            while j < data.len() && keep(data[j]) {
                j += 1;
            }
            push(&mut out, &String::from_utf8_lossy(&data[i..j]));
            i = j;
        } else {
            i += 1;
        }
    }
    // UTF-16BE：每两字节一个 ASCII 字符
    let mut i = 0usize;
    while i + 10 <= data.len() {
        let starts = data[i] == 0
            && data[i + 1] == b'A'
            && data[i + 2] == 0
            && data[i + 3] == b'D'
            && data[i + 4] == 0
            && data[i + 5] == b'B'
            && data[i + 6] == 0
            && data[i + 7] == b'E'
            && data[i + 8] == 0;
        if starts {
            let mut j = i;
            let mut text = String::new();
            while j + 1 < data.len() && data[j] == 0 && keep(data[j + 1]) {
                text.push(data[j + 1] as char);
                j += 2;
            }
            push(&mut out, &text);
            i = j;
        } else {
            i += 1;
        }
    }
    out
}

fn apply_rifx(s: &mut Session, path: &str, bytes: &[u8]) -> Result<(usize, Vec<String>)> {
    let names = rifx_effect_names(bytes);
    if names.is_empty() {
        return Err(EngineError::Other(format!("{path}: RIFX 预设里没找到效果名")));
    }
    let mut applied = 0usize;
    let mut missing: Vec<String> = Vec::new();
    for name in names {
        // aep 里那份 matchName → EffectCraft id 的映射表（by_match_name）
        let id = effectcraft_aep::container::effect_map::by_match_name(&name)
            .map(|m| m.effect.to_string())
            .unwrap_or_else(|| name.clone());
        match s.execute("effect.apply", serde_json::json!({"effect": id})) {
            Ok(_) => applied += 1,
            Err(_) => missing.push(name),
        }
    }
    Ok((applied, missing))
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
    Ok(applied)
}

/// 面板用的报告版：先按文件头分派，再给出「套上了几个 / 缺哪些」。
/// 单独一个函数是为了不动 `apply_ffx` 的签名（JSON 预设与文字动画器都依赖它返回 usize）。
pub(crate) fn apply_preset_report(s: &mut Session, path: &str) -> Result<(usize, Vec<String>)> {
    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    // ① RIFX 二进制（AE 的 .ffx 多数是它）
    if bytes.starts_with(b"RIFX") {
        return apply_rifx(s, path, &bytes);
    }
    let text = String::from_utf8_lossy(&bytes);
    let head = text.trim_start();
    // ② 既不是 RIFX 也不是 XML/JSON：明确报「无法识别」，绝不静默成功。
    if !head.starts_with('<') && !head.starts_with('{') {
        return Err(EngineError::Other(format!("{path}: 无法识别的预设格式")));
    }
    // ③ 交给现有 apply_ffx（XML / JSON / .gp / 文字动画器都在里面）。
    //    「没有本机能识别的效果」不是故障：那就是 applied = 0，缺哪些由下面算出来。
    let applied = match apply_ffx(s, path) {
        Ok(n) => n,
        Err(e) if e.to_string().contains("没有本机能识别的效果") => 0,
        Err(e) => return Err(e),
    };
    // ④ 预设里出现、但我们不认识的名字，作为「缺失」
    let known: Vec<String> = FFX_KNOWN.iter().map(|(name, _)| name.to_ascii_lowercase()).collect();
    let mut missing: Vec<String> = Vec::new();
    for name in ffx_effect_names(&text) {
        let lower = name.to_ascii_lowercase();
        if !known.iter().any(|k| lower.contains(k) || k.eq_ignore_ascii_case(&name)) && !missing.contains(&name) {
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
