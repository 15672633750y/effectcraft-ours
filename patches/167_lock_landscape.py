#!/usr/bin/env python3
"""The activity stays landscape, so rotating the phone never re-creates the drawing surface.

`config_changes` already lists every rotation-related change, yet turning the phone still crashed
the app: the native window and its graphics surface are resized mid-frame and that path is what
fails, not the activity being re-created. A video editor is a landscape app anyway — locking the
orientation to landscape removes the transition entirely. (Rotating the phone 90° keeps the same
landscape layout; the app simply no longer tries to run in portrait.)
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_LOCK_LANDSCAPE_V1"
OLD = 'orientation = "sensor"'
NEW = 'orientation = "sensorLandscape"'


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/build-common.sh"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("orientation already locked")
        return
    n = src.count(OLD)
    if n != 2:
        raise SystemExit(f"orientation anchor: expected 2, found {n}")
    src = src.replace(OLD, NEW + "  # " + MARKER)
    path.write_text(src, encoding="utf-8")
    print("activity locked to landscape")


if __name__ == "__main__":
    main()
