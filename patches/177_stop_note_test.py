#!/usr/bin/env python3
"""The stop-note writing becomes a function, and a test covers it.

The note (frames reached, reason, file name, path) and the deletion of the unfinished video used to
live inline in `poll_render`, reachable only by interrupting a real render. Pulled into
`write_stop_note`, a unit test can check both halves: the note names the frame it stopped at, and
the broken mp4 is gone afterwards.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STOP_NOTE_TEST_V1"

BLOCK_START = "            // EFFECTCRAFT_OURS_STOPPED_NOTE_V3"
BLOCK_END = "            let msg = if let [only] = failures.as_slice() {"

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
                    let path = output.clone().or_else(|| self.resolve_output(&item));
                    let Some(path) = path else { continue };
                    let comp_name = self.project.item(item.comp).map(|i| i.name.clone()).unwrap_or_default();
                    let format = format!("{:?}", item.output.format);
                    if let Err(e) = write_stop_note(&path, reason, &comp_name, &format, st.done, st.total, *seconds, now_unix) {
                        log::warn!("{e}");
                    }
                }
            }
'''

HELPER = r'''

// EFFECTCRAFT_OURS_STOP_NOTE_TEST_V1
/// A stopped or failed render leaves a readable record and no unplayable half-file.
///
/// An mp4 whose index was never written cannot be opened, so it is deleted; the note next to it says
/// how far the render got, which is what the user asked for.
#[allow(clippy::too_many_arguments)]
pub(crate) fn write_stop_note(
    path: &str,
    reason: &str,
    comp: &str,
    format: &str,
    done: u64,
    total: u64,
    seconds: f64,
    now_unix: u64,
) -> std::io::Result<()> {
    let file_name = std::path::Path::new(path).file_name().and_then(|n| n.to_str()).unwrap_or("");
    let played = done as f64 / 60.0;
    let note = format!(
        "EffectCraft 导出记录\n\
         ==================\n\
         结果      : {reason}\n\
         文件      : {file_name}\n\
         路径      : {path}\n\
         合成      : {comp}\n\
         格式      : {format}\n\
         已渲染    : {done} / {total} 帧\n\
         大约时长  : {played:.2} 秒\n\
         本次耗时  : {seconds:.1} 秒\n\
         结束时间  : unix {now_unix}\n\
         \n\
         说明：视频没写完索引，播放器打不开，已删除；帧数就是它停下的位置。\n",
    );
    let side = format!("{path}.已停止.txt");
    std::fs::write(&side, note)?;
    match std::fs::remove_file(path) {
        Ok(()) => Ok(()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(e) => Err(e),
    }
}

#[cfg(test)]
mod stop_note_tests {
    use super::write_stop_note;

    #[test]
    fn a_stop_note_names_the_frame_and_the_file_is_removed() {
        let dir = std::env::temp_dir().join(format!("ec-stop-note-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let video = dir.join("clip.mp4");
        std::fs::write(&video, b"half an mp4").unwrap();
        let path = video.to_string_lossy().to_string();
        write_stop_note(&path, "手动停止", "合成 1", "H264", 120, 300, 4.5, 1_700_000_000).unwrap();
        let note = std::fs::read_to_string(format!("{path}.已停止.txt")).unwrap();
        assert!(note.contains("120 / 300"), "{note}");
        assert!(note.contains("手动停止"), "{note}");
        assert!(note.contains("clip.mp4"), "{note}");
        assert!(!video.exists(), "the unfinished video is gone");
        let _ = std::fs::remove_dir_all(&dir);
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("stop-note helper and test already installed")
        return
    start = src.find(BLOCK_START)
    end = src.find(BLOCK_END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f"block not found (start={start}, end={end})")
    src = src[:start] + BLOCK + src[end:]
    src += HELPER.replace("EFFECTCRAFT_OURS_STOP_NOTE_TEST_V1", MARKER)
    path.write_text(src, encoding="utf-8")
    print("stop note extracted and tested")


if __name__ == "__main__":
    main()
