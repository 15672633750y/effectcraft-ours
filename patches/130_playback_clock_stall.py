#!/usr/bin/env python3
"""Playback that freezes on the first frame while the sound plays: follow the wall clock when the
audio clock stops moving.

The preview shows the frame under the audible sample, and that sample comes from the audio device's
consumed-frame count. On this Android build the count has been seen to stand still while the device
keeps playing, so the sound ran and the picture stayed on frame 0 (scrubbing still worked, because
scrubbing sets the time directly). Now the audio clock is watched every pass; once it has not moved
for half a second while the preview plays, the frame comes from the wall clock, the prefetch
follows the same clock (so it stops re-requesting the stuck frames), the stalled frame is requested
directly, and one log line says it happened.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOCK_STALL_V1"

DESTRUCTURE_OLD = "        let PlaybackPass { ctx, now, series, video, frame_rate: fr, cur, .. } = *pass;\n"
DESTRUCTURE_NEW = "        let PlaybackPass { ctx, now, series, video, frame_rate: fr, cur, cid, scale, .. } = *pass;\n"

TARGET_OLD = '''        let snap = |f: i64| wa + (f - wa).div_euclid(step) * step;
        let target = snap(audio::frame_of_sample(a.clock(), a.rate, fr).clamp(wa, wb));
'''
TARGET_NEW = '''        let snap = |f: i64| wa + (f - wa).div_euclid(step) * step;
        // EFFECTCRAFT_OURS_CLOCK_STALL_V1
        // The device clock can stand still while the sound plays: the picture then never leaves
        // the first frame. Watch it; once it has not moved for half a second, take the frame from
        // the wall clock so playback moves, and say so once in the log.
        let clock_key = egui::Id::new("playback-audio-clock-stall");
        let stall_flag = egui::Id::new("playback-audio-clock-stalled");
        let now_tick = a.clock();
        let last = ctx.data(|d| d.get_temp::<(i64, f64)>(clock_key));
        // 播放刚开始的头一秒不算停滞（上一次播放留下的记录会误判）。
        let stalled = matches!(last, Some((sample, at)) if sample == now_tick && now - at > 0.5 && now - self.playback.start_wall > 1.0);
        if last.is_none_or(|(sample, _)| sample != now_tick) {
            ctx.data_mut(|d| d.insert_temp(clock_key, (now_tick, now)));
        }
        ctx.data_mut(|d| d.insert_temp(stall_flag, stalled));
        if stalled {
            let once = egui::Id::new("playback-audio-clock-stall-logged");
            if !ctx.data(|d| d.get_temp::<bool>(once).unwrap_or(false)) {
                ctx.data_mut(|d| d.insert_temp(once, true));
                log::warn!(target: "effectcraft_ui", "audio clock stalled at sample {now_tick}; the picture follows the wall clock");
            }
        }
        let target = if stalled {
            // Where the picture would be if the wall clock drove it.
            let elapsed = (now - self.playback.start_wall).max(0.0);
            let frames = ((elapsed * self.playback.fps) / step as f64).floor() as i64;
            let want = snap((self.playback.start_frame + frames).clamp(wa, wb));
            // The prefetch follows the same clock now; ask for this frame in case it fell outside
            // the window while the sound's clock was standing still.
            self.request_frame(cid, want, scale);
            want
        } else {
            snap(audio::frame_of_sample(a.clock(), a.rate, fr).clamp(wa, wb))
        };
'''

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/prefetch.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("clock stall guard already installed")
        return
    for old, new in ((DESTRUCTURE_OLD, DESTRUCTURE_NEW), (TARGET_OLD, TARGET_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:50]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("playback follows the wall clock when the audio clock stalls")


if __name__ == "__main__":
    main()
