#!/usr/bin/env python3
"""A NodeVideo zip that cannot be rebuilt says so instead of being parsed as JSON.

When `import_nodevideo` gives up on a `.zip`/`.nv`, the old code fell through to the media-extraction
path, which tried to read the zip as JSON and surfaced "expected value at line 1 column 1". Now the
zip ends its own branch with an explanation, and the attempt logs what it saw (entry names, node
count, whether the media resolved) so the next report can be diagnosed.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_ZIP_ERROR_V1"

HOOK_OLD = '''    // EFFECTCRAFT_OURS_FIX3_V1 — NodeVideo 的 zip / .nv 先处理：zip 不是 JSON，不能在下面被解析
    if let Some(note) = import_nodevideo(s, path) {
        s.toast(note);
        return Ok(Vec::new());
    }
'''
HOOK_NEW = '''    // EFFECTCRAFT_OURS_FIX3_V1 — NodeVideo 的 zip / .nv 先处理：zip 不是 JSON，不能在下面被解析
    {
        let lower = path.to_ascii_lowercase();
        if lower.ends_with(".zip") || lower.ends_with(".nv") {
            // EFFECTCRAFT_OURS_NV_ZIP_ERROR_V1 — 走到底：成功就用时间线，失败给明确原因，
            // 不再退回 JSON 解析（那会报 "expected value at line 1 column 1"）
            let diag = nv_diag(path);
            return match import_nodevideo(s, path) {
                Some(note) => {
                    s.toast(note);
                    Ok(Vec::new())
                }
                None => Err(EngineError::Other(format!(
                    "{path}：NV 工程没导入成功——可能原因：①工程里只有纯色/调整层，没有媒体图层 ②素材不在本机也不在 zip 的 Medias/ 里；诊断：{diag}"
                ))),
            };
        }
    }
'''


DIAG = r'''

/// 失败时给一句诊断：zip 里有多少条目、有没有 .nv。
fn nv_diag(path: &str) -> String {
    let lower = path.to_ascii_lowercase();
    if !lower.ends_with(".zip") {
        return format!("{}：不是 zip", if lower.ends_with(".nv") { "只有 .nv" } else { "未知" });
    }
    let Ok(file) = std::fs::File::open(path) else { return "打不开文件".into() };
    let Ok(mut zip) = zip::ZipArchive::new(file) else { return "不是有效的 zip".into() };
    let mut nv = 0usize;
    let mut media = 0usize;
    let mut first = Vec::new();
    for i in 0..zip.len() {
        let Ok(e) = zip.by_index(i) else { continue };
        let n = e.name().to_ascii_lowercase();
        if n.ends_with(".nv") { nv += 1; }
        if n.starts_with("medias/") || n.contains("/medias/") { media += 1; }
        if first.len() < 3 { first.push(e.name().to_string()); }
    }
    format!("{} 个条目，{} 个 .nv，{} 个媒体，例如 {:?}", zip.len(), nv, media, first)
}
'''

LOG_OLD = '''    if nodes.is_empty() {
        return None;
    }
'''
LOG_NEW = '''    if nodes.is_empty() {
        log::warn!("nodevideo: {path} has no media nodes");
        return None;
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    ext = root / "crates/engine/src/cmd/import_ext.rs"
    src = ext.read_text(encoding="utf-8")
    if MARKER in src:
        print("zip branch already explicit")
        return
    if src.count(HOOK_OLD) != 1:
        raise SystemExit(f"hook anchor: {src.count(HOOK_OLD)}")
    src = src.replace(HOOK_OLD, HOOK_NEW + DIAG, 1)
    if src.count(LOG_OLD) == 1:
        src = src.replace(LOG_OLD, LOG_NEW, 1)
    ext.write_text(src, encoding="utf-8")
    print("a failed NodeVideo zip now explains itself")


if __name__ == "__main__":
    main()
