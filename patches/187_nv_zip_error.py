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
            return match import_nodevideo(s, path) {
                Some(note) => {
                    s.toast(note);
                    Ok(Vec::new())
                }
                None => Err(EngineError::Other(format!(
                    "{path}：没有找到可用的 NodeVideo 工程（zip 里需要有 .nv，且素材要在本机或 zip 的 Medias/ 里）"
                ))),
            };
        }
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
    src = src.replace(HOOK_OLD, HOOK_NEW, 1)
    if src.count(LOG_OLD) == 1:
        src = src.replace(LOG_OLD, LOG_NEW, 1)
    ext.write_text(src, encoding="utf-8")
    print("a failed NodeVideo zip now explains itself")


if __name__ == "__main__":
    main()
