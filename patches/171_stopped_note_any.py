#!/usr/bin/env python3
"""A stopped render always leaves its `.已停止.txt` — the stop path reports no output path.

`ItemUpdate::Finished` carries `output: None` when an item is stopped or cancelled (see the three
places that push that status), so the earlier version of this block — which only handled
`output: Some(path)` — never ran for a manual stop. The path is therefore resolved from the queue
item when the update has none, and the note is written before the unfinished file is removed.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STOPPED_NOTE_V3"
START = "            // EFFECTCRAFT_OURS_STOPPED_NOTE_V2"
END = "            let msg = if let [only] = failures.as_slice() {"

BLOCK = '''            // EFFECTCRAFT_OURS_STOPPED_NOTE_V3 — 中断/失败：写详细记录，删掉放不出来的半成品
            if stopped || failed > 0 {
                let now_unix = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);
                for u in updates.iter() {
                    let ItemUpdate::Finished { id, status, seconds, output } = u else { continue };
                    let reason = match status {
                        RenderStatus::UserStopped => "手动停止",
                        RenderStatus::Failed(why) => why.as_str(),
                        _ => continue,
                    };
                    let Some(item) = self.project.render_queue.iter().find(|i| i.id == *id).cloned() else { continue };
                    // 停止的条目 update 里没有路径，按队列里这一条的设置重新算一遍。
                    let path = output.clone().or_else(|| self.resolve_output(&item));
                    let Some(path) = path else { continue };
                    let comp_name = self.project.item(item.comp).map(|i| i.name.clone()).unwrap_or_default();
                    let format = format!("{:?}", item.output.format);
                    let file_name = std::path::Path::new(&path).file_name().and_then(|n| n.to_str()).unwrap_or("").to_string();
                    let played = st.done as f64 / 60.0;
                    let note = format!(
                        "EffectCraft 导出记录\\n\\
                         ==================\\n\\
                         结果      : {reason}\\n\\
                         文件      : {file_name}\\n\\
                         路径      : {path}\\n\\
                         合成      : {comp_name}\\n\\
                         格式      : {format}\\n\\
                         已渲染    : {} / {} 帧\\n\\
                         大约时长  : {played:.2} 秒\\n\\
                         本次耗时  : {seconds:.1} 秒\\n\\
                         结束时间  : unix {now_unix}\\n\\
                         \\n\\
                         说明：视频没写完索引，播放器打不开，已删除；帧数就是它停下的位置。\\n",
                        st.done, st.total,
                    );
                    let side = format!("{path}.已停止.txt");
                    if let Err(e) = std::fs::write(&side, note) {
                        log::warn!("could not write {side}: {e}");
                    }
                    if let Err(e) = std::fs::remove_file(&path) {
                        log::warn!("could not remove the unfinished render {path}: {e}");
                    }
                }
            }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("stopped note already handles a missing path")
        return
    start = src.find(START)
    end = src.find(END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f"region not found (start={start}, end={end})")
    path.write_text(src[:start] + BLOCK + src[end:], encoding="utf-8")
    print("a stopped render always writes its note")


if __name__ == "__main__":
    main()
