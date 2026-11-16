#!/usr/bin/env python3
"""`ours.shareFile {path}`：让手机上弹出系统分享面板（Java 侧的文件监视器接住）。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SHARE_COMMAND_V1"

SPEC_OLD = '''        always,
        export_project_zip
    )]
}'''
SPEC_NEW = '''        always,
        export_project_zip
    ), cmd!(
        "ours.shareFile",
        "分享文件",
        [],
        None,
        "{path: 要分享的文件}",
        always,
        share_file
    )]
}'''

FN = '''

/// EFFECTCRAFT_OURS_SHARE_COMMAND_V1 — 写一个请求文件，Java 侧的线程会弹出系统分享面板。
fn share_file(_s: &mut Session, p: &Value) -> Result<Value> {
    let path = str_p(p, "path").unwrap_or("").to_string();
    if path.is_empty() {
        return Err(bad("ours.shareFile", "no path"));
    }
    if !std::path::Path::new(&path).is_file() {
        return Err(bad("ours.shareFile", "the file does not exist"));
    }
    let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
    let _ = std::fs::create_dir_all(dir);
    let req = dir.join(".share-request");
    std::fs::write(&req, path.as_bytes()).map_err(|e| crate::EngineError::Other(format!("{e}")))?;
    Ok(json!({"ok": true, "path": path}))
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("share command already present")
        return
    if src.count(SPEC_OLD) != 1:
        raise SystemExit(f"spec anchor: {src.count(SPEC_OLD)}")
    src = src.replace(SPEC_OLD, SPEC_NEW, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("ours.shareFile added")


if __name__ == "__main__":
    main()
