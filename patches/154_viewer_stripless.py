#!/usr/bin/env python3
"""Rolled back: marking the viewer a protected canvas did not remove its strip (it shares its group
with the Layer tab) and it is a docking-rule change; the strip stays for now."""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_VIEWER_STRIPLESS_ROLLED_BACK"


def main() -> None:
    print("viewer canvas permission rolled back")


if __name__ == "__main__":
    main()
