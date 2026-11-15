#!/usr/bin/env python3
"""A 剪映/CapCut draft becomes an editing timeline, not just a folder of media.

The official importer already reads OpenTimelineIO (`file.importTimeline`), so the draft is converted
to OTIO instead of hand-building a project: one Video/Audio track per draft track, a clip per
segment with its source in/out, `Gap` items for the holes between them. The result is a composition
whose clips sit at the times they had in 剪映 — cuts, order, durations and speed-trimmed ranges come
back; transitions/effects/text are not converted (they are 剪映's own), and the toast says so.

If the conversion finds nothing usable (no segments, no reachable media) the old behaviour stays:
import the media the draft references.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CAPCUT_TIMELINE_V1"

IMPORT_FIX = "use serde_json::Value;\n"
IMPORT_NEW = "use serde_json::{json, Value};\n"

HOOK_OLD = '''    let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: {e}")))?;
        capcut_media(&doc)
    };
'''
HOOK_NEW = '''    let doc: Value = serde_json::from_str(&text).map_err(|e| EngineError::Other(format!("{path}: {e}")))?;
        capcut_media(&doc)
    };
    // EFFECTCRAFT_OURS_CAPCUT_TIMELINE_V1 — 草稿能重建时间线时，按时间线导入而不是只丢素材
    if path.to_ascii_lowercase().ends_with("draft_content.json")
        && let Some(note) = import_capcut_timeline(s, path, &text)
    {
        s.toast(note);
        return Ok(Vec::new());
    }
'''

HELPERS = r'''
/// 把剪映草稿写成 OTIO，再交给官方的 timeline 导入器。返回一句给用户的说明。
fn import_capcut_timeline(s: &mut Session, path: &str, text: &str) -> Option<String> {
    let doc: Value = serde_json::from_str(text).ok()?;
    let dir = dir_of(path);
    let rate = doc.get("fps").and_then(Value::as_f64).filter(|r| *r > 1.0 && *r < 240.0).unwrap_or(30.0);
    let list = doc.get("tracks").and_then(Value::as_array)?;
    let mut tracks: Vec<Value> = Vec::new();
    let mut clips = 0usize;
    let mut missing = 0usize;
    for t in list {
        let kind = t.get("type").and_then(Value::as_str).unwrap_or("video");
        let audio = kind == "audio";
        if kind != "video" && !audio {
            continue;
        }
        let mut children: Vec<Value> = Vec::new();
        let mut cursor_us: i64 = 0;
        if let Some(segs) = t.get("segments").and_then(Value::as_array) {
            for seg in segs {
                let Some(tr) = seg.get("target_timerange") else { continue };
                let start = tr.get("start").and_then(Value::as_i64).unwrap_or(0);
                let dur = tr.get("duration").and_then(Value::as_i64).unwrap_or(0);
                if dur <= 0 {
                    continue;
                }
                let src_start = seg
                    .get("source_timerange")
                    .and_then(|x| x.get("start"))
                    .and_then(Value::as_i64)
                    .unwrap_or(0);
                let mat_id = seg.get("material_id").and_then(Value::as_str).unwrap_or("");
                let mut file: Option<String> = None;
                for key in ["videos", "audios"] {
                    if let Some(arr) = doc.get("materials").and_then(|m| m.get(key)).and_then(Value::as_array) {
                        for m in arr {
                            if m.get("id").and_then(Value::as_str) == Some(mat_id) {
                                file = m.get("path").and_then(Value::as_str).map(str::to_string);
                            }
                        }
                    }
                }
                let Some(raw) = file else { continue };
                let Some(media) = resolve(s, &raw, &dir) else {
                    missing += 1;
                    continue;
                };
                if start > cursor_us {
                    let hole = frames_of(start - cursor_us, rate);
                    if hole > 0 {
                        children.push(otio_gap(hole, rate));
                    }
                }
                children.push(otio_clip(&media, src_start, dur, rate));
                cursor_us = start + dur;
                clips += 1;
            }
        }
        if children.is_empty() {
            continue;
        }
        tracks.push(json!({
            "OTIO_SCHEMA": "Track.1",
            "name": if audio { "A" } else { "V" },
            "kind": if audio { "Audio" } else { "Video" },
            "children": children,
            "effects": [],
            "markers": [],
            "enabled": true,
            "metadata": {}
        }));
    }
    if clips == 0 {
        return None;
    }
    let name = std::path::Path::new(path)
        .parent()
        .and_then(|d| d.file_name())
        .and_then(|n| n.to_str())
        .unwrap_or("剪映工程")
        .to_string();
    let timeline = json!({
        "OTIO_SCHEMA": "Timeline.1",
        "name": name,
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
    let mut note = format!("已按工程重建时间线：{clips} 个片段");
    if missing > 0 {
        note.push_str(&format!("，{missing} 个素材找不到"));
    }
    note.push_str("（转场/特效/文字不转换）");
    Some(note)
}

fn frames_of(us: i64, rate: f64) -> i64 {
    ((us as f64) / 1_000_000.0 * rate).round().max(0.0) as i64
}

fn otio_rt(value: i64, rate: f64) -> Value {
    json!({"OTIO_SCHEMA": "RationalTime.1", "rate": rate, "value": value})
}

fn otio_tr(start: i64, dur: i64, rate: f64) -> Value {
    json!({"OTIO_SCHEMA": "TimeRange.1", "start_time": otio_rt(start, rate), "duration": otio_rt(dur, rate)})
}

fn otio_gap(frames: i64, rate: f64) -> Value {
    json!({
        "OTIO_SCHEMA": "Gap.1",
        "name": "",
        "source_range": otio_tr(0, frames, rate),
        "effects": [],
        "markers": [],
        "enabled": true,
        "metadata": {}
    })
}

fn otio_clip(path: &str, src_start_us: i64, dur_us: i64, rate: f64) -> Value {
    let name = std::path::Path::new(path).file_name().and_then(|n| n.to_str()).unwrap_or("");
    json!({
        "OTIO_SCHEMA": "Clip.1",
        "name": name,
        "source_range": otio_tr(frames_of(src_start_us, rate), frames_of(dur_us, rate), rate),
        "media_reference": {
            "OTIO_SCHEMA": "ExternalReference.1",
            "name": name,
            "target_url": format!("file://{path}"),
            "available_range": Value::Null,
            "available_image_bounds": Value::Null,
            "metadata": {}
        },
        "effects": [],
        "markers": [],
        "enabled": true,
        "metadata": {}
    })
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    if not path.exists():
        raise SystemExit("import_ext.rs missing (136_import_recipes must run first)")
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("draft timeline already installed")
        return
    if src.count(IMPORT_FIX) != 1:
        raise SystemExit(f"import anchor: {src.count(IMPORT_FIX)}")
    src = src.replace(IMPORT_FIX, IMPORT_NEW, 1)
    if src.count(HOOK_OLD) != 1:
        raise SystemExit(f"hook anchor: {src.count(HOOK_OLD)}")
    src = src.replace(HOOK_OLD, HOOK_NEW, 1)
    src += HELPERS
    path.write_text(src, encoding="utf-8")
    print("CapCut/剪映 drafts rebuild the timeline through OTIO")


if __name__ == "__main__":
    main()
