#!/usr/bin/env python3
"""The NodeVideo skeleton is remembered where the exporter can find it.

The importer unpacks a project into app-private storage (the picker copies files there), which the
exporter's folder scan never sees. So the import records the `.nv` it produced in
`DCIM/EffectCraft/.nv-skeleton.txt`, and the exporter reads that first. The refusal message is also a
plain sentence now ("invalid parameters for …" came from passing it through `bad`).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_SKELETON_V1"

RECORD_OLD = '''            if is_project && project_json.is_none() {
                project_json = std::fs::read_to_string(&out_path).ok();
            }
'''
RECORD_NEW = '''            if is_project {
                if project_json.is_none() {
                    project_json = std::fs::read_to_string(&out_path).ok();
                }
                // EFFECTCRAFT_OURS_NV_SKELETON_V1 — 记下骨架位置，导出时直接用
                let _ = std::fs::create_dir_all("/storage/emulated/0/DCIM/EffectCraft");
                let _ = std::fs::write("/storage/emulated/0/DCIM/EffectCraft/.nv-skeleton.txt", &out_path);
            }
'''

FIND_OLD = '''    let mut candidates: Vec<String> = Vec::new();
'''
FIND_NEW = '''    let mut candidates: Vec<String> = Vec::new();
    // 导入时记下的骨架优先
    if let Ok(saved) = std::fs::read_to_string("/storage/emulated/0/DCIM/EffectCraft/.nv-skeleton.txt") {
        let saved = saved.trim().to_string();
        if !saved.is_empty() {
            candidates.push(saved);
        }
    }
'''

ERR_OLD = '''        return Err(bad(
            "ours.exportNodeVideo",
            "需要一个 NodeVideo 工程做骨架：先在 NodeVideo 里导出过一次工程（.zip），再把它导入 EffectCraft 一次",
        ));'''
ERR_NEW = '''        return Err(crate::EngineError::Other(
            "需要一个 NodeVideo 工程做骨架：先在 NodeVideo 里导出过一次工程（.zip），再把它导入 EffectCraft 一次".into(),
        ));'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    ext = root / "crates/engine/src/cmd/import_ext.rs"
    src = ext.read_text(encoding="utf-8")
    if "EFFECTCRAFT_OURS_NV_SKELETON_V1" not in src:
        if src.count(RECORD_OLD) != 1:
            raise SystemExit(f"record anchor: {src.count(RECORD_OLD)}")
        ext.write_text(src.replace(RECORD_OLD, RECORD_NEW, 1), encoding="utf-8")
        print("import records the skeleton")
    exp = root / "crates/engine/src/cmd/ours_export.rs"
    src = exp.read_text(encoding="utf-8")
    changed = False
    if FIND_OLD in src:
        src = src.replace(FIND_OLD, FIND_NEW, 1)
        changed = True
    if ERR_OLD in src:
        src = src.replace(ERR_OLD, ERR_NEW, 1)
        changed = True
    if changed:
        exp.write_text(src, encoding="utf-8")
        print("exporter reads the recorded skeleton")
    print("done" if not changed else "")


if __name__ == "__main__":
    main()
