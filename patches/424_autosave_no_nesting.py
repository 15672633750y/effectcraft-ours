#!/usr/bin/env python3
"""自动保存目录不再套娃：`EffectCraft Auto-Save/EffectCraft Auto-Save/EffectCraft Auto-Save/...`

崩溃恢复打开的是自动保存文件，`session.path` 于是指向 `.../EffectCraft Auto-Save/x.ecproj`；
下一次自动保存按 `project.parent().join("EffectCraft Auto-Save")` 又套一层，文件名也滚成
`Untitled Project auto-save 3 auto-save 3 auto-save 1`（cloud.log 里能直接看到）。

修法：`folder()` 先把路径尾部的 `EffectCraft Auto-Save` 段全部剥掉，再拼一次。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUTOSAVE_NO_NEST_V1"

OLD = '''    match project.and_then(|p| Path::new(p).parent()) {
        Some(dir) => Some(dir.join(AUTOSAVE_FOLDER)),
        None => fallback.map(|f| f.join(AUTOSAVE_FOLDER)),
    }'''

NEW = '''    match project.and_then(|p| Path::new(p).parent()) {
        // EFFECTCRAFT_OURS_AUTOSAVE_NO_NEST_V1 — 已经在自动保存目录里就向上找到真正的工程目录，
        // 否则每崩溃恢复一次就多套一层 `EffectCraft Auto-Save`。
        Some(dir) => {
            let mut base = dir.to_path_buf();
            while base
                .file_name()
                .map(|n| n == AUTOSAVE_FOLDER)
                .unwrap_or(false)
            {
                match base.parent() {
                    Some(parent) => base = parent.to_path_buf(),
                    None => break,
                }
            }
            Some(base.join(AUTOSAVE_FOLDER))
        }
        None => fallback.map(|f| f.join(AUTOSAVE_FOLDER)),
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/settings/autosave.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("autosave nesting already fixed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("autosave folder no longer nests")


if __name__ == "__main__":
    main()
