#!/usr/bin/env python3
"""A stopped render leaves a note saying how far it got.

An mp4 whose muxer never wrote its index cannot be played, so an interrupted file cannot be
"watched" to see where it stopped. Next to it goes a small text file with the frame count reached,
so the answer is readable without a player: `合成 1-…​.mp4.已停止.txt`.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STOPPED_NOTE_V1"

OLD = '''            let msg = if let [only] = failures.as_slice() {'''
NEW = '''            // EFFECTCRAFT_OURS_STOPPED_NOTE_V1 — 中断的成片旁边留一份文字说明，能看出渲染到哪
            if stopped || failed > 0 {
                for u in updates.iter() {
                    if let ItemUpdate::Finished { status, output: Some(path), seconds, .. } = u {
                        let interrupted = matches!(status, RenderStatus::UserStopped)
                            || matches!(status, RenderStatus::Failed(_));
                        if !interrupted {
                            continue;
                        }
                        let note = format!(
                            "这次渲染没有完成：已渲染 {} / {} 帧（约 {:.1} 秒），用时 {:.1} 秒。\\n\\
                             视频文件缺少索引，播放器打不开是正常的；帧数就是它停下的位置。\\n",
                            st.done, st.total, st.done as f64 / 60.0, seconds
                        );
                        let side = format!("{path}.已停止.txt");
                        if let Err(e) = std::fs::write(&side, note) {
                            log::warn!("could not write {side}: {e}");
                        }
                    }
                }
            }
            let msg = if let [only] = failures.as_slice() {'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/render_queue.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("stopped-render note already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("stopped renders leave a note")


if __name__ == "__main__":
    main()
