#!/usr/bin/env python3
"""H.264 encoding speed, the AfterCodecs speed preset.

AfterCodecs pairs its quality slider with a speed preset (slower = better quality at the same
quality setting). EffectCraft's encoder already has `Preset::{Speed, Balanced, Quality}` but nothing
ever set it, so every render used the middle one. The Output Module now carries `encode_speed`
(0 = balanced, the default; 1 = slower/quality; 2 = faster), the render command accepts
`encodeSpeed`, and the export dialog offers it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ENCODE_SPEED_V1"

FIELD = '''    /// H.264 encoder speed preset: 0 = balanced, 1 = slower (quality), 2 = faster.
    pub encode_speed: u8,
'''

FIELD_ANCHOR = "    /// H.264 target bitrate (and WebM's when `webm_bitrate`; HEVC / AV1 with [`RateControlMode::Bitrate`]).\n"

DEFAULT_ANCHOR = "            bitrate_kbps: 10_000,\n"
DEFAULT = "            encode_speed: 0,\n"

ENGINE_ANCHOR = '''    if let Some(b) = f_p(p, "bitrate") {
        om.bitrate_kbps = b.clamp(50.0, 500_000.0) as u32;
    }
'''
ENGINE = '''    if let Some(v) = f_p(p, "encodeSpeed") {
        om.encode_speed = (v.clamp(0.0, 2.0)) as u8;
    }
'''

ENC_OLD = "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, quality: RenderQuality, codec: VideoCodecOptions, codes: Codes) -> Result<H264> {\n"
ENC_NEW = "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, quality: RenderQuality, codec: VideoCodecOptions, speed: u8, codes: Codes) -> Result<H264> {\n"

ENC_CALL_OLD = "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, job.settings.quality, job.output.codec, codes)?),\n"
ENC_CALL_NEW = "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, job.settings.quality, job.output.codec, job.output.encode_speed, codes)?),\n"

PRESET_ANCHOR = "        cfg.keyint = (rate.as_f64() * 2.0).round().max(1.0) as u32;\n"
PRESET = '''        // AfterCodecs' speed presets: the encoder trades search effort for time.
        cfg.preset = match speed {
            1 => filmcraft_h264enc::Preset::Quality,
            2 => filmcraft_h264enc::Preset::Speed,
            _ => filmcraft_h264enc::Preset::Balanced,
        };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    project = root / "crates/project/src/render_queue.rs"
    src = project.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FIELD_ANCHOR) != 1:
            raise SystemExit(f"field anchor: {src.count(FIELD_ANCHOR)}")
        src = src.replace(FIELD_ANCHOR, "    // " + MARKER + "\n" + FIELD + FIELD_ANCHOR, 1)
        if src.count(DEFAULT_ANCHOR) != 1:
            raise SystemExit(f"default anchor: {src.count(DEFAULT_ANCHOR)}")
        src = src.replace(DEFAULT_ANCHOR, DEFAULT_ANCHOR + DEFAULT, 1)
        project.write_text(src, encoding="utf-8")
        print("OutputModule carries encode_speed")

    engine = root / "crates/engine/src/cmd/render_queue.rs"
    src = engine.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(ENGINE_ANCHOR) != 1:
            raise SystemExit(f"engine anchor: {src.count(ENGINE_ANCHOR)}")
        src = src.replace(ENGINE_ANCHOR, ENGINE_ANCHOR + ENGINE, 1)
        engine.write_text(src, encoding="utf-8")
        print("renderQueue.add accepts encodeSpeed")

    enc = root / "crates/export/src/encode.rs"
    src = enc.read_text(encoding="utf-8")
    if PRESET not in src:
        for old, new in ((ENC_OLD, ENC_NEW), (ENC_CALL_OLD, ENC_CALL_NEW), (PRESET_ANCHOR, PRESET_ANCHOR + PRESET)):
            if src.count(old) != 1:
                raise SystemExit(f"encode anchor {old[:40]!r}: {src.count(old)}")
            src = src.replace(old, new, 1)
        enc.write_text(src, encoding="utf-8")
        print("H.264 encoder uses the speed preset")


if __name__ == "__main__":
    main()
