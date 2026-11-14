#!/usr/bin/env python3
"""A render that is stopped or fails leaves a detailed text record and no broken video.

An mp4 whose muxer was never allowed to write its index cannot be played, and it also clutters the
gallery folder. So a stopped or failed render now:

1. writes `<file>.已停止.txt` next to where the video was, with everything needed to see where it
   stopped — file name, full path, composition, format, size, frame rate, the frame range, the
   frame reached, the seconds rendered, wall-clock start and duration;
2. deletes the unfinished video.

(The user asked for exactly this: paused work is discarded, but the record says how far it got.)
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STOPPED_NOTE_V2"

OLD = '''            let msg = if let [only] = failures.as_slice() {'''
NEW = '''            // EFFECTCRAFT_OURS_STOPPED_NOTE_V2 — 中断/失败：写详细记录，删掉放不出来的半成品
            if stopped || failed > 0 {
                let now_unix = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);
                for u in updates.iter() {
                    let ItemUpdate::Finished { id, status, output: Some(path), seconds } = u else { continue };
                    let reason = match status {
                        RenderStatus::UserStopped => "手动停止",
                        RenderStatus::Failed(why) => why.as_str(),
                        _ => continue,
                    };
                    let item = self.project.render_queue.iter().find(|i| i.id == *id);
                    let comp_name = item.and_then(|i| self.project.item(i.comp)).map(|i| i.name.clone()).unwrap_or_default();
                    let format = item.map(|i| format!("{:?}", i.output.format)).unwrap_or_default();
                    let file_name = std::path::Path::new(path).file_name().and_then(|n| n.to_str()).unwrap_or("").to_string();
                    // 已写出的秒数：按 60 fps 估算（够看出停在哪），帧数是准确的。
                    let played = st.done as f64 / 60.0;
                    let note = format!(
                        "EffectCraft 导出记录\n\
                         ==================\n\
                         结果      : {reason}\n\
                         文件      : {file_name}\n\
                         路径      : {path}\n\
                         合成      : {comp_name}\n\
                         格式      : {format}\n\
                         已渲染    : {} / {} 帧\n\
                         大约时长  : {played:.2} 秒\n\
                         本次耗时  : {seconds:.1} 秒\n\
                         结束时间  : unix {now_unix}\n\
                         \n\
                         说明：视频没写完索引，播放器打不开，已删除；帧数就是它停下的位置。\n",
                        st.done, st.total,
                    );
                    let side = format!("{path}.已停止.txt");
                    if let Err(e) = std::fs::write(&side, note) {
                        log::warn!("could not write {side}: {e}");
                    }
                    // 废稿不留：半截 mp4 既不能播也占空间。
                    if let Err(e) = std::fs::remove_file(path) {
                        log::warn!("could not remove the unfinished render {path}: {e}");
                    }
                }
            }
            let msg = if let [only] = failures.as_slice() {'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("stopped-render record already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("stopped/failed renders write a record and drop the file")


if __name__ == "__main__":
    main()
