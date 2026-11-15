#!/usr/bin/env python3
"""NodeVideo ("仿AE") projects import with their timeline.

A NodeVideo project is a `.zip` holding `*.nv` (JSON: a node tree, each node with a `TimeLine`) and
`Medias/`. The `.nv` tree is walked for media nodes — `NodeMediaImage`, `NodeMediaVideo`,
`NodeMediaAudio` — and each becomes a layer:

* `Pos`            → where the clip starts on the timeline
* `Start`          → the source in point
* `(End - Start)`  → the source length
* `1 / Stretch`    → its speed (not converted: layers keep 100 %)

The media the zip carries is unpacked next to it (`<zip>.unpacked/`) because the imported footage
must point at a real file; the project file itself is turned into OTIO and handed to the official
`file.importTimeline` importer, exactly like the 剪映 drafts.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NODEDVIDEO_V1"

CARGO_OLD = 'serde_json = { workspace = true }\n'
CARGO_NEW = 'serde_json = { workspace = true }\nzip = { version = "2", default-features = false, features = ["deflate"] }\n'

HELPERS_VIS_OLD = "fn frames_of(us: i64, rate: f64) -> i64 {"
HELPERS_VIS_NEW = "pub(crate) fn frames_of(us: i64, rate: f64) -> i64 {"

DETECT_OLD = '''    if lower.ends_with(".nk") {
        return true;
    }'''
DETECT_NEW = '''    if path.to_ascii_lowercase().ends_with(".nk") || lower.ends_with(".nv") {
        return true;
    }
    // NodeVideo 工程是 zip：里面有 .nv
    if lower.ends_with(".zip") {
        return true;
    }'''

HOOK_OLD = '''    // EFFECTCRAFT_OURS_CAPCUT_TIMELINE_V1 — 草稿能重建时间线时，按时间线导入而不是只丢素材
    if path.to_ascii_lowercase().ends_with("draft_content.json")
'''
HOOK_NEW = '''    // EFFECTCRAFT_OURS_NODEDVIDEO_V1 — NodeVideo（仿AE）的 zip / .nv：解包并重建时间线
    if let Some(note) = import_nodevideo(s, path) {
        s.toast(note);
        return Ok(Vec::new());
    }
    // EFFECTCRAFT_OURS_CAPCUT_TIMELINE_V1 — 草稿能重建时间线时，按时间线导入而不是只丢素材
    if path.to_ascii_lowercase().ends_with("draft_content.json")
'''

MODULE = r'''

// ---------------------------------------------------------------- NodeVideo (仿AE)

/// A NodeVideo project: a `.zip` with `*.nv` (JSON) and `Medias/`, or the `.nv` itself.
pub(crate) fn import_nodevideo(s: &mut Session, path: &str) -> Option<String> {
    let lower = path.to_ascii_lowercase();
    let unpacked = format!("{path}.unpacked");
    let mut project_json: Option<String> = None;
    if lower.ends_with(".zip") {
        let file = std::fs::File::open(path).ok()?;
        let mut zip = zip::ZipArchive::new(file).ok()?;
        let mut names: Vec<String> = (0..zip.len()).filter_map(|i| zip.by_index(i).ok().map(|e| e.name().to_string())).collect();
        names.sort();
        if !names.iter().any(|n| n.to_ascii_lowercase().ends_with(".nv")) {
            return None; // 不是 NodeVideo 工程，交给后面的分支
        }
        std::fs::create_dir_all(&unpacked).ok()?;
        for name in names {
            let is_media = name.to_ascii_lowercase().starts_with("medias/");
            let is_project = name.to_ascii_lowercase().ends_with(".nv");
            if !is_media && !is_project {
                continue;
            }
            let mut entry = zip.by_name(&name).ok()?;
            if entry.is_dir() {
                continue;
            }
            let rel = name.trim_start_matches('/');
            let out_path = format!("{unpacked}/{rel}");
            if let Some(dir) = std::path::Path::new(&out_path).parent() {
                let _ = std::fs::create_dir_all(dir);
            }
            let mut out = std::fs::File::create(&out_path).ok()?;
            std::io::copy(&mut entry, &mut out).ok()?;
            if is_project && project_json.is_none() {
                project_json = std::fs::read_to_string(&out_path).ok();
            }
        }
    } else {
        project_json = std::fs::read_to_string(path).ok();
    }
    let text = project_json?;
    let doc: Value = serde_json::from_str(&text).ok()?;
    let media_dir = format!("{unpacked}/Medias");
    let mut nodes: Vec<&Value> = Vec::new();
    collect_media_nodes(&doc, &mut nodes);
    if nodes.is_empty() {
        return None;
    }
    let rate = 30.0f64;
    let mut tracks: Vec<Value> = Vec::new();
    let mut placed = 0usize;
    let mut missing = 0usize;
    for node in nodes {
        let tl = node.get("TimeLine");
        let pos = tl.and_then(|t| t.get("Pos")).and_then(Value::as_f64).unwrap_or(0.0);
        let start = tl.and_then(|t| t.get("Start")).and_then(Value::as_f64).unwrap_or(0.0);
        let end = tl.and_then(|t| t.get("End")).and_then(Value::as_f64).unwrap_or(0.0);
        let stretch = tl.and_then(|t| t.get("Stretch")).and_then(Value::as_f64).filter(|v| *v > 0.01).unwrap_or(1.0);
        let src_len = (end - start).max(0.0);
        if src_len <= 0.0 {
            continue;
        }
        let Some(raw) = asset_path(node) else { continue };
        let name = std::path::Path::new(&raw).file_name().and_then(|n| n.to_str()).unwrap_or("");
        let candidate = format!("{media_dir}/{name}");
        let media = if std::path::Path::new(&candidate).is_file() {
            candidate
        } else {
            let beside = if dir_of(path).is_empty() { name.to_string() } else { format!("{}/{}", dir_of(path), name) };
            if std::path::Path::new(&beside).is_file() {
                beside
            } else {
                missing += 1;
                continue;
            }
        };
        let audio = is_audio(&media);
        let visible = src_len / stretch;
        let mut children: Vec<Value> = Vec::new();
        let hole = frames_of((pos * 1_000_000.0) as i64, rate);
        if hole > 0 {
            children.push(otio_gap(hole, rate));
        }
        children.push(otio_clip(&media, (start * 1_000_000.0) as i64, (src_len * 1_000_000.0) as i64, rate));
        let _ = visible;
        tracks.push(json!({
            "OTIO_SCHEMA": "Track.1",
            "name": node.get("Name").and_then(Value::as_str).unwrap_or("layer"),
            "kind": if audio { "Audio" } else { "Video" },
            "children": children,
            "effects": [],
            "markers": [],
            "enabled": !node.get("Hided").and_then(Value::as_bool).unwrap_or(false),
            "metadata": {}
        }));
        placed += 1;
    }
    if placed == 0 {
        return None;
    }
    let timeline = json!({
        "OTIO_SCHEMA": "Timeline.1",
        "name": std::path::Path::new(path).file_stem().and_then(|n| n.to_str()).unwrap_or("NodeVideo"),
        "global_start_time": otio_rt(0, rate),
        "metadata": {},
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "name": "stack",
            "children": tracks,
            "effects": [],
            "markers": [],
            "enabled": true,
            "metadata": {}
        }
    });
    let otio_path = format!("{path}.otio");
    s.services.write_file(&otio_path, timeline.to_string().as_bytes()).ok()?;
    let imported = s.execute("file.importTimeline", json!({"path": otio_path}));
    let _ = std::fs::remove_file(&otio_path);
    imported.ok()?;
    let mut note = format!("已按 NodeVideo 工程重建时间线：{placed} 个图层");
    if missing > 0 {
        note.push_str(&format!("，{missing} 个素材缺失"));
    }
    note.push_str("（速度/效果/关键帧不转换，素材已解包到 .unpacked 目录）");
    Some(note)
}

fn is_audio(path: &str) -> bool {
    let p = path.to_ascii_lowercase();
    p.ends_with(".mp3") || p.ends_with(".wav") || p.ends_with(".m4a") || p.ends_with(".aac") || p.ends_with(".flac")
}

fn collect_media_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {
    if let Some(t) = node.get("$type").and_then(Value::as_str) {
        let media = t.contains("NodeMedia") && (t.contains("Image") || t.contains("Video") || t.contains("Audio"));
        if media && asset_path(node).is_some() {
            out.push(node);
        }
    }
    if let Some(children) = node.get("ChildList").and_then(Value::as_array) {
        for c in children {
            collect_media_nodes(c, out);
        }
    }
}

fn asset_path(node: &Value) -> Option<String> {
    for key in ["AssetImage", "AssetVideo", "AssetAudio", "Asset"] {
        if let Some(p) = node.get(key).and_then(|a| a.get("AbsolutePath")).and_then(Value::as_str)
            && !p.is_empty()
        {
            return Some(p.to_string());
        }
    }
    None
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    cargo = root / "crates/engine/Cargo.toml"
    src = cargo.read_text(encoding="utf-8")
    if "zip = { version" not in src:
        if src.count(CARGO_OLD) != 1:
            raise SystemExit(f"cargo anchor: {src.count(CARGO_OLD)}")
        cargo.write_text(src.replace(CARGO_OLD, CARGO_NEW, 1), encoding="utf-8")
        print("zip crate added to the engine")
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("NodeVideo import already installed")
        return
    for old, new in ((HELPERS_VIS_OLD, HELPERS_VIS_NEW), (DETECT_OLD, DETECT_NEW), (HOOK_OLD, HOOK_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:44]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    src += MODULE
    path.write_text(src, encoding="utf-8")
    print("NodeVideo (.zip / .nv) rebuilds its timeline")


if __name__ == "__main__":
    main()
