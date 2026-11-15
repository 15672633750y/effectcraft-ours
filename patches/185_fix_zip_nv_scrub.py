#!/usr/bin/env python3
"""Three fixes from the phone: the zip is one file, NodeVideo zips import, and the scrub works
while it plays.

* `完整导出工程` wrote the `.ecproj` next to the zip as well, so the folder got two files. The
  project is now written to a temporary file, put inside the zip, and deleted.
* NodeVideo's `.zip` reached the 剪映 branch, which tried to parse it as JSON ("expected value at
  line 1 column 1"). The NodeVideo check now runs before anything is parsed.
* Dragging the full-screen scrub during playback did nothing: playback kept advancing the time and
  overwrote the drag. A drag now pauses playback first, so the finger decides where the picture is.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FIX3_V1"

# 1. NodeVideo 分支提前到 JSON 解析之前
HOOK_OLD = '''    // EFFECTCRAFT_OURS_NODEDVIDEO_V1 — NodeVideo（仿AE）的 zip / .nv：解包并重建时间线
    if let Some(note) = import_nodevideo(s, path) {
        s.toast(note);
        return Ok(Vec::new());
    }
'''
HOOK_NEW = ''

PARSE_OLD = '''    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes).to_string();
'''
PARSE_NEW = '''    // EFFECTCRAFT_OURS_FIX3_V1 — NodeVideo 的 zip / .nv 先处理：zip 不是 JSON，不能在下面被解析
    if let Some(note) = import_nodevideo(s, path) {
        s.toast(note);
        return Ok(Vec::new());
    }
    let bytes = s.services.read_file(path).map_err(|e| EngineError::Other(format!("cannot read {path}: {e}")))?;
    let text = String::from_utf8_lossy(&bytes).to_string();
'''

# 2. 工程文件写到临时目录，不进导出文件夹
PROJ_OLD = '''    let project_path = format!("{}.ecproj", target.trim_end_matches(".zip"));
    s.execute("file.saveCopy", json!({"path": project_path}))?;
'''
PROJ_NEW = '''    // EFFECTCRAFT_OURS_FIX3_V1 — 工程文件写到临时目录，只把 zip 留在导出文件夹
    let project_path = std::env::temp_dir().join(format!("ec-share-{}.ecproj", std::process::id()));
    let project_path = project_path.to_string_lossy().to_string();
    s.execute("file.saveCopy", json!({"path": project_path}))?;
'''

# 3. 全屏拖动时先暂停播放
SCRUB_OLD = '''    let resp = ui.interact(track.expand2(egui::vec2(0.0, 8.0)), egui::Id::unique("ours-fs-scrub"), egui::Sense::click_and_drag());
'''
SCRUB_NEW = '''    let resp = ui.interact(track.expand2(egui::vec2(0.0, 8.0)), egui::Id::unique("ours-fs-scrub"), egui::Sense::click_and_drag());
    // EFFECTCRAFT_OURS_FIX3_V1 — 播放中拖动会立刻被播放进度覆盖，所以先暂停。
    if resp.drag_started() && app.playback.playing {
        let _ = crate::menus::invoke(app, &ctx, "playback.toggle", serde_json::json!({}));
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    changed = []
    ext = root / "crates/engine/src/cmd/import_ext.rs"
    src = ext.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(HOOK_OLD) != 1 or src.count(PARSE_OLD) != 1:
            raise SystemExit(f"nv anchors: hook={src.count(HOOK_OLD)} parse={src.count(PARSE_OLD)}")
        src = src.replace(HOOK_OLD, HOOK_NEW, 1)
        src = src.replace(PARSE_OLD, PARSE_NEW, 1)
        ext.write_text(src, encoding="utf-8")
        changed.append("nv order")
    exp = root / "crates/engine/src/cmd/ours_export.rs"
    src = exp.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(PROJ_OLD) != 1:
            raise SystemExit(f"project anchor: {src.count(PROJ_OLD)}")
        src = src.replace(PROJ_OLD, PROJ_NEW, 1)
        exp.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
        changed.append("single file")
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if "drag_started() && app.playback.playing" not in src:
        if src.count(SCRUB_OLD) != 1:
            raise SystemExit(f"scrub anchor: {src.count(SCRUB_OLD)}")
        frame.write_text(src.replace(SCRUB_OLD, SCRUB_NEW, 1), encoding="utf-8")
        changed.append("scrub pause")
    print("fixed: " + ", ".join(changed) if changed else "already fixed")


if __name__ == "__main__":
    main()
