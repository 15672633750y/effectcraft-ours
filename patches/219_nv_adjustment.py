#!/usr/bin/env python3
"""NodeVideo 调整图层（NodeAdjustment）导入成调整图层。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_ADJUSTMENT_V2"

COLLECT = r"""
fn is_adjustment_node(node: &Value) -> bool {
    node.get("$type").and_then(Value::as_str).is_some_and(|t| t.contains("NodeAdjustment"))
}

fn collect_adjustment_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {
    if is_adjustment_node(node) {
        out.push(node);
    }
    if let Some(children) = node.get("ChildList").and_then(Value::as_array) {
        for c in children {
            collect_adjustment_nodes(c, out);
        }
    }
}
"""

COLLECT_OLD = "fn is_fill_node(node: &Value) -> bool {\n"
CALL_OLD = "    let mut fills: Vec<&Value> = Vec::new();\n    collect_fill_nodes(&doc, &mut fills);\n"
CALL_NEW = CALL_OLD + "    let mut adjustments: Vec<&Value> = Vec::new();\n    collect_adjustment_nodes(&doc, &mut adjustments);\n"
GUARD_OLD = "    if placed == 0 && fills.is_empty() {\n        return None;\n    }\n"
GUARD_NEW = "    if placed == 0 && fills.is_empty() && adjustments.is_empty() {\n        return None;\n    }\n"
NOTE_OLD = '    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");\n'
NOTE_NEW = r"""    // 调整图层
    let mut adjust_made = 0usize;
    for node in adjustments {
        let tl = node.get("TimeLine");
        let pos = tl.and_then(|t| t.get("Pos")).and_then(Value::as_f64).unwrap_or(0.0);
        let start = tl.and_then(|t| t.get("Start")).and_then(Value::as_f64).unwrap_or(0.0);
        let end = tl.and_then(|t| t.get("End")).and_then(Value::as_f64).unwrap_or(0.0);
        let len = (end - start).max(0.0);
        if len <= 0.0 {
            continue;
        }
        let name = node.get("Name").and_then(Value::as_str).unwrap_or("调整图层").to_string();
        let Ok(res) = s.execute("layer.newAdjustment", json!({"name": name})) else { continue };
        let Some(lid) = res.get("layer").and_then(Value::as_u64) else { continue };
        let restore = s.time().seconds();
        let _ = s.execute("time.set", json!({"time": pos}));
        let _ = s.execute("layer.stretchInToTime", json!({"layers": [lid]}));
        let _ = s.execute("time.set", json!({"time": pos + len}));
        let _ = s.execute("layer.stretchOutToTime", json!({"layers": [lid]}));
        let _ = s.execute("time.set", json!({"time": restore}));
        adjust_made += 1;
    }
    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
    if adjust_made > 0 {
        note.push_str(&format!("、{adjust_made} 个调整图层"));
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("NV adjustment layers already imported")
        return
    for old, new in (
        (COLLECT_OLD, COLLECT + "\n" + COLLECT_OLD),
        (CALL_OLD, CALL_NEW),
        (GUARD_OLD, GUARD_NEW),
        (NOTE_OLD, NOTE_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("NV adjustment layers import as adjustment layers")


if __name__ == "__main__":
    main()
