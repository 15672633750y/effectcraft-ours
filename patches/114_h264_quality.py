#!/usr/bin/env python3
"""H.264 export quality: an AfterCodecs-style constant-quality control.

Every H.264 render used to aim at the Output Module's 10 Mbit/s no matter how many pixels had to
be described, so 1440p and 4K exports came out visibly softer than the source — 10 Mbit/s at 4K is
about 0.04 bits per pixel per frame, while AfterCodecs' default Q70 spends several times that.

The Output Module already has the AfterCodecs shape for HEVC/AV1 (`codec.rate_control` =
Bitrate|Quality and `codec.quality` 1–100); H.264 just never read it. Now:

* `rateControl: quality` → CRF 8 + (100 − quality) × 0.4, so the familiar 70 lands on CRF 20 —
  AfterCodecs' default slider position, and visually lossless on real footage.
* otherwise the Best render quality defaults to that same CRF 20 (no more flat bitrate), and a
  Draft render keeps the cheap bitrate target, which is what a rough cut wants.

The encoder already writes High profile, limited (TV) range, BT.709 and 2 s key frames.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_H264_CRF_V1"

OLD_IMPORT = "use effectcraft_project::render_queue::{AudioFormat, Channels, OutputFormat, ProResProfile};\n"
NEW_IMPORT = (
    "use effectcraft_project::render_queue::{AudioFormat, Channels, OutputFormat, ProResProfile, RateControlMode, RenderQuality, VideoCodecOptions};\n"
)

OLD_SIG = "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, codes: Codes) -> Result<H264> {\n"
NEW_SIG = (
    "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, quality: RenderQuality, codec: VideoCodecOptions, codes: Codes) -> Result<H264> {\n"
)

OLD_RATE = """        let kbps = kbps.max(100);
        cfg.rate = filmcraft_h264enc::RateControl::Vbr { target_kbps: kbps, max_kbps: kbps * 3 / 2 };
"""
NEW_RATE = """        // EFFECTCRAFT_OURS_H264_CRF_V1
        // Constant quality instead of a fixed bitrate: the same 10 Mbit/s over four times the
        // pixels (4K) is a quarter of the detail. `rateControl: quality` and the 1–100 slider
        // pick the CRF the way AfterCodecs does; Best without a slider still gets CRF 20.
        let crf = match codec.rate_control {
            RateControlMode::Quality => 8.0 + (100 - codec.quality.clamp(1, 100)) as f32 * 0.4,
            RateControlMode::Bitrate => 20.0,
        };
        cfg.rate = if matches!(quality, RenderQuality::Draft) {
            let kbps = kbps.max(100);
            filmcraft_h264enc::RateControl::Vbr { target_kbps: kbps, max_kbps: kbps * 3 / 2 }
        } else {
            filmcraft_h264enc::RateControl::Crf(crf)
        };
"""

OLD_CALL = "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, codes)?),\n"
NEW_CALL = (
    "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, job.settings.quality, job.output.codec, codes)?),\n"
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/export/src/encode.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("H.264 CRF already installed")
        return
    for old, new in ((OLD_IMPORT, NEW_IMPORT), (OLD_SIG, NEW_SIG), (OLD_RATE, NEW_RATE), (OLD_CALL, NEW_CALL)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:60]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("H.264 quality: constant quality (CRF) with the AfterCodecs-style 1-100 slider")


if __name__ == "__main__":
    main()
