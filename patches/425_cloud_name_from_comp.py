#!/usr/bin/env python3
"""云端工程名：未命名/自动保存工程用**当前合成名**，而不是恒为「我的工程」。

cloud.log 里能直接看到问题：
`UPLOAD .../EffectCraft Auto-Save/Untitled Project auto-save 3.ecproj 18099 bytes as 我的工程`
——用户根本没保存过工程，路径是自动保存文件，剥完仍是 "Untitled Project"，于是回退默认名。

现在的取名顺序：
1. 文件名剥掉 " auto-save N" 后，如果是有意义的名字 → 用它
2. 否则用**当前合成名**（如「合成 1」）——至少和用户看到的一致
3. 再不行才「我的工程」
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_NAME_COMP_V1"

NAME_OLD = '''fn cloud_project_name(path: &str) -> String {'''
NAME_NEW = '''fn cloud_project_name(app: &EffectcraftApp, path: &str) -> String {'''

TAIL_OLD = '''    let cleaned = out.trim().to_string();
    let lower = cleaned.to_ascii_lowercase();
    if cleaned.is_empty() || lower.starts_with("untitled") || cleaned == "无标题" {
        return "我的工程".to_string();
    }
    cleaned
}'''

TAIL_NEW = '''    let cleaned = out.trim().to_string();
    let lower = cleaned.to_ascii_lowercase();
    if cleaned.is_empty() || lower.starts_with("untitled") || cleaned == "无标题" {
        // EFFECTCRAFT_OURS_CLOUD_NAME_COMP_V1 — 用当前合成名，别固定成「我的工程」
        if let Some(id) = app.session.active_comp_id() {
            if let Some(item) = app.session.project.item(id) {
                let n = item.name.trim();
                if !n.is_empty() {
                    return n.to_string();
                }
            }
        }
        return "我的工程".to_string();
    }
    cleaned
}'''

CALL1_OLD = "    let name = cloud_project_name(&path);"
CALL1_NEW = "    let name = cloud_project_name(app, &path);"

CALL2_OLD = "                let name = cloud_project_name(&target);"
CALL2_NEW = "                let name = cloud_project_name(app, &target);"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/account_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("cloud name from comp already present")
        return
    for name, old, new in (
        ("sig", NAME_OLD, NAME_NEW),
        ("tail", TAIL_OLD, TAIL_NEW),
        ("call1", CALL1_OLD, CALL1_NEW),
        ("call2", CALL2_OLD, CALL2_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("cloud name falls back to the active composition name")


if __name__ == "__main__":
    main()
