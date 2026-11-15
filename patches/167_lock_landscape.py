#!/usr/bin/env python3
"""Lock the activity to landscape — the last way to keep the app openable.

Both rotation paths kill this app on this phone: with `configChanges` the drawing surface is
resized in place and the graphics stack dies; without it, Android re-creates the activity on every
launch (the phone starts in portrait, the app wants landscape) and the app dies just as often. With
the orientation locked there is no rotation to handle, so the app simply opens.

A video editor is a landscape app; portrait would need the surface path fixed first.
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
