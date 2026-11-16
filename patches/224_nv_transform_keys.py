#!/usr/bin/env python3
"""NodeVideo 变换关键帧（位置/缩放/旋转/不透明度）导入。

关键帧编码取自样本：{_x: 时间(秒), _y: 数值}；矢量优先读 vx/vy，其次 x/y。
数据不完整的键会跳过并在提示里报数量，不猜。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_TRANSFORM_KEYS_V1"

HERE = Path(__file__).resolve().parent


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("NV transform keys already imported")
        return
    helpers = (HERE / "nv_keys_helpers.rs").read_text(encoding="utf-8")
    apply = (HERE / "nv_keys_apply.rs").read_text(encoding="utf-8")

    anchor = "fn is_fill_node(node: &Value) -> bool {\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"helper anchor: {src.count(anchor)}")
    src = src.replace(anchor, helpers + "\n" + anchor, 1)

    keep_old = "    let mut nodes: Vec<&Value> = Vec::new();\n    collect_media_nodes(&doc, &mut nodes);\n"
    keep_new = keep_old + "    let mut all_nodes: Vec<&Value> = Vec::new();\n    collect_all_nodes(&doc, &mut all_nodes);\n"
    if src.count(keep_old) != 1:
        raise SystemExit(f"collect anchor: {src.count(keep_old)}")
    src = src.replace(keep_old, keep_new, 1)

    note_old = '    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");\n'
    if src.count(note_old) != 1:
        raise SystemExit(f"note anchor: {src.count(note_old)}")
    tail = apply + '    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");\n'
    tail += '    if keyed > 0 {\n        note.push_str(&format!("、{keyed} 个变换关键帧"));\n    }\n'
    tail += '    if skipped > 0 {\n        note.push_str(&format!("（{skipped} 个键因数据不完整跳过）"));\n    }\n'
    src = src.replace(note_old, tail, 1)
    path.write_text(src, encoding="utf-8")
    print("NV transform keyframes imported")


if __name__ == "__main__":
    main()
