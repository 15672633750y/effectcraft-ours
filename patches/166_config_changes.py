#!/usr/bin/env python3
"""Rolled back: adding configChanges was the wrong direction — see 167 (rotation now re-creates the
activity, which is the path Android handles)."""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_CONFIG_CHANGES_ROLLED_BACK"


def main() -> None:
    print("configChanges patch retired")


if __name__ == "__main__":
    main()
