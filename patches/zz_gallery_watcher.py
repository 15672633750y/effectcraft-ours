#!/usr/bin/env python3
"""No-op: the gallery watcher is gone.

It scanned the whole app files folder for new videos and pushed them into `DCIM/EffectCraft`. That
folder also holds the working copies of everything imported, so importing two clips added two
copies of them to the gallery. Exports publish themselves when the document is committed
(`97_gallery_publish.py`), which is the only path that produces a render, so nothing is lost.
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_GALLERY_WATCHER_REMOVED_V1"


def main() -> None:
    print("gallery watcher removed; exports publish on commit")


if __name__ == "__main__":
    main()
