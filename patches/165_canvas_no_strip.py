#!/usr/bin/env python3
"""Rolled back: making the viewer a lone canvas hid the row that was wanted and left the one that is
not (the comp pill). The strip/bar split in the docking library needs to be understood before the
next attempt, so this changes nothing for now."""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_CANVAS_ROLLED_BACK"


def main() -> None:
    print("viewer canvas change rolled back")


if __name__ == "__main__":
    main()
