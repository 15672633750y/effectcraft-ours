#!/usr/bin/env python3
"""NodeVideo 的调整图层（NodeAdjustment）也导入成调整图层。

The sample project carries eight of them; they used to be dropped because only media and fill nodes
were read. An adjustment layer changes nothing by itself — the effects inside it have no counterpart
here — but its span and place in the stack are kept, which keeps the rest of the rebuild in step.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_ADJUSTMENT_V1"

COLLECT_OLD = "fn collect_fill_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {\n"
COLLECT_NEW = '''fn is_adjustment_node(node: &Value) -> bool {
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

''' + COLLECT_OLD

CALL_OLD = '''    let mut fills: Vec<&Value> = Vec::new();
    collect_fill_nodes(&doc, &mut fills);
'''
CALL_NEW = '''    let mut fills: Vec<&Value> = Vec::new();
    collect_fill_nodes(&doc, &mut fills);
    let mut adjustments: Vec<&Value> = Vec::new();
    collect_adjustment_nodes(&doc, &mut adjustments);
'''

GUARD_OLD = "    if placed == 0 && fills.is_empty() {\n"
GUARD_NEW = "    if placed == 0 && fills.is_empty() && adjustments.is_empty() {\n"

END_OLD = '''    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
'''
END_NEW = '''    // EFFECTCRAFT_OURS_NV_ADJUSTMENT_V1 — 调整图层
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
        if let Some(cid) = s.active_comp_id()
            && let Some(comp) = s.project.comp_mut(cid)
            && let Some(l) = comp.layers.iter_mut().find(|l| l.id.0 == lid)
        {
            l.start_time = super::Tick::from_seconds_f64(pos);
            l.in_point = super::Tick::from_seconds_f64(pos);
            l.out_point = super::Tick::from_seconds_f64(pos + len);
        }
        adjust_made += 1;
    }
    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
    if adjust_made > 0 {
        note.push_str(&format!("、{adjust_made} 个调整图层"));
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("NV adjustment layers already imported")
        return
    for old, new in ((COLLECT_OLD, COLLECT_NEW), (CALL_OLD, CALL_NEW), (GUARD_OLD, GUARD_NEW), (END_OLD, END_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:36]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("NV adjustment layers import as adjustment layers")


if __name__ == "__main__":
    main()
