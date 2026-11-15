#!/usr/bin/env python3
"""Temporarily removed: isolating start-up crashes.

The log copy, the clean-up and the gallery watcher all run in the first seconds of a launch. They
are the only code that differs from the build that opened reliably, so they come out wholesale until
the crash is located; if the app is stable without them, they go back one at a time.
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_LOG_EXPORT_DISABLED"


def main() -> None:
    print("log export / clean-up disabled for the isolation build")


if __name__ == "__main__":
    main()
