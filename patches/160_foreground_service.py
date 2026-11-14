#!/usr/bin/env python3
"""Rolled back: the keep-alive foreground service is the newest lifecycle code, and the app now
crashes when it goes to the background and comes back ("switching to another app and back"). A
service that starts in onStop is exactly what runs on that path, so it comes out until the crash is
understood. The app may again be killed after a while in the background, but it should stop crashing
on the way there.
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_KEEPALIVE_ROLLED_BACK"


def main() -> None:
    print("foreground keep-alive service removed")


if __name__ == "__main__":
    main()
