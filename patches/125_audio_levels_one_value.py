#!/usr/bin/env python3
"""Audio Levels look like After Effects: one `+4.00 dB` while the channels are linked.

The value was always drawn as two numbers. AE draws one number until you unlink the pair, so the
panel showed "0.0 dB, 0.0 dB" and it was not obvious that dragging it moves both channels.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_LEVELS_ONE_V1"

OLD = '''    for d in 0..n.min(c.len()) {
        let suffix = if pct && d + 1 == n { "%" } else if levels { " dB" } else { "" };
'''
NEW = '''    // EFFECTCRAFT_OURS_AUDIO_LEVELS_ONE_V1
    // Linked Audio Levels draw one number (both channels move together), like After Effects.
    let fields = if levels && linked { 1 } else { n.min(c.len()) };
    for d in 0..fields {
        let suffix = if pct && d + 1 == n { "%" } else if levels { " dB" } else { "" };
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("single Audio Levels value already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    src = src.replace(OLD, NEW, 1)
    path.write_text(src, encoding="utf-8")
    print("linked Audio Levels draw one dB value")


if __name__ == "__main__":
    main()
