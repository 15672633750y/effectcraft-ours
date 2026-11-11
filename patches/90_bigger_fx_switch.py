#!/usr/bin/env python3
"""Make the timeline's layer switches (fx, shy, 3D …) easier to hit with a thumb."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BIGGER_SWITCHES_V1"


def replace_once(src: str, old: str, new: str, label: str) -> str:
    if new in src:
        return src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, found {n}")
    return src.replace(old, new, 1)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("switch sizing already applied")
        return
    src = replace_once(src, "const SW: f32 = 19.0;", "const SW: f32 = 24.0;", "switch column width")
    src = replace_once(
        src,
        "let br = Rect::from_center_size(pos2(cw.switches + SW * i as f32 + SW / 2.0, cy), vec2(16.0, 16.0));",
        "let br = Rect::from_center_size(pos2(cw.switches + SW * i as f32 + SW / 2.0, cy), vec2(21.0, 21.0));",
        "switch rect",
    )
    path.write_text(f"// {MARKER}\n{src}", encoding="utf-8")
    print("timeline switches are 21px in a 24px column now")


if __name__ == "__main__":
    main()
