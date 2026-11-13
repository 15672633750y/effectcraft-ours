#!/usr/bin/env python3
"""H.264 export quality: constant-quality (CRF) encoding at the Best setting.

Every H.264 render used to aim at the Output Module's 10 Mbit/s no matter how many pixels had to
be described, so 1440p and 4K exports came out visibly softer than the source — a 4K frame at
10 Mbit/s is about 0.04 bits per pixel per frame, while AfterCodecs' default Q70 spends several
times that. CRF lets the bitrate follow the picture instead: detail survives where it matters and
quiet shots stay small. Draft keeps the bitrate target, which is cheaper and fine for a rough cut.

The encoder (filmcraft-h264enc) already writes High profile, limited (TV) range, BT.709 and 2 s
key frames, so the rest of the AfterCodecs baseline is in place; this is the missing piece.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_H264_CRF_V1"

OLD_IMPORT = "use effectcraft_project::render_queue::{AudioFormat, Channels, OutputFormat, ProResProfile};\n"
NEW_IMPORT = "use effectcraft_project::render_queue::{AudioFormat, Channels, OutputFormat, ProResProfile, RenderQuality};\n"

OLD_SIG = "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, codes: Codes) -> Result<H264> {\n"
NEW_SIG = "    fn new(w: u32, h: u32, rate: FrameRate, kbps: u32, quality: RenderQuality, codes: Codes) -> Result<H264> {\n"

OLD_RATE = """        let kbps = kbps.max(100);
        cfg.rate = filmcraft_h264enc::RateControl::Vbr { target_kbps: kbps, max_kbps: kbps * 3 / 2 };
"""
NEW_RATE = """        // EFFECTCRAFT_OURS_H264_CRF_V1
        // Constant quality: a fixed bitrate starves 1440p and 4K (same bits spread over four
        // times the pixels), so the Best setting lets the encoder spend what the picture needs.
        match quality {
            RenderQuality::Best => cfg.rate = filmcraft_h264enc::RateControl::Crf(20.0),
            RenderQuality::Draft => {
                let kbps = kbps.max(100);
                cfg.rate = filmcraft_h264enc::RateControl::Vbr { target_kbps: kbps, max_kbps: kbps * 3 / 2 };
            }
        }
"""

OLD_CALL = "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, codes)?),\n"
NEW_CALL = "        OutputFormat::H264 => Box::new(H264::new(w, h, rate, job.output.bitrate_kbps, job.settings.quality, codes)?),\n"


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
    print("H.264 Best quality now encodes at CRF 20 (Draft keeps the bitrate target)")


if __name__ == "__main__":
    main()

