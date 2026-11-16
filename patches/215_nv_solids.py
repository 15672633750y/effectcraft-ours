#!/usr/bin/env python3
"""NodeVideo 工程里的纯色层（NodeFill）也导入成纯色图层。

They used to be skipped — the importer only looked at media nodes — so a project made of solids
imported as "nothing to rebuild". Each fill becomes a solid layer with its colour, at its own place
on the timeline. The colour is read tolerantly (object with r/g/b, or an array, 0–1 or 0–255), since
only one sample of the format was available; a missing colour falls back to white instead of failing
the import.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_SOLIDS_V1"

COLLECT_OLD = '''fn collect_media_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {'''
COLLECT_NEW = '''/// EFFECTCRAFT_OURS_NV_SOLIDS_V1 — 纯色节点（NodeFill）。
fn is_fill_node(node: &Value) -> bool {
    node.get("$type")
        .and_then(Value::as_str)
        .is_some_and(|t| t.contains("NodeFill") || t.contains("NodeSolid") || t.contains("NodeColorFill"))
}

/// 颜色：接受 {r,g,b} / {R,G,B} / [r,g,b(,a)]，0–1 或 0–255。
fn fill_color(node: &Value) -> [f32; 3] {
    let pick = |o: &Value, keys: [&str; 3]| -> Option<[f32; 3]> {
        let mut out = [0.0f32; 3];
        for (i, k) in keys.iter().enumerate() {
            out[i] = o.get(*k).and_then(Value::as_f64)? as f32;
        }
        Some(out)
    };
    let raw = node
        .get("Color")
        .or_else(|| node.get("FillColor"))
        .or_else(|| node.get("ColorValue"));
    let mut c = match raw {
        Some(Value::Array(a)) if a.len() >= 3 => {
            let g = |i: usize| a.get(i).and_then(Value::as_f64).unwrap_or(0.0) as f32;
            [g(0), g(1), g(2)]
        }
        Some(o @ Value::Object(_)) => pick(o, ["r", "g", "b"]).or_else(|| pick(o, ["R", "G", "B"])).unwrap_or([1.0, 1.0, 1.0]),
        _ => [1.0, 1.0, 1.0],
    };
    if c.iter().any(|v| *v > 1.0) {
        c = [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0];
    }
    [c[0].clamp(0.0, 1.0), c[1].clamp(0.0, 1.0), c[2].clamp(0.0, 1.0)]
}

fn collect_fill_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {
    if is_fill_node(node) {
        out.push(node);
    }
    if let Some(children) = node.get("ChildList").and_then(Value::as_array) {
        for c in children {
            collect_fill_nodes(c, out);
        }
    }
}

fn collect_media_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {'''

CALL_OLD = '''    let mut nodes: Vec<&Value> = Vec::new();
    collect_media_nodes(&doc, &mut nodes);
'''
CALL_NEW = '''    let mut nodes: Vec<&Value> = Vec::new();
    collect_media_nodes(&doc, &mut nodes);
    // EFFECTCRAFT_OURS_NV_SOLIDS_V1 — 纯色层单独收集
    let mut fills: Vec<&Value> = Vec::new();
    collect_fill_nodes(&doc, &mut fills);
'''

PLACED_OLD = '''    if placed == 0 {
        return None;
    }
'''
PLACED_NEW = '''    if placed == 0 && fills.is_empty() {
        return None;
    }
'''

END_OLD = '''    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
'''
END_NEW = '''    // EFFECTCRAFT_OURS_NV_SOLIDS_V1 — 纯色层：新建纯色并摆到原来的时间位置
    let mut solids_made = 0usize;
    for node in fills {
        let tl = node.get("TimeLine");
        let pos = tl.and_then(|t| t.get("Pos")).and_then(Value::as_f64).unwrap_or(0.0);
        let start = tl.and_then(|t| t.get("Start")).and_then(Value::as_f64).unwrap_or(0.0);
        let end = tl.and_then(|t| t.get("End")).and_then(Value::as_f64).unwrap_or(0.0);
        let len = (end - start).max(0.0);
        if len <= 0.0 {
            continue;
        }
        let c = fill_color(node);
        let name = node.get("Name").and_then(Value::as_str).unwrap_or("纯色").to_string();
        let hex = format!(
            "#{:02x}{:02x}{:02x}",
            (c[0] * 255.0).round() as u32,
            (c[1] * 255.0).round() as u32,
            (c[2] * 255.0).round() as u32
        );
        let Ok(res) = s.execute("layer.newSolid", json!({"name": name, "color": hex})) else { continue };
        let Some(lid) = res.get("layer").and_then(Value::as_u64) else { continue };
        if let Some(cid) = s.active_comp_id()
            && let Some(comp) = s.project.comp_mut(cid)
            && let Some(l) = comp.layers.iter_mut().find(|l| l.id.0 == lid)
        {
            l.start_time = effectcraft_project::Tick::from_seconds_f64(pos);
            l.in_point = effectcraft_project::Tick::from_seconds_f64(pos);
            l.out_point = effectcraft_project::Tick::from_seconds_f64(pos + len);
        }
        solids_made += 1;
    }
    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
    if solids_made > 0 {
        note.push_str(&format!("、{solids_made} 个纯色层"));
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("NV solids already imported")
        return
    for old, new in (
        (COLLECT_OLD, COLLECT_NEW),
        (CALL_OLD, CALL_NEW),
        (PLACED_OLD, PLACED_NEW),
        (END_OLD, END_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("NV fill nodes import as solid layers")


if __name__ == "__main__":
    main()
