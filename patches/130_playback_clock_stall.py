#!/usr/bin/env python3
"""Preview playback: start at once, keep moving when the audio clock stops, loop at the end.

Three separate stalls had the same symptom (sound runs, picture does not):

1. **The first second.** The preview shows the frame under the audible sample, and the device's
   consumed-frame clock reads 0 until the audio stream has actually started. The picture then sat
   on the first frame until it did. It now follows the wall clock until the audio clock moves.
2. **Mid-playback.** On this Android build that clock has been seen to stop while the sound keeps
   playing. Once it has not moved for half a second the wall clock drives the picture, the frame is
   requested directly, and one line is logged.
3. **The end.** The audio device reports `finished()` and the preview stopped there. After Effects
   loops the work area instead, so this restarts the sound and the picture from the work area's
   first frame when the preview loops (`play_with` sets `looping`).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOCK_STALL_V2"

HEAD_OLD = '''        let PlaybackPass { ctx, now, series, video, frame_rate: fr, cur, .. } = *pass;
        let FrameWindow { first: wa, last: wb } = pass.window;
        let Some(a) = &self.audio else { return false };
        if a.finished() {
            if video {
                self.session.set_time(fr.tick_of(wb));
            } else {
                self.playback.audio_frame = Some(wb);
            }
            self.stop();
            return true;
        }
'''
HEAD_NEW = '''        let PlaybackPass { ctx, now, series, video, frame_rate: fr, cur, cid, scale, looping, .. } = *pass;
        let FrameWindow { first: wa, last: wb } = pass.window;
        let Some((clock, rate, finished)) = self.audio.as_ref().map(|a| (a.clock(), a.rate, a.finished())) else {
            return false;
        };
        if finished {
            if looping {
                // 工作区放完自动循环（和 AE 一样），声音与画面一起从头开始。
                self.playback.start_wall = now;
                self.playback.start_frame = wa;
                self.session.set_time(fr.tick_of(wa));
                self.start_audio(fr.tick_of(wa));
                if video {
                    self.request_frame(cid, wa, scale);
                }
                ctx.request_repaint();
                return true;
            }
            if video {
                self.session.set_time(fr.tick_of(wb));
            } else {
                self.playback.audio_frame = Some(wb);
            }
            self.stop();
            return true;
        }
'''

TARGET_OLD = '''        let snap = |f: i64| wa + (f - wa).div_euclid(step) * step;
        let target = snap(audio::frame_of_sample(a.clock(), a.rate, fr).clamp(wa, wb));
'''
TARGET_NEW = '''        let snap = |f: i64| wa + (f - wa).div_euclid(step) * step;
        // EFFECTCRAFT_OURS_CLOCK_STALL_V2
        // (1) 音频设备刚启动时 clock() 还是 0，画面不能等它 —— 先用墙上时钟。
        // (2) 播放中途音频时钟停走（本机见过）：超过 0.5 秒不动就改由墙上时钟驱动。
        // (3) 循环时按工作区取模，不会停在最后一帧。
        let n = ((wb - wa) / step).max(0) + 1;
        let wrap = |f: i64| if looping { wa + (f - wa).rem_euclid(n) * step } else { f.clamp(wa, wb) };
        let elapsed = (now - self.playback.start_wall).max(0.0);
        let fps = self.playback.fps.max(1.0);
        let wall = wrap(self.playback.start_frame + (((elapsed * fps) / step as f64).floor() as i64) * step);
        let clock_key = egui::Id::new("playback-audio-clock-stall");
        let start_key = egui::Id::new("playback-audio-clock-start");
        let now_tick = clock;
        let base = match ctx.data(|d| d.get_temp::<(f64, i64)>(start_key)) {
            Some((w, c)) if (w - self.playback.start_wall).abs() < 1e-6 => (w, c),
            _ => {
                ctx.data_mut(|d| d.insert_temp(start_key, (self.playback.start_wall, now_tick)));
                (self.playback.start_wall, now_tick)
            }
        };
        // 本次播放开始后音频时钟一次都没动过：声音还没起来，画面先按墙上时钟走。
        let audio_waiting = now_tick <= base.1;
        let last = ctx.data(|d| d.get_temp::<(i64, f64)>(clock_key));
        let stalled = !audio_waiting && matches!(last, Some((sample, at)) if sample == now_tick && now - at > 0.5);
        if last.is_none_or(|(sample, _)| sample != now_tick) {
            ctx.data_mut(|d| d.insert_temp(clock_key, (now_tick, now)));
        }
        if stalled {
            let once = egui::Id::new("playback-audio-clock-stall-logged");
            if !ctx.data(|d| d.get_temp::<bool>(once).unwrap_or(false)) {
                ctx.data_mut(|d| d.insert_temp(once, true));
                log::warn!(target: "effectcraft_ui", "audio clock stalled at sample {now_tick}; the picture follows the wall clock");
            }
        }
        let target = if audio_waiting || stalled {
            if video {
                // 目标帧可能不在预取窗口里（音频时钟停着的时候），直接要一次。
                self.request_frame(cid, wall, scale);
            }
            wall
        } else {
            wrap(snap(audio::frame_of_sample(clock, rate, fr).clamp(wa, wb)))
        };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/prefetch.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("clock stall guard already installed")
        return
    for old, new in ((HEAD_OLD, HEAD_NEW), (TARGET_OLD, TARGET_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:48]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("playback starts at once, survives a stalled clock, and loops")


if __name__ == "__main__":
    main()
