#!/usr/bin/env python3
"""Playback: start at once, survive a stalled audio clock, loop at the end (v0.24.1 anchors).

Same behaviour as the 0.22 version of this patch, re-pointed at 0.24.1, where the frame under the
audio clock is `fr.frame_at(a.clock_time())` instead of `audio::frame_of_sample(a.clock(), …)`.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOCK_STALL_V3"

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
        let Some((clock, finished)) = self.audio.as_ref().map(|a| (a.clock_time(), a.finished())) else {
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
        let target = snap(fr.frame_at(a.clock_time()).clamp(wa, wb));
'''
TARGET_NEW = '''        let snap = |f: i64| wa + (f - wa).div_euclid(step) * step;
        // EFFECTCRAFT_OURS_CLOCK_STALL_V3
        // (1) 音频设备刚启动时 clock 还是 0，画面不能等它 —— 先用墙上时钟。
        // (2) 播放中途音频时钟停走（本机见过）：超过 0.5 秒不动就改由墙上时钟驱动。
        // (3) 循环时按工作区取模，不会停在最后一帧。
        let n = ((wb - wa) / step).max(0) + 1;
        let wrap = |f: i64| if looping { wa + (f - wa).rem_euclid(n) * step } else { f.clamp(wa, wb) };
        let elapsed = (now - self.playback.start_wall).max(0.0);
        let fps = self.playback.fps.max(1.0);
        let wall = wrap(self.playback.start_frame + (((elapsed * fps) / step as f64).floor() as i64) * step);
        let clock_key = egui::Id::new("playback-audio-clock-stall");
        let start_key = egui::Id::new("playback-audio-clock-start");
        let base = match ctx.data(|d| d.get_temp::<(f64, i64)>(start_key)) {
            Some((w, c)) if (w - self.playback.start_wall).abs() < 1e-6 => (w, c),
            _ => {
                let v = (self.playback.start_wall, clock.0);
                ctx.data_mut(|d| d.insert_temp(start_key, v));
                v
            }
        };
        let audio_waiting = clock.0 <= base.1;
        let last = ctx.data(|d| d.get_temp::<(i64, f64)>(clock_key));
        let stalled = !audio_waiting && matches!(last, Some((sample, at)) if sample == clock.0 && now - at > 0.5);
        if last.is_none_or(|(sample, _)| sample != clock.0) {
            ctx.data_mut(|d| d.insert_temp(clock_key, (clock.0, now)));
        }
        if stalled {
            let once = egui::Id::new("playback-audio-clock-stall-logged");
            if !ctx.data(|d| d.get_temp::<bool>(once).unwrap_or(false)) {
                ctx.data_mut(|d| d.insert_temp(once, true));
                log::warn!(target: "effectcraft_ui", "audio clock stalled; the picture follows the wall clock");
            }
        }
        let target = if audio_waiting || stalled {
            if video {
                self.request_frame(cid, wall, scale);
            }
            wall
        } else {
            wrap(snap(fr.frame_at(clock).clamp(wa, wb)))
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
