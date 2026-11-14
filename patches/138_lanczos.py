#!/usr/bin/env python3
"""Rolled back: exports stopped producing a file after the High-quality resize switched to Lanczos.

The function stays out of the tree entirely — the export uses the bicubic resample again, which is
what produced the files that worked. (Lanczos can come back once a render on the device is checked
with the small test clip.)
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_LANCZOS_ROLLED_BACK"


def main() -> None:
    print("export resize back to bicubic")


if __name__ == "__main__":
    main()
