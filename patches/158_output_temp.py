#!/usr/bin/env python3
"""Renders must not land in the import staging folder.

The queue row showed the output as

    /storage/emulated/0/Android/data/<pkg>/files/media/合成 1.mp4

`media/` is where the shell stages the working copies of imported documents, and the gallery watcher
skips it on purpose (otherwise every import would be copied into the gallery). So a render written
there is finished and then never published — exactly "render completes, no file".

The output folder is redirected to `Renders/` beside it. Everything else about the path stays.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_OUTPUT_DIR_V2"

OLD = '''        let base = base.or_else(|| std::env::current_dir().ok()).or_else(|| cfg!(target_arch = "wasm32").then(|| "/".into()))?;
        Some(base.join(path).to_string_lossy().to_string())
'''
NEW = '''        let base = base.or_else(|| std::env::current_dir().ok()).or_else(|| cfg!(target_arch = "wasm32").then(|| "/".into()))?;
        // EFFECTCRAFT_OURS_OUTPUT_DIR_V2 — 成片直接写进 DCIM/EffectCraft：用户和相册都看得见，
        // 不再依赖“私有目录 + 后台复制”。（私有目录在安卓 11+ 连文件管理器都进不去。）
        #[cfg(target_os = "android")]
        let base = std::path::PathBuf::from("/storage/emulated/0/DCIM/EffectCraft");
        Some(base.join(path).to_string_lossy().to_string())
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("output folder already redirected")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("renders go to Renders/ instead of media/")


if __name__ == "__main__":
    main()
