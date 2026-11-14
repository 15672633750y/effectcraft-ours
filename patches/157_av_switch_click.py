#!/usr/bin/env python3
"""Rolled back: the custom click/long-press handler crashed the app. The A/V switches keep
upstream's handler; only their size grows, in `zzzzzzzzzz_small_switches.py` (which runs last)."""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_AV_CLICK_ROLLED_BACK"


def main() -> None:
    print("A/V switch handler left as upstream")


if __name__ == "__main__":
    main()
