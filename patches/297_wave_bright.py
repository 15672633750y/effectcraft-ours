#!/usr/bin/env python3
"""音频波形再亮一点（主题色往白里提 45%）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_WAVE_BRIGHT_V1"

OLD = 'super::waveform::draw(&gp, wr.shrink2(vec2(0.0, 2.0)), &tm, layer, &s, t.accent)'

NEW = 'super::waveform::draw(&gp, wr.shrink2(vec2(0.0, 2.0)), &tm, layer, &s, t.accent.lerp_to_gamma(egui::Color32::WHITE, 0.45))'

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("waveform already brighter")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("waveform is brighter")


if __name__ == "__main__":
    main()
